class RetourClientConstantes:
    INCONNU = 'Inconnu'

    CRITIQUE = 'C'
    NORMAL = 'N'
    NON_URGENT = 'B'

    priorite = [
        (CRITIQUE, 'Critique'),
        (NORMAL, 'Normal'),
        (NON_URGENT, 'Non Urgent'),
    ]

    EN_ATTENTE = 'A'
    EN_TRAITEMENT = 'E'
    TRAITE = 'T'
    VALIDE = 'V'
    V2 = 'Z'

    statut = [
        (EN_ATTENTE, 'En attente'),
        (EN_TRAITEMENT, 'En cours'),
        (TRAITE, 'Traité par Revolucy'),
        (VALIDE, 'Retour validé'),
        (V2, 'Demande V2'),
    ]

    statut_client = [
        (EN_ATTENTE, 'En attente'),
        (EN_TRAITEMENT, 'En cours'),
        (TRAITE, 'Traité par Revolucy'),
        (V2, 'Demande V2'),
    ]

    NON_CLASSE = 'N'
    QUESTION = 'Q'
    BUG = 'B'
    AMELIORATION = 'A'

    type = [
        (NON_CLASSE, 'Non classé'),
        (QUESTION, 'Question'),
        (BUG, 'Bug'),
        (AMELIORATION, 'Amélioration'),
    ]

    STATUS_MAPPING_YT = {
        'En attente': 'A',
        'En cours': 'E',
        'Terminé': 'T',
    }

    REVOLUCY = 'R'
    CLIENT = 'C'

    repondant = [
        (REVOLUCY, 'Revolucy'),
        (CLIENT, 'Client'),
    ]

    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    role_chatbot = [
        (ROLE_USER, 'Utilisateur'),
        (ROLE_ASSISTANT, 'Assistant'),
    ]

    class Environnement:
        LOCAL = 'local'
        RECETTE = 'recette'
        PREPRODUCTION = 'preproduction'
        PRODUCTION = 'production'
