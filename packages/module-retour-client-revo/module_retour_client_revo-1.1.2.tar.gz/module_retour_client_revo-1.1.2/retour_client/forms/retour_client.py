from django import forms

from retour_client.models import RetourClient


class RetourClientForm(forms.ModelForm):
    class Meta:
        model = RetourClient
        exclude = ['date_ajout', 'statut', 'utilisateur', 'image', 'navigateur', 'lien_url', 'type']

    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6}), required=True)

    def clean_description(self):
        description = self.cleaned_data.get('description')
        # Convertit les sauts de ligne en <br> dans la description
        return description.replace('\n', '<br>')
