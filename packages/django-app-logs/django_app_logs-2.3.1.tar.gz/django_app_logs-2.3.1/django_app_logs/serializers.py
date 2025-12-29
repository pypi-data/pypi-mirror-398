import json
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from django.db.models import Model
from django.db.models.fields.files import FieldFile


class ActionLogEncoder(json.JSONEncoder):
    """
    Encodeur JSON personnalisé pour les valeurs de modèles Django.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, FieldFile):
            return obj.name if obj else None
        elif isinstance(obj, Model):
            return {
                'pk': obj.pk,
                'repr': str(obj),
                'model': f"{obj._meta.app_label}.{obj._meta.model_name}"
            }
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        return super().default(obj)


def serialize_value(value):
    """Sérialise une valeur pour stockage JSON."""
    return json.loads(json.dumps(value, cls=ActionLogEncoder))


def get_model_field_value(instance, field_name):
    """
    Récupère la valeur d'un champ de manière sécurisée.
    Gère les FK en récupérant le PK et la représentation.
    """
    try:
        field = instance._meta.get_field(field_name)
        value = getattr(instance, field_name, None)

        # Pour les ForeignKey, on stocke le PK + représentation
        if hasattr(field, 'related_model') and field.related_model:
            if value is not None:
                return {
                    'pk': value.pk,
                    'repr': str(value)
                }
            return None

        return serialize_value(value)
    except Exception:
        return None


def compute_changes(old_instance, new_instance, fields_to_track=None):
    """
    Calcule les différences entre deux instances d'un modèle.

    Args:
        old_instance: Instance avant modification (ou None pour CREATE)
        new_instance: Instance après modification
        fields_to_track: Liste de noms de champs à tracker (None = tous)

    Returns:
        dict: {field_name: {'old': value, 'new': value}, ...}
    """
    changes = {}

    # Champs à ignorer
    ignored_fields = {'id', 'pk', 'created_at', 'updated_at'}

    # Déterminer les champs à tracker
    if fields_to_track is None:
        fields = [
            f.name for f in new_instance._meta.get_fields()
            if hasattr(f, 'column') and f.name not in ignored_fields
        ]
    else:
        fields = [f for f in fields_to_track if f not in ignored_fields]

    for field_name in fields:
        new_value = get_model_field_value(new_instance, field_name)

        if old_instance is None:
            # CREATE: toutes les nouvelles valeurs
            if new_value is not None:
                changes[field_name] = {'new': new_value}
        else:
            # UPDATE: seulement les différences
            old_value = get_model_field_value(old_instance, field_name)
            if old_value != new_value:
                changes[field_name] = {'old': old_value, 'new': new_value}

    return changes


def get_instance_snapshot(instance):
    """
    Capture un snapshot complet d'une instance (pour DELETE).
    """
    snapshot = {}
    ignored_fields = {'id', 'pk'}

    for field in instance._meta.get_fields():
        if hasattr(field, 'column') and field.name not in ignored_fields:
            value = get_model_field_value(instance, field.name)
            if value is not None:
                snapshot[field.name] = {'old': value}

    return snapshot
