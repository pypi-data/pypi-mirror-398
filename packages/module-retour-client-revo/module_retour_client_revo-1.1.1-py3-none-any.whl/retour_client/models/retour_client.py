from django.conf import settings
from django.db import models

from retour_client import adapters
from retour_client.constantes import RetourClientConstantes


class RetourClient(models.Model):
    date_ajout = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=1, choices=RetourClientConstantes.statut,
                              default=RetourClientConstantes.EN_ATTENTE)
    type = models.CharField(max_length=1, choices=RetourClientConstantes.type,
                            default=RetourClientConstantes.NON_CLASSE)
    lien_url = models.URLField(max_length=300)
    utilisateur = models.CharField(max_length=100, default=RetourClientConstantes.INCONNU)
    image = models.ImageField(upload_to=adapters.image_upload_to, null=True, blank=True)
    titre = models.CharField(max_length=100)
    description = models.TextField()
    priorite = models.CharField(max_length=1, choices=RetourClientConstantes.priorite,
                                default=RetourClientConstantes.NORMAL)
    navigateur = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Retour Client"
        verbose_name_plural = "Retours Client"

    def __str__(self):
        return f'n°{self.pk} - {self.titre}'

    @property
    def color_statut(self):
        if self.statut == RetourClientConstantes.EN_ATTENTE:
            return '#d46060'
        elif self.statut == RetourClientConstantes.EN_TRAITEMENT:
            return '#e8b019'
        elif self.statut == RetourClientConstantes.V2:
            return '#48cae4'
        elif self.statut == RetourClientConstantes.TRAITE:
            return '#c3eb34'
        elif self.statut == RetourClientConstantes.VALIDE:
            return '#34eba1'
        else:
            return '#cccccc'

    @property
    def color_priorite(self):
        if self.priorite == RetourClientConstantes.CRITIQUE:
            return '#e63363'
        elif self.statut == RetourClientConstantes.NON_URGENT:
            return '#a6e633'
        else:
            return '#33abe6'

    @property
    def icone_type(self):
        if self.type == RetourClientConstantes.NON_CLASSE:
            return '<i class="fa-solid fa-note-sticky"></i>'
        elif self.type == RetourClientConstantes.QUESTION:
            return '<i class="fa-regular fa-circle-question"></i>'
        elif self.type == RetourClientConstantes.BUG:
            return '<i class="fa-solid fa-bug"></i>'
        elif self.type == RetourClientConstantes.AMELIORATION:
            return '<i class="fa-regular fa-square-plus"></i>'

    @property
    def slug_url(self):
        url_site = f'{settings.URL_PROTOCOL}://{settings.URL_DOMAIN}'
        return self.lien_url.replace(url_site, '')

    def display_status_for(self, user):
        from retour_client.adapters import is_user_admin

        is_admin = bool(user) and not getattr(user, "is_anonymous", False) and is_user_admin(user)

        if self.statut == RetourClientConstantes.EN_ATTENTE and is_admin:
            return "Bug en traitement"
        if self.statut == RetourClientConstantes.EN_TRAITEMENT and is_admin:
            return "Bug traité"
        if self.statut == RetourClientConstantes.TRAITE:
            return "Je valide le correctif Revolucy"
        return ""

    @property
    def attente_reponse_revolucy(self):
        return not self.retour_client.all() or self.retour_client.last().repondant is RetourClientConstantes.CLIENT

    @property
    def attente_reponse_client(self):
        return self.retour_client.last().repondant is RetourClientConstantes.REVOLUCY

    @property
    def statut_bloque(self):
        return self.statut == RetourClientConstantes.VALIDE
