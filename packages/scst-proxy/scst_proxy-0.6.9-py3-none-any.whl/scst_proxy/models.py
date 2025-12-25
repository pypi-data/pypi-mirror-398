from django.db import models
from . import PLUGIN_NAME

class PluginSettings(models.Model):
    """Модель для хранения настроек плагина"""
    api_endpoint = models.URLField(
        max_length=255,
        default="http://proxyreg.ekzoman.ru/",
        verbose_name="API Endpoint"
    )
    api_key = models.CharField(
        max_length=255,
        default="YOUR_API_KEY",
        verbose_name="API ключ"
    )

    proxy_address = models.CharField(
        max_length=255,
        default='scst.proxy.ekzoman.ru',
        verbose_name='Адрес проси сервера'
    )

    class Meta:
        verbose_name = "Настройки плагина"
        verbose_name_plural = "Настройки плагина"
        permissions = [
            ("can_use_proxy","Может использовать прокси сервер"),
            ("can_view_page", "Может смотреть страницу плагина")
        ]

    def __str__(self):
        return PLUGIN_NAME
    
    @classmethod
    def get_settings(cls):
        """Получает или создает настройки по умолчанию"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj