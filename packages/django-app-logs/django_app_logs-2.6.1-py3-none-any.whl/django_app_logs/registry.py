class ActionLogRegistry:
    """
    Registre des modèles à exclure du tracking automatique.
    """

    _excluded_models = set()

    @classmethod
    def exclude(cls, model_or_label):
        """
        Exclut un modèle du tracking.

        Usage:
            ActionLogRegistry.exclude('operation_app.Transfert')
            ActionLogRegistry.exclude(Transfert)
        """
        if isinstance(model_or_label, str):
            cls._excluded_models.add(model_or_label.lower())
        else:
            label = f"{model_or_label._meta.app_label}.{model_or_label._meta.model_name}"
            cls._excluded_models.add(label.lower())

    @classmethod
    def is_excluded(cls, model):
        """Vérifie si un modèle est exclu."""
        label = f"{model._meta.app_label}.{model._meta.model_name}".lower()
        return label in cls._excluded_models

    @classmethod
    def register_default_exclusions(cls):
        """Enregistre les exclusions par défaut."""
        # Modèles explicitement exclus (ont leur propre système d'archive)
        #cls.exclude('operation_app.transfert')
        #cls.exclude('operation_app.recouvrement')

        # Le modèle ActionLog lui-même (éviter récursion)
        cls.exclude('django_app_logs.actionlog')

        # Modèles Django internes à exclure
        cls.exclude('contenttypes.contenttype')
        cls.exclude('sessions.session')
        cls.exclude('admin.logentry')
        cls.exclude('auth.permission')
