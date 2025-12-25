"""
Service de gestion des statuts Retours de bug.
"""

from django.contrib import messages
from django.db import transaction

from retour_client.constantes import RetourClientConstantes
from retour_client.models import RetourClient


class RetourBugService:

    @staticmethod
    @transaction.atomic
    def lien_changement_statut_bug(request, bug):
        try:
            if bug.statut == RetourClientConstantes.EN_ATTENTE:
                bug.statut = RetourClientConstantes.EN_TRAITEMENT
                bug.save()
            elif bug.statut == RetourClientConstantes.EN_TRAITEMENT:
                bug.statut = RetourClientConstantes.TRAITE
                bug.save()
            elif bug.statut == RetourClientConstantes.TRAITE:
                bug.statut = RetourClientConstantes.VALIDE
                bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")

    @staticmethod
    @transaction.atomic
    def lien_refus_validation_bug(request, bug):
        try:
            bug.statut = RetourClientConstantes.EN_ATTENTE
            bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")

    # ACTION BTN GESTION DE PROJET

    @staticmethod
    @transaction.atomic
    def lien_changement_statut_v2(request, bug):
        try:
            bug.statut = RetourClientConstantes.V2
            bug.type = RetourClientConstantes.AMELIORATION
            bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")

    @staticmethod
    @transaction.atomic
    def lien_changement_type_v1(request, bug):
        try:
            bug.statut = RetourClientConstantes.EN_TRAITEMENT
            bug.type = RetourClientConstantes.AMELIORATION
            bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")

    @staticmethod
    @transaction.atomic
    def lien_changement_type_question(request, bug):
        try:
            bug.statut = RetourClientConstantes.EN_TRAITEMENT
            bug.type = RetourClientConstantes.QUESTION
            bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")

    @staticmethod
    @transaction.atomic
    def lien_changement_type_bug(request, bug):
        try:
            bug.statut = RetourClientConstantes.EN_TRAITEMENT
            bug.type = RetourClientConstantes.BUG
            bug.save()

        except RetourClient.DoesNotExist:
            messages.error(request, "Retour Client introuvable.")
