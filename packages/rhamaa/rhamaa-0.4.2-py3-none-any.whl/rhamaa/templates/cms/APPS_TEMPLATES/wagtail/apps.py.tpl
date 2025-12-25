from django.apps import AppConfig


class {{app_config_class}}(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{{app_name}}'
    verbose_name = '{{app_verbose_name}}'
