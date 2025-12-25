# Module de retour Client

## Conception

- [Django](https://www.djangoproject.com/)
- [Bootstrap](https://getbootstrap.com/)
- [JQuery 3.5.1](https://api.jquery.com/category/version/3.5/)

## Installation

#### 1 - Ajouter le package dans les requirements
#### 2 - Ajouter dans votre .env :
=> Pour la préprod/Prod :<br>
```html
#====================================== RETOUR CLIENT =======================================
EMAIL_CLIENT_RETOUR='test@test.fr'
SIREN_CLIENT='1245648'
DATE_MISE_EN_PRODUCTION='2024-12-30'
DATE_FIN_GARANTIE='2024-12-30'

# API Claude pour le chatbot IA (optionnel)
ANTHROPIC_API_KEY='sk-ant-xxxxx'
```

#### 3 - Ajouter dans votre fichier settings.py :
```html
INSTALLED_APPS = [
    'retour_client',
]
```
```html
'context_processors': [
    'retour_client.context_processors.formulaire_retour_client',
]
```
```html
########### Configuration RETOUR CLIENT.
EMAIL_CLIENT_RETOUR = env('EMAIL_CLIENT_RETOUR')
SIREN_CLIENT = env('SIREN_CLIENT')
DATE_MISE_EN_PRODUCTION = env('DATE_MISE_EN_PRODUCTION')
DATE_FIN_GARANTIE = env('DATE_FIN_GARANTIE')

# Configuration API Claude (optionnel - pour le chatbot IA)
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default=None)
CLAUDE_MODEL = 'claude-sonnet-4-20250514'  # Modèle par défaut
```
#### 4 - Ajouter dans votre fichier urls.py :
```html
 path('retour-client/', include("retour_client.urls")),
```
#### 5 - Ajouter dans le footer.html de votre base :
```html
<!-- AJOUT POPUP RETOUR CLIENT -->
{% include 'retour_client.html' %}
```
#### 6 - Ajouter un cron journalier 09h00 sur le serveur pour envoi des mails en préprod:
```html
Commande : envoi_mail_retour_client_preprod
```

## Licence

[Revolucy](https://www.revolucy.fr)

## Versionning

- V1.0.0 | Création du module de retour
- V1.0.1 | Modification des versions des requirements
- V1.0.2 | Correction bug correspondance Python 3.9
- V1.0.3 | Correction bug buttons admin
- V1.0.4 | Correction bug date
- V1.0.5 | Correction bug
- V1.0.6 | Ajout d'un cockpit de gestion statistique
- V1.0.7 | Amélioration CSS
- V1.1.0 | Intégration de l'IA Claude pour aide à la rédaction et analyse des tickets via un chatbot
- V1.1.1 | Correction bug

## Fonctionnalités IA (V1.1.0+)

### Chatbot Assistant IA
Accessible depuis la page `/retour-client/pipeline-retours/` via un bouton fixe sur la droite.

**Fonctionnalités :**
- Recherche de tickets par mots-clés, statut, type, priorité
- Analyse statistique des tickets (tendances, pages problématiques, etc.)
- Identification de patterns et bugs récurrents
- Réponses contextuelles basées sur l'historique des tickets
- Historique des conversations par utilisateur

### Aide à la rédaction de description
Bouton "Aide IA" disponible dans le formulaire de création de bug.

**Fonctionnalités :**
- Génération automatique d'une structure de description basée sur le titre
- Format optimisé pour les développeurs (contexte, comportement attendu/constaté, étapes de reproduction, impact)
- Placeholders à compléter par l'utilisateur

## Flux

### PREPROD : 
=> Module de retour visible pour tous les utilisateurs

1 - Création d'un ticket par le client :
- Enregistrement du ticket sur le site
- 2 Mails (Client / Chef de projet revo) journalier avec liste des tickets en attente de traitement avec les retours via un Batch

### PRODUCTION - EN PERIODE DE GARANTIE : 
=> Module de retour visible pour les administrateurs seulement
=> Affichage du compteur de jours restant de garantie

1 - Création d'un ticket par le client :
- Enregistrement du ticket sur le site
- 2 Mails (Client / Chef de projet revo) journalier avec liste des tickets en attente de traitement avec les retours via un Batch

### PRODUCTION - HORS PERIODE DE GARANTIE : 
=> Module de retour visible pour les administrateurs seulement
=> Affichage du compteur de nombre de crédit ticket restant
=> Si moins d’1H de crédit : Ajout d'un lien pour prendre un pack de crédit 5H ou 10H, puis création de la facture associée dans Lucy

1 - Création d'un ticket par le client :
- Enregistrement du ticket sur le site
- Mail Chef de projet revo à l'ajout du ticket

2 - Réponse par le chef de projet : 
- Indication du nombre d'heure passé
- Déduction du crédit de temps dans Lucy par API
- Mail Client à l'ajout d'une réponse au ticket

## Déploiement Pypi

1 - pip install build twine<br>
2 - python -m build<br>
3 - python -m twine upload dist/*<br>
4 - Indiquer le token présent dans 1Password