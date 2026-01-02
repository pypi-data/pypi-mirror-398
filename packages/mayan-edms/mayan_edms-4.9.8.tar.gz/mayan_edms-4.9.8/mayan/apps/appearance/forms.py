from mayan.apps.forms import forms

from .models import Theme, UserThemeSetting


class ThemeForm(forms.ModelForm):
    class Meta:
        fields = ('label', 'stylesheet')
        model = Theme


class UserThemeSettingForm(forms.ModelForm):
    class Meta:
        fields = ('theme',)
        model = UserThemeSetting
        widgets = {
            'theme': forms.Select(
                attrs={
                    'class': 'select2'
                }
            )
        }


class UserThemeSettingForm_view(forms.DetailForm):
    class Meta:
        fields = ('theme',)
        model = UserThemeSetting
