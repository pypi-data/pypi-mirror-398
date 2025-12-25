from celery import shared_task
import requests
import logging

from scst_proxy.helpers import remove_user_api_call

logger = logging.getLogger(__name__)

@shared_task
def send_permission_removed_notification_task(user):
    try:
        logger.info(f"Уведомление об изменении состояния пользователя {user.username} отправлено успешно.")
        remove_user_api_call(user)
    except requests.RequestException as e:
        logger.error(f"Ошибка при отправке уведомления об изменении состояния пользователя: {e}")
        # Опционально: реализуйте повторные попытки или уведомления администраторов