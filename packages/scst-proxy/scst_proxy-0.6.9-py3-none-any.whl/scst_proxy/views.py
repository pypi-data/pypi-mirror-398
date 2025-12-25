from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
from django.template.exceptions import TemplateDoesNotExist
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .models import PluginSettings
from . import PLUGIN_NAME, PLUGIN_TITLE


@login_required
@permission_required(f'{PLUGIN_NAME}.can_view_page')
def main_view(request):
    try:
        permissions = list(request.user.get_all_permissions())
        accessPermission = f'{PLUGIN_NAME}.can_view_page'
        if accessPermission not in permissions:
            raise PermissionDenied("У вас нет доступа к этому плагину")
        
        context = {
            'PAGE_TITLE': PLUGIN_TITLE,
            'PROXY_URL': PluginSettings.get_settings().proxy_address,
            'CHARACTER_NAME': request.user.profile.main_character.character_name.replace(' ','_')
        }

        return render(request, f'{ PLUGIN_NAME }/main.html', context)
    
    except TemplateDoesNotExist as e:
        return JsonResponse(
            {'status': 'error', 'message': 'Template not found'},
            status=500
        )



@login_required
@permission_required(f'{PLUGIN_NAME}.can_view_page')
@require_http_methods(["POST"])
def call_api_endpoint(request):
    # Get user IP address
    # client_ip, is_routable = get_client_ip(request)
    settings = PluginSettings.get_settings()
    
    character_name = request.user.profile.main_character.character_name
    
    # Get API key from user settings (you'll need to implement this)
    try:
        api_key = settings.api_key
    except AttributeError:
        return JsonResponse(
            {'status': 'error', 'message': 'API key not configured'},
            status=400
        )
    
    # Prepare API request
    api_url = settings.api_endpoint + 'add' # Replace with your API URL
    newPassword = User.objects.make_random_password()
    params = {
        'password': newPassword,
        'login': character_name.replace(' ','_'),
        'apikey': api_key
    }
    
    try:
        response = requests.post(api_url, json=params, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        return JsonResponse({'response':response.json(), 'password': newPassword })
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e), 'params': str(params), 'endpoint': api_url},
            status=500
        )