from django.contrib import admin
from .models import PluginSettings

@admin.register(PluginSettings)
class PluginSettingsAdmin(admin.ModelAdmin):
    list_display = ('api_endpoint','api_key','proxy_address')
    readonly_fields = ('id',)
    
    def has_add_permission(self, request):
        return False if self.model.objects.count() > 0 else super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False