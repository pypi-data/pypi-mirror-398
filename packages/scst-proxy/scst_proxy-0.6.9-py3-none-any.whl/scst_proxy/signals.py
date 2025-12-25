# permission_tracker/signals.py

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user
from django.contrib.auth.models import User, Permission
from scst_proxy.tasks import send_permission_removed_notification_task
import logging


logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=User.user_permissions.through)
def user_permissions_changed(sender, instance, action, pk_set, **kwargs):
    """
    Обработчик сигнала m2m_changed для отслеживания добавления и удаления разрешений пользователя.
    """
    if action == "post_remove":
        # Разрешения удалены у пользователя
        for perm_id in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_id)
                send_permission_removed_notification_task(instance)
                logger.info(f"Permission '{permission.codename}' removed from user '{instance.username}'.")
            except Permission.DoesNotExist:
                logger.error(f"Permission with id {perm_id} does not exist.")

@receiver(m2m_changed, sender=User.groups.through)
def user_group_changed(sender, instance, action, pk_set, **kwargs):
    """
    Обработчик сигнала m2m_changed для отслеживания добавления и удаления группы пользователя.
    """
    if action == "post_remove":
        # Разрешения удалены у пользователя
        for perm_id in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_id)
                logger.info(f"Permission '{permission.codename}' removed from user.")
            except Permission.DoesNotExist:
                logger.error(f"Permission with id {perm_id} does not exist.")