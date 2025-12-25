from django.contrib import admin

from retour_client.models import RetourClient, ReponseBug


class BlockReponseBug(admin.StackedInline):
    model = ReponseBug
    extra = 1


@admin.register(RetourClient)
class RetourClientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'priorite', 'statut', 'description')
    inlines = [BlockReponseBug]
