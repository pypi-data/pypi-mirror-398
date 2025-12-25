from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from retour_client.constantes import RetourClientConstantes
from retour_client.models import RetourClient
from retour_client.utils import AnymailModuleRetourUtils

"""
Batch JOURNALIER d'envoi de mail des récap des tickets en cours
au client et au chef de projet en RECETTE / PREPRODUCTION,
ou en PRODUCTION pendant la période de garantie.
"""


class EnvoiMailRetourClientBatch:
    @staticmethod
    def do_process():
        today = timezone.now().date()

        in_recette = settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.RECETTE
        in_preprod = settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.PREPRODUCTION

        in_prod_garantie = False
        if settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.PRODUCTION:
            try:
                fin_gar = datetime.strptime(settings.DATE_FIN_GARANTIE, "%Y-%m-%d").date()
                in_prod_garantie = fin_gar >= today
            except Exception:
                in_prod_garantie = False

        if not (in_recette or in_preprod or in_prod_garantie):
            return

        yesterday = today - timedelta(days=1)

        # si date_ajout est un DateTimeField, filtre par __date
        bugs_a_verifier = RetourClient.objects.filter(
            statut=RetourClientConstantes.TRAITE,
            date_ajout__date=yesterday
        )
        bugs_a_traiter = RetourClient.objects.exclude(
            Q(statut=RetourClientConstantes.EN_ATTENTE) | Q(statut=RetourClientConstantes.EN_TRAITEMENT)
        ).filter(date_ajout__date=yesterday)

        # --- Mail client (récap à vérifier) ---
        if bugs_a_verifier.exists():
            context = {"bugs": bugs_a_verifier}
            # Utilise le nom de template Django
            body_html = AnymailModuleRetourUtils.render_template(
                "retour_client/mails/recap-journalier-client.tpl", context
            )
            subject = "Retours corrigés par Revolucy hier à vérifier"
            AnymailModuleRetourUtils.send_mail(subject, [settings.EMAIL_CLIENT_RETOUR], body_html=body_html)

        # --- Mail Revolucy (à traiter) ---
        if bugs_a_traiter.exists():
            context = {"bugs": bugs_a_traiter}
            body_html = AnymailModuleRetourUtils.render_template(
                "retour_client/mails/recap-journalier-revo.tpl", context
            )
            subject = f"Retours clients ({settings.EMAIL_CLIENT_RETOUR}) à traiter"

            import requests
            collaborateur_associe = "maxence@revolucy.fr"
            try:
                url = f"https://app.lucy-crm.fr/api/credit-client/{settings.SIREN_CLIENT}"
                r = requests.get(url, timeout=(2, 5))
                if r.ok:
                    data = r.json()
                    collaborateur_associe = data.get("collaborateur_associe") or collaborateur_associe
            except Exception:
                pass

            AnymailModuleRetourUtils.send_mail(subject, [collaborateur_associe], body_html=body_html)
