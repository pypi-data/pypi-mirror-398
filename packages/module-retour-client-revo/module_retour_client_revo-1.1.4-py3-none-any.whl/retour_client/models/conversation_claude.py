from django.db import models
from django.utils import timezone

from retour_client.constantes import RetourClientConstantes


class ConversationClaude(models.Model):
    """Modèle pour stocker l'historique des conversations avec Claude AI"""

    utilisateur = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=RetourClientConstantes.role_chatbot)
    message = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "Conversation Claude"
        verbose_name_plural = "Conversations Claude"
        ordering = ['id']

    def __str__(self):
        return f"{self.utilisateur} - {self.role} - #{self.pk}"

    @classmethod
    def get_conversation_history(cls, session_id, limit=50):
        """Récupère l'historique des messages pour une session donnée"""
        # Utiliser only() pour éviter de charger date_creation qui pose problème avec MySQL timezone
        messages = cls.objects.filter(session_id=session_id).order_by('id').only('role', 'message')[:limit]
        return [
            {"role": msg.role, "content": msg.message}
            for msg in messages
        ]

    @classmethod
    def add_message(cls, session_id, utilisateur, role, message):
        """Ajoute un message à la conversation"""
        return cls.objects.create(
            session_id=session_id,
            utilisateur=utilisateur,
            role=role,
            message=message
        )
