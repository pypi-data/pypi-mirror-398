from django import forms
from .models import PluginSettings

class PluginSettingsForm(forms.ModelForm):
    class Meta:
        model = PluginSettings
        fields = '__all__'
        widgets = {
            'api_endpoint': forms.URLInput(attrs={'class': 'form-control'}),
            'api_key': forms.NumberInput(attrs={'class': 'form-control'}),
        }