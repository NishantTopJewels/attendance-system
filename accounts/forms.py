from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class RoleBasedAuthenticationForm(AuthenticationForm):
    user_role = forms.CharField(widget=forms.HiddenInput(), initial='student')

    def clean(self):
        cleaned_data = super().clean()
        user = self.user_cache
        role = cleaned_data.get('user_role')

        if user:
            if role == 'student':
                if user.is_staff or user.is_superuser:
                    raise forms.ValidationError(
                        _("This account is not registered as a Student. Please use the correct portal."),
                        code='invalid_role',
                    )
            elif role == 'teacher':
                if not user.is_staff or user.is_superuser:
                    raise forms.ValidationError(
                        _("This account is not registered as a Teacher. Please use the correct portal."),
                        code='invalid_role',
                    )
            elif role == 'admin':
                if not user.is_superuser:
                    raise forms.ValidationError(
                        _("This account is not registered as an Admin. Please use the correct portal."),
                        code='invalid_role',
                    )
        return cleaned_data
