import json
import logging
from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

import anthropic

from retour_client.models import RetourClient, ConversationClaude
from retour_client.constantes import RetourClientConstantes

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service pour interagir avec l'API Claude d'Anthropic"""

    def __init__(self):
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY non configurée dans les settings")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = getattr(settings, 'CLAUDE_MODEL', 'claude-3-5-haiku-20241022')

    def _get_tickets_context(self):
        """Génère le contexte des tickets pour Claude"""
        # Utiliser order_by('-pk') pour éviter d'accéder à date_ajout (problème MySQL timezone)
        tickets = RetourClient.objects.all().order_by('-pk')[:100]

        tickets_data = []
        for ticket in tickets:
            # Gérer le cas où date_ajout pose problème avec MySQL timezone
            try:
                date_str = ticket.date_ajout.strftime("%d/%m/%Y %H:%M") if ticket.date_ajout else "Non définie"
            except Exception:
                date_str = "Non définie"

            ticket_info = {
                "id": ticket.pk,
                "titre": ticket.titre,
                "description": ticket.description[:500] if ticket.description else "",
                "statut": dict(RetourClientConstantes.statut).get(ticket.statut, ticket.statut),
                "type": dict(RetourClientConstantes.type).get(ticket.type, ticket.type),
                "priorite": dict(RetourClientConstantes.priorite).get(ticket.priorite, ticket.priorite),
                "utilisateur": ticket.utilisateur,
                "date_ajout": date_str,
                "url": ticket.lien_url,
            }
            tickets_data.append(ticket_info)

        return tickets_data

    def _get_statistics_context(self):
        """Génère les statistiques des tickets"""
        stats = {
            "total": RetourClient.objects.count(),
            "par_statut": {},
            "par_type": {},
            "par_priorite": {},
            "par_mois": [],
        }

        # Stats par statut
        for code, label in RetourClientConstantes.statut:
            count = RetourClient.objects.filter(statut=code).count()
            stats["par_statut"][label] = count

        # Stats par type
        for code, label in RetourClientConstantes.type:
            count = RetourClient.objects.filter(type=code).count()
            stats["par_type"][label] = count

        # Stats par priorité
        for code, label in RetourClientConstantes.priorite:
            count = RetourClient.objects.filter(priorite=code).count()
            stats["par_priorite"][label] = count

        # Stats par mois (6 derniers mois) - désactivé si problème MySQL timezone
        try:
            monthly_stats = (
                RetourClient.objects
                .annotate(mois=TruncMonth('date_ajout'))
                .values('mois')
                .annotate(count=Count('id'))
                .order_by('-mois')[:6]
            )
            stats["par_mois"] = [
                {"mois": s["mois"].strftime("%B %Y") if s["mois"] else "Inconnu", "count": s["count"]}
                for s in monthly_stats
            ]
        except Exception:
            stats["par_mois"] = []

        return stats

    def _build_system_prompt(self):
        """Construit le prompt système avec le contexte des tickets"""
        tickets_data = self._get_tickets_context()
        stats = self._get_statistics_context()

        system_prompt = f"""Tu es un assistant IA spécialisé dans l'analyse et la gestion des tickets de retour client pour l'entreprise Revolucy.

Tu as accès aux données suivantes :

## STATISTIQUES GLOBALES
{json.dumps(stats, ensure_ascii=False, indent=2)}

## LISTE DES TICKETS (100 derniers)
{json.dumps(tickets_data, ensure_ascii=False, indent=2)}

## TES CAPACITÉS
Tu peux :
1. **Rechercher des tickets** : Trouver des tickets par mot-clé, statut, type, priorité, utilisateur, URL
2. **Analyser les statistiques** : Donner des insights sur les tendances, les pages les plus problématiques, etc.
3. **Répondre aux questions** : Expliquer le fonctionnement, donner des conseils
4. **Identifier des patterns** : Repérer des bugs récurrents ou des problèmes similaires

## RÈGLES
- Réponds toujours en français
- Sois concis mais précis
- Quand tu mentionnes un ticket, indique son numéro (ID) pour que l'utilisateur puisse le retrouver
- Si tu ne trouves pas de ticket correspondant, dis-le clairement
- Pour les statistiques, donne des chiffres précis
- Formate tes réponses de manière lisible (utilise des listes, des titres, etc.)
"""
        return system_prompt

    def send_message(self, session_id: str, utilisateur: str, user_message: str) -> str:
        """
        Envoie un message à Claude et retourne la réponse.
        Conserve l'historique de la conversation.
        """
        # Sauvegarder le message utilisateur
        ConversationClaude.add_message(
            session_id=session_id,
            utilisateur=utilisateur,
            role=RetourClientConstantes.ROLE_USER,
            message=user_message
        )

        # Récupérer l'historique de la conversation
        history = ConversationClaude.get_conversation_history(session_id)

        try:
            # Appeler l'API Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self._build_system_prompt(),
                messages=history
            )

            assistant_message = response.content[0].text

            # Sauvegarder la réponse de l'assistant
            ConversationClaude.add_message(
                session_id=session_id,
                utilisateur=utilisateur,
                role=RetourClientConstantes.ROLE_ASSISTANT,
                message=assistant_message
            )

            return assistant_message

        except anthropic.APIError as e:
            logger.error(f"Erreur API Claude: {e}")
            raise Exception(f"Erreur lors de la communication avec Claude: {str(e)}")

    def generate_description_help(self, titre: str, url_page: str = "") -> str:
        """
        Génère une aide à la rédaction de description de bug basée sur le titre.
        """
        prompt = f"""Un utilisateur souhaite signaler un problème avec le titre suivant :
"{titre}"

{f"L'utilisateur se trouve sur la page : {url_page}" if url_page else ""}

Génère une description COURTE et structurée avec uniquement ces 2 sections :

### 1. Comportement attendu
[Décrire ce qui devrait normalement se passer...]

### 2. Comportement constaté
[Décrire précisément ce qui ne fonctionne pas...]

Utilise des placeholders entre crochets [comme ceci] pour les informations que l'utilisateur doit compléter.
Sois concis : 2-3 lignes maximum par section.
Réponds uniquement avec la description formatée, sans introduction ni conclusion."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Erreur API Claude (génération description): {e}")
            raise Exception(f"Erreur lors de la génération: {str(e)}")

    def search_similar_tickets(self, query: str, limit: int = 5) -> list:
        """
        Recherche des tickets similaires à une requête donnée.
        """
        prompt = f"""Voici une requête de recherche : "{query}"

Analyse les tickets disponibles et identifie les {limit} tickets les plus pertinents.

Pour chaque ticket trouvé, retourne un objet JSON avec :
- id: l'identifiant du ticket
- titre: le titre
- pertinence: un score de 1 à 10
- raison: pourquoi ce ticket est pertinent (en une phrase)

Retourne UNIQUEMENT un tableau JSON, sans autre texte."""

        tickets_data = self._get_tickets_context()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=f"Tu es un assistant de recherche. Voici les tickets disponibles :\n{json.dumps(tickets_data, ensure_ascii=False)}",
                messages=[{"role": "user", "content": prompt}]
            )

            # Parser la réponse JSON
            result_text = response.content[0].text
            # Nettoyer le texte pour extraire le JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            return json.loads(result_text.strip())

        except (anthropic.APIError, json.JSONDecodeError) as e:
            logger.error(f"Erreur recherche tickets: {e}")
            return []
