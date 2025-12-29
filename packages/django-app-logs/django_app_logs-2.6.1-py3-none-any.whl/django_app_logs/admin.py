from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import path, reverse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.utils.html import format_html
from django.http import Http404
import json

from .models import ActionLog


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'user_display',
        'action_display',
        'content_type',
        'object_repr',
        'object_history_link',
        'ip_address',
    )
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('object_repr', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'content_type',
        'object_id',
        'object_repr',
        'action',
        'user',
        'ip_address',
        'user_agent',
        'changes_display',
        'timestamp',
    )

    fieldsets = (
        ('Objet', {
            'fields': ('content_type', 'object_id', 'object_repr')
        }),
        ('Action', {
            'fields': ('action', 'user', 'timestamp')
        }),
        ('Contexte', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Modifications', {
            'fields': ('changes_display',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'object-history/<int:content_type_id>/<int:object_id>/',
                self.admin_site.admin_view(self.object_history_view),
                name='history_object_history'
            ),
        ]
        return custom_urls + urls

    def object_history_view(self, request, content_type_id, object_id):
        """Vue pour afficher l'historique complet d'un objet."""
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            raise Http404("Type de contenu non trouvé")

        logs = ActionLog.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-timestamp')

        # Récupérer la représentation de l'objet
        if logs.exists():
            object_repr = logs.first().object_repr
        else:
            # Essayer de récupérer l'objet directement
            model_class = content_type.model_class()
            try:
                obj = model_class.objects.get(pk=object_id)
                object_repr = str(obj)
            except model_class.DoesNotExist:
                object_repr = f"{content_type.model} #{object_id} (supprimé)"

        # URL vers l'objet s'il existe encore
        object_url = None
        model_class = content_type.model_class()
        if model_class is not None:
            try:
                obj = model_class.objects.get(pk=object_id)
                object_url = reverse(
                    f'admin:{content_type.app_label}_{content_type.model}_change',
                    args=[object_id]
                )
            except (model_class.DoesNotExist, Exception):
                pass

        context = {
            **self.admin_site.each_context(request),
            'title': f'Historique de {object_repr}',
            'logs': logs,
            'content_type': content_type,
            'object_id': object_id,
            'object_repr': object_repr,
            'object_url': object_url,
        }

        return render(request, 'admin/history/object_history.html', context)

    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.last_name} {obj.user.first_name}".strip() or obj.user.username
        return "Système"
    user_display.short_description = "Utilisateur"

    def action_display(self, obj):
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#ffc107',
            'DELETE': '#dc3545',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = "Action"

    def object_history_link(self, obj):
        """Lien vers l'historique complet de l'objet."""
        url = reverse(
            f'{self.admin_site.name}:history_object_history',
            args=[obj.content_type_id, obj.object_id]
        )
        count = ActionLog.objects.filter(
            content_type=obj.content_type,
            object_id=obj.object_id
        ).count()
        return format_html(
            '<a href="{}" title="Voir tout l\'historique de cet objet">'
            '<i class="fas fa-history"></i> {} action(s)</a>',
            url,
            count
        )
    object_history_link.short_description = "Historique"


    def changes_display(self, obj):
        if not obj.changes:
            return "-"

        history = []
        for field, values in obj.changes.items():
            old_val = values.get('old', '-')
            new_val = values.get('new', '-')

            if isinstance(old_val, dict):
                old_val = old_val.get('repr', json.dumps(old_val, ensure_ascii=False))
            if isinstance(new_val, dict):
                new_val = new_val.get('repr', json.dumps(new_val, ensure_ascii=False))

            data = {
                "field": field,
                "old_val": old_val,
                "new_val": new_val,
            }
            history.append(data)

        context = {
            'history': history
        }
        return render_to_string('admin/partials/action_view.html', context)
    changes_display.short_description = "Détails des modifications"

