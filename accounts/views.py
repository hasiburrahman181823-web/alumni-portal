from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView

from .forms import LoginForm, ProfileForm, RegisterForm, UserUpdateForm
from .mixins import AdminRequiredMixin, role_required
from .models import Profile, User


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)  # saves the user (signal creates the Profile)
        login(self.request, self.object, backend="accounts.backends.EmailOrUsernameBackend")
        messages.success(self.request, "Welcome! Your account has been created. Complete your profile next.")
        return redirect("accounts:profile_edit")


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class ProfileDetailView(LoginRequiredMixin, DetailView):
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return get_object_or_404(Profile.objects.select_related("user"), user__username=self.kwargs["username"])


class ProfileEditView(LoginRequiredMixin, View):
    """Edits the User and Profile together. Both forms must be valid before anything is saved."""

    template_name = "accounts/profile_edit.html"

    def _forms(self, request, bound=False):
        data = request.POST if bound else None
        files = request.FILES if bound else None
        return (
            UserUpdateForm(data, instance=request.user),
            ProfileForm(data, files, instance=request.user.profile),
        )

    def get(self, request):
        user_form, profile_form = self._forms(request)
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})

    def post(self, request):
        user_form, profile_form = self._forms(request, bound=True)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():  # all-or-nothing
                user_form.save()
                profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile", username=request.user.username)
        messages.error(request, "Please fix the errors below.")
        return render(request, self.template_name, {"user_form": user_form, "profile_form": profile_form})


class AlumniListView(LoginRequiredMixin, ListView):
    """Alumni directory with keyword search, graduation-year filter and pagination."""

    template_name = "accounts/alumni_list.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        qs = Profile.objects.select_related("user").filter(user__is_active=True)
        q = self.request.GET.get("q", "").strip()
        year = self.request.GET.get("year", "").strip()
        if q:
            qs = qs.filter(
                Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__username__icontains=q)
                | Q(company__icontains=q)
                | Q(job_title__icontains=q)
                | Q(department__icontains=q)
                | Q(location__icontains=q)
            )
        if year.isdigit():  # ignore junk instead of raising ValueError
            qs = qs.filter(graduation_year=int(year))
        return qs.order_by("-graduation_year", "user__first_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["years"] = (
            Profile.objects.exclude(graduation_year__isnull=True)
            .order_by("-graduation_year")
            .values_list("graduation_year", flat=True)
            .distinct()
        )
        ctx["q"] = self.request.GET.get("q", "")
        ctx["year"] = self.request.GET.get("year", "")
        return ctx


class UserManageListView(AdminRequiredMixin, ListView):
    """Admin-only screen to promote/demote users."""

    model = User
    template_name = "accounts/user_manage.html"
    context_object_name = "users"
    paginate_by = 20
    queryset = User.objects.order_by("username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["roles"] = User.Role.choices
        return ctx


@require_POST
@role_required(User.Role.ADMIN)
def change_role(request, pk):
    target = get_object_or_404(User, pk=pk)
    new_role = request.POST.get("role")
    if target == request.user:
        messages.error(request, "You can't change your own role.")
    elif new_role not in User.Role.values:
        messages.error(request, "Invalid role.")
    else:
        target.role = new_role
        target.save(update_fields=["role"])
        messages.success(request, f"{target.username} is now {target.get_role_display()}.")
    return redirect(request.POST.get("next") or "accounts:user_manage")
