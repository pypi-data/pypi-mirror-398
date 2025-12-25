import json
import uuid
import logging

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from retour_client.constantes import RetourClientConstantes
from retour_client.models import ConversationClaude
from retour_client.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)


class ChatbotMessageView(LoginRequiredMixin, View):
    """Vue pour envoyer un message au chatbot Claude"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            session_id = data.get('session_id', '')

            if not message:
                return JsonResponse({
                    'success': False,
                    'error': 'Le message ne peut pas être vide'
                }, status=400)

            # Générer un session_id si non fourni
            if not session_id:
                session_id = f"{request.user.email}_{uuid.uuid4().hex[:8]}"

            # Obtenir l'email de l'utilisateur
            utilisateur = getattr(request.user, 'email', 'Inconnu')
            if not utilisateur:
                utilisateur = str(request.user)

            # Envoyer le message à Claude
            service = ClaudeService()
            response_message = service.send_message(
                session_id=session_id,
                utilisateur=utilisateur,
                user_message=message
            )

            return JsonResponse({
                'success': True,
                'message': response_message,
                'session_id': session_id
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Format JSON invalide'
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur chatbot: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ChatbotHistoryView(LoginRequiredMixin, View):
    """Vue pour récupérer l'historique des conversations"""

    def get(self, request):
        try:
            session_id = request.GET.get('session_id', '')
            utilisateur = getattr(request.user, 'email', str(request.user))

            if session_id:
                # Récupérer l'historique d'une session spécifique (sans charger date_creation)
                messages = ConversationClaude.objects.filter(
                    session_id=session_id
                ).order_by('id').only('role', 'message')
            else:
                # Récupérer les sessions de l'utilisateur (sans accéder aux dates)
                sessions = ConversationClaude.objects.filter(
                    utilisateur=utilisateur
                ).values('session_id').distinct()[:10]

                return JsonResponse({
                    'success': True,
                    'sessions': [
                        {
                            'session_id': s['session_id'],
                            'first_message': ConversationClaude.objects.filter(
                                session_id=s['session_id'],
                                role=RetourClientConstantes.ROLE_USER
                            ).only('message').first().message[:50] + '...' if ConversationClaude.objects.filter(
                                session_id=s['session_id'],
                                role=RetourClientConstantes.ROLE_USER
                            ).exists() else 'Nouvelle conversation'
                        }
                        for s in sessions
                    ]
                })

            messages_data = [
                {
                    'role': msg.role,
                    'message': msg.message
                }
                for msg in messages
            ]

            return JsonResponse({
                'success': True,
                'messages': messages_data,
                'session_id': session_id
            })

        except Exception as e:
            logger.error(f"Erreur récupération historique: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ChatbotNewSessionView(LoginRequiredMixin, View):
    """Vue pour créer une nouvelle session de conversation"""

    def post(self, request):
        try:
            utilisateur = getattr(request.user, 'email', str(request.user))
            session_id = f"{utilisateur}_{uuid.uuid4().hex[:8]}"

            return JsonResponse({
                'success': True,
                'session_id': session_id
            })

        except Exception as e:
            logger.error(f"Erreur création session: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class GenerateDescriptionView(LoginRequiredMixin, View):
    """Vue pour générer une aide à la description de bug"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            titre = data.get('titre', '').strip()
            url_page = data.get('url_page', '').strip()

            if not titre:
                return JsonResponse({
                    'success': False,
                    'error': 'Le titre est requis'
                }, status=400)

            service = ClaudeService()
            description = service.generate_description_help(
                titre=titre,
                url_page=url_page
            )

            return JsonResponse({
                'success': True,
                'description': description
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Format JSON invalide'
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur génération description: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class GenerateDescriptionPublicView(View):
    """Vue publique pour générer une aide à la description de bug (pour le formulaire public)"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            titre = data.get('titre', '').strip()
            url_page = data.get('url_page', '').strip()

            if not titre:
                return JsonResponse({
                    'success': False,
                    'error': 'Le titre est requis'
                }, status=400)

            service = ClaudeService()
            description = service.generate_description_help(
                titre=titre,
                url_page=url_page
            )

            return JsonResponse({
                'success': True,
                'description': description
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Format JSON invalide'
            }, status=400)
        except Exception as e:
            logger.error(f"Erreur génération description: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
