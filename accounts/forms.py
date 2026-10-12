from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile, User

INPUT_CLASSES = (
    "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 "
    "placeholder-slate-400 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600/30 "
    "dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
)
FILE_CLASSES = (
    "block w-full text-sm text-slate-600 dark:text-slate-300 file:mr-3 file:rounded-md file:border-0 "
    "file:bg-teal-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-teal-800 "
    "hover:file:bg-teal-100 dark:file:bg-slate-700 dark:file:text-teal-200"
)


class TailwindFormMixin:
    """Adds Tailwind classes to every widget so templates can just render `{{ field }}`."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-teal-700 focus:ring-teal-600"
            elif isinstance(widget, forms.FileInput):  # also covers ClearableFileInput
                widget.attrs["class"] = FILE_CLASSES
            else:
                widget.attrs["class"] = INPUT_CLASSES


class RegisterForm(TailwindFormMixin, UserCreationForm):
    """Public sign-up. `role` is intentionally NOT a field: everyone starts as a General user."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class LoginForm(TailwindFormMixin, AuthenticationForm):
    username = forms.CharField(label="Username or email", widget=forms.TextInput(attrs={"autofocus": True}))


class UserUpdateForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email


class ProfileForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ("user", "updated_at")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}
