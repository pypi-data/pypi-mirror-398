from django.contrib.contenttypes.models import ContentType

from .models import ActionLog, ActionType
from .middleware import RequestContextMiddleware
from .serializers import compute_changes, get_instance_snapshot


def bulk_create_with_history(model_class, objects, **kwargs):
    """
    Wrapper pour bulk_create avec tracking.

    Usage:
        from history.utils import bulk_create_with_history
        created = bulk_create_with_history(MyModel, [obj1, obj2, obj3])
    """
    created = model_class.objects.bulk_create(objects, **kwargs)

    content_type = ContentType.objects.get_for_model(model_class)
    context = {
        'user': RequestContextMiddleware.get_current_user(),
        'ip_address': RequestContextMiddleware.get_ip_address(),
        'user_agent': RequestContextMiddleware.get_user_agent() or '',
    }

    logs = []
    for obj in created:
        changes = compute_changes(None, obj)
        logs.append(ActionLog(
            content_type=content_type,
            object_id=obj.pk,
            object_repr=str(obj)[:255],
            action=ActionType.CREATE,
            changes=changes,
            **context
        ))

    ActionLog.objects.bulk_create(logs)
    return created


def queryset_delete_with_history(queryset):
    """
    Wrapper pour QuerySet.delete() avec tracking.

    Usage:
        from history.utils import queryset_delete_with_history
        deleted_count = queryset_delete_with_history(MyModel.objects.filter(active=False))
    """
    model_class = queryset.model
    content_type = ContentType.objects.get_for_model(model_class)
    context = {
        'user': RequestContextMiddleware.get_current_user(),
        'ip_address': RequestContextMiddleware.get_ip_address(),
        'user_agent': RequestContextMiddleware.get_user_agent() or '',
    }

    logs = []
    for obj in queryset:
        snapshot = get_instance_snapshot(obj)
        logs.append(ActionLog(
            content_type=content_type,
            object_id=obj.pk,
            object_repr=str(obj)[:255],
            action=ActionType.DELETE,
            changes=snapshot,
            **context
        ))

    ActionLog.objects.bulk_create(logs)
    return queryset.delete()


def get_object_history(obj):
    """
    Récupère l'historique complet d'un objet.

    Usage:
        from history.utils import get_object_history
        history = get_object_history(my_intermed)
    """
    content_type = ContentType.objects.get_for_model(obj)
    return ActionLog.objects.filter(
        content_type=content_type,
        object_id=obj.pk
    ).order_by('-timestamp')


def get_user_actions(user, limit=50):
    """
    Récupère les dernières actions d'un utilisateur.

    Usage:
        from history.utils import get_user_actions
        actions = get_user_actions(request.user)
    """
    return ActionLog.objects.filter(user=user).order_by('-timestamp')[:limit]


def get_object_history_url(obj):
    """
    Retourne l'URL de la page d'historique d'un objet.

    Usage:
        from history.utils import get_object_history_url
        url = get_object_history_url(my_intermed)
        # -> /admin/history/actionlog/object-history/15/42/
    """
    from django.urls import reverse
    content_type = ContentType.objects.get_for_model(obj)
    return reverse(
        'admin:django_app_logs_object_history',
        args=[content_type.pk, obj.pk]
    )


def get_history_link_html(obj):
    """
    Retourne un lien HTML vers l'historique d'un objet.
    Utile pour l'intégration dans d'autres ModelAdmin.

    Usage dans un ModelAdmin:
        from history.utils import get_history_link_html

        def history_link(self, obj):
            return get_history_link_html(obj)
        history_link.short_description = "Historique"
    """
    from django.utils.html import format_html
    url = get_object_history_url(obj)
    count = ActionLog.objects.filter(
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk
    ).count()
    if count > 0:
        return format_html(
            '<a href="{}" title="Voir l\'historique">'
            '<i class="fas fa-history"></i> {} action(s)</a>',
            url, count
        )
    return format_html('<span class="text-muted">Aucun historique</span>')
