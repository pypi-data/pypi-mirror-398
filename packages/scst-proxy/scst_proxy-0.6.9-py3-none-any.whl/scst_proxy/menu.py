from allianceauth.menu import menu_factory

@menu_factory.register
def register_menu_item():
    """Глобальное меню, отображаемое в левом меню."""
    return {
        'label': 'Your Menu Item',
        'url': 'your-url-name',  # URL-шаблон для вашего пункта меню
        'order': 100,  # Порядок отображения пункта меню в меню
    }