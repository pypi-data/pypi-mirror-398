import logging
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.apps import apps

from .models import ActionLog, ActionType
from .registry import ActionLogRegistry
from .middleware import RequestContextMiddleware
from .serializers import compute_changes, get_instance_snapshot

logger = logging.getLogger('history')

# Cache pour stocker l'état pré-modification
_pre_save_states = {}
_pre_delete_states = {}


def get_context():
    """Récupère le contexte de la requête courante."""
    return {
        'user': RequestContextMiddleware.get_current_user(),
        'ip_address': RequestContextMiddleware.get_ip_address(),
        'user_agent': RequestContextMiddleware.get_user_agent(),
    }

def _skip_signal():
    # App pas complètement prête (startup, migrate, shell, etc.)
    if not apps.ready:
        return True

    # Migration / transaction en cours
    if connection.in_atomic_block:
        return True

    # Table pas encore créée
    return "django_app_logs_actionlog" not in connection.introspection.table_names()


@receiver(pre_save)
def on_pre_save(sender, instance, raw, using, update_fields, **kwargs):
    """
    Signal pre_save: capture l'état avant modification pour UPDATE.
    """
    if raw:
        return

    if ActionLogRegistry.is_excluded(sender):
        return

    if sender._meta.proxy or sender._meta.abstract:
        return

    # Seulement pour les updates (instance avec pk existant en base)
    if instance.pk:
        try:
            cache_key = (sender, instance.pk)
            old_instance = sender.objects.get(pk=instance.pk)
            _pre_save_states[cache_key] = old_instance
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def on_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """
    Signal post_save: capture CREATE et UPDATE.
    """
    # Ignorer les fixtures (raw=True)
    if raw or _skip_signal():
        return

    # Vérifier si le modèle est exclu
    if ActionLogRegistry.is_excluded(sender):
        return

    # Ignorer les modèles sans table (proxy, abstract)
    if sender._meta.proxy or sender._meta.abstract:
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
        context = get_context()

        if created:
            # CREATE
            action = ActionType.CREATE
            changes = compute_changes(None, instance)
        else:
            # UPDATE
            action = ActionType.UPDATE

            # Récupérer l'ancien état depuis le cache
            cache_key = (sender, instance.pk)
            old_instance = _pre_save_states.pop(cache_key, None)

            changes = compute_changes(old_instance, instance)

            # Si aucun changement significatif, ne pas logger
            if not changes:
                return

        ActionLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            object_repr=str(instance)[:255],
            action=action,
            user=context['user'],
            ip_address=context['ip_address'],
            user_agent=context['user_agent'] or '',
            changes=changes,
        )

    except Exception as e:
        # En production, logger l'erreur sans faire échouer la transaction
        logger.exception(f"Erreur lors du tracking de {sender}: {e}")


@receiver(pre_delete)
def on_pre_delete(sender, instance, using, **kwargs):
    """
    Signal pre_delete: capture l'état avant suppression.
    """
    if ActionLogRegistry.is_excluded(sender):
        return

    if sender._meta.proxy or sender._meta.abstract:
        return

    cache_key = (sender, instance.pk)
    _pre_delete_states[cache_key] = {
        'snapshot': get_instance_snapshot(instance),
        'repr': str(instance)[:255],
    }


@receiver(post_delete)
def on_post_delete(sender, instance, using, **kwargs):
    """
    Signal post_delete: enregistre la suppression.
    """
    if ActionLogRegistry.is_excluded(sender):
        return

    if sender._meta.proxy or sender._meta.abstract:
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
        context = get_context()

        cache_key = (sender, instance.pk)
        pre_state = _pre_delete_states.pop(cache_key, None)

        if pre_state:
            changes = pre_state['snapshot']
            object_repr = pre_state['repr']
        else:
            changes = get_instance_snapshot(instance)
            object_repr = str(instance)[:255]

        ActionLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            object_repr=object_repr,
            action=ActionType.DELETE,
            user=context['user'],
            ip_address=context['ip_address'],
            user_agent=context['user_agent'] or '',
            changes=changes,
        )

    except Exception as e:
        logger.exception(f"Erreur lors du tracking suppression de {sender}: {e}")
