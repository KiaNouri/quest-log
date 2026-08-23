from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import Profile


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class ProfileForm(forms.ModelForm):
    """
    `total_xp` and `level` are both system computed and must never be user-editable.

    User can edit their bio and profile picture using this form.
    """

    class Meta:
        model = Profile
        fields = ("bio", "profile_picture")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["bio"].widget = forms.Textarea(
            attrs={
                "rows": 4,
                "maxlength": 300,
                "placeholder": "Tell people a bit about yourself...",
            }
        )
