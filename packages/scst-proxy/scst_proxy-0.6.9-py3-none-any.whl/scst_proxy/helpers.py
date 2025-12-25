
from django.http import JsonResponse
from scst_proxy.models import PluginSettings
import requests


# def add_menu_items():
#     return [
#         {
#             'label': 'Регистрация прокси',
#             'url': 'scst_proxy:main',
#             'icon': 'fa-home-icon',
#         }
#     ]

def remove_user_api_call(user):
    settings = PluginSettings.get_settings()
    
    character_name = user.profile.main_character.character_name
    
    # Get API key from user settings (you'll need to implement this)
    try:
        api_key = settings.api_key
    except AttributeError:
        return JsonResponse(
            {'status': 'error', 'message': 'API key not configured'},
            status=400
        )
    
    # Prepare API request
    api_url = settings.api_endpoint + 'delete' # Replace with your API URL
    params = {
        'login': character_name,
        'apikey': api_key
    }
    
    try:
        response = requests.delete(api_url, json=params, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        return JsonResponse({'response':response.json()})
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e), 'params': str(params), 'endpoint': api_url},
            status=500
        )