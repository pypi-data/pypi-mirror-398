from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ActionType(models.TextChoices):
    CREATE = 'CREATE', 'Création'
    UPDATE = 'UPDATE', 'Modification'
    DELETE = 'DELETE', 'Suppression'


class ActionLog(models.Model):
    """
    Modèle de traçabilité des actions CRUD sur tous les modèles du projet.
    """
    # Relation générique vers l'objet concerné
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Type de contenu"
    )
    object_id = models.PositiveIntegerField(verbose_name="ID objet")
    content_object = GenericForeignKey('content_type', 'object_id')

    # Représentation textuelle de l'objet (utile après suppression)
    object_repr = models.CharField(
        max_length=255,
        verbose_name="Représentation objet",
        blank=True
    )

    # Type d'action
    action = models.CharField(
        max_length=10,
        choices=ActionType.choices,
        verbose_name="Action"
    )

    # Utilisateur ayant effectué l'action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs',
        verbose_name="Utilisateur"
    )

    # Informations de contexte HTTP
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User-Agent"
    )

    # Données avant/après modification
    # Pour CREATE: {"field1": {"new": value}, ...}
    # Pour UPDATE: {"field1": {"old": x, "new": y}, ...} (champs modifiés uniquement)
    # Pour DELETE: {"field1": {"old": value}, ...}
    changes = models.JSONField(
        default=dict,
        verbose_name="Modifications"
    )

    # Timestamp de l'action
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Date/Heure"
    )

    class Meta:
        verbose_name = "Journal d'action"
        verbose_name_plural = "Journal des actions"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Système'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} - {self.action} - {self.object_repr}"
