import logging

from django.core.management import BaseCommand

from retour_client.management.envoi_mail_retour_client_preprod import EnvoiMailRetourClientBatch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Envoyer les recap des tickets en cours au client et chef de projet"

    def handle(self, *args, **options):
        logger.info(f"Lancement de la commande '{self.help}'")
        EnvoiMailRetourClientBatch.do_process()
