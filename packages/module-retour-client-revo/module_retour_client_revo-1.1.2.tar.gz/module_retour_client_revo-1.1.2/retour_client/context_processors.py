import logging
from datetime import datetime

from django.conf import settings

from .constantes import RetourClientConstantes
from .forms import RetourClientForm
from .http_utils import safe_get_json

logger = logging.getLogger(__name__)


def formulaire_retour_client(request):
    form_bug = RetourClientForm()
    jrs_restant_garantie = 0
    solde_ticket = 0
    current_user = request.user

    siren = settings.SIREN_CLIENT

    if (settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.PRODUCTION
            and not current_user.is_anonymous
            and getattr(current_user, "is_administrateur", False)):

        date_fin_garantie = getattr(settings, 'DATE_FIN_GARANTIE', None)
        if date_fin_garantie:
            jrs_restant_garantie = (
                    datetime.strptime(date_fin_garantie, '%Y-%m-%d').date()
                    - datetime.today().date()
            ).days
        else:
            jrs_restant_garantie = 0

        url = f"https://app.lucy-crm.fr/api/credit-client/{siren}"

        data, err = safe_get_json(url, timeout=(2, 5))  # ≤ ~5 s
        if data:
            solde_ticket = data.get("solde_ticket", 0)
        else:
            # On loggue mais on NE BLOQUE PAS : on garde solde_ticket=0
            logger.error(f"[Lucy API] Impossible de récupérer solde_ticket: {err}")

    return {
        'form_bug': form_bug,
        'environnement': settings.ENVIRONNEMENT,
        'siren_client': siren,
        'jrs_restant_garantie': jrs_restant_garantie,
        'solde_ticket': solde_ticket,
    }
