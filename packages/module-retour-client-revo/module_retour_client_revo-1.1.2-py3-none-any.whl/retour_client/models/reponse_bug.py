from django.db import models

from retour_client.constantes import RetourClientConstantes


class ReponseBug(models.Model):
    date_ajout = models.DateTimeField(auto_now_add=True)
    reponse = models.TextField()
    repondant = models.CharField(max_length=1, choices=RetourClientConstantes.repondant)
    retour_client = models.ForeignKey('retour_client.RetourClient', on_delete=models.CASCADE, related_name='retour_client')
    temps_passe = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5)
    piece_jointe = models.FileField(upload_to='retourclient_pj', blank=True, null=True)

    class Meta:
        verbose_name = "Retour Client"
        verbose_name_plural = "Retours Client"

    def __str__(self):
        return f'{self.reponse} - n°{self.pk}'

    @property
    def reponse_revolucy(self):
        return self.repondant is RetourClientConstantes.REVOLUCY
