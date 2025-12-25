from django.apps import AppConfig
from . import PLUGIN_NAME


class ScStProxySettings(AppConfig):
    name = PLUGIN_NAME
    label = PLUGIN_NAME
    default_pesmissions = (f'{PLUGIN_NAME}.can_use_proxy', f'{PLUGIN_NAME}.can_view_page')
    

    def ready(self):
        # Импортируем хуки при загрузке приложения
        from . import hooks  # noqa
        from . import signals