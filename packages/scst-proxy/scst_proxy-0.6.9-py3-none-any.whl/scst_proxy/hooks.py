from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook, ServicesHook, get_extension_logger
from django.utils.translation import gettext_lazy as _
from . import urls
from scst_proxy.tasks import send_permission_removed_notification_task
from . import PLUGIN_TITLE, PLUGIN_NAME

logger = get_extension_logger(__name__)

class ProxyRegMenuItem(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            PLUGIN_TITLE,  # Текст в меню
            'fas fa-server',  # Иконка Font Awesome (например, fa-rocket)
            'scst_proxy:main',  # Имя URL из urls.py
            navactive=['scst_proxy:'],  # Подсветка меню при активности
        )
    def render(self, request):
        permissions = list(request.user.get_all_permissions())
        if (f'{PLUGIN_NAME}.can_view_page') in permissions:
            return MenuItemHook.render(self, request)
        return ""

class UpdateUserService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.urlpatterns = self.urlpatterns
        
    #Изменение State
    def update_groups(self, user):
        permissions = list(user.get_all_permissions())
        if f'{PLUGIN_NAME}.can_use_proxy' not in permissions:
            logger.debug('Пользователь %s больше не имеет доступа к прокси серверу' % user)
            send_permission_removed_notification_task(user)
        else :
            logger.debug('Пользователь %s теперь имеет доступ к прокси серверу' % user)
            
        pass

@hooks.register('menu_item_hook')  # Регистрация хука
def register_menu():
  return ProxyRegMenuItem()

@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, PLUGIN_NAME, r"^scst_proxy/")

@hooks.register('services_hook')
def register_service():
    return UpdateUserService()
