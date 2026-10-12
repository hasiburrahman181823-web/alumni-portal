from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),  # POST only (Django 5)
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("profile/<str:username>/", views.ProfileDetailView.as_view(), name="profile"),
    path("alumni/", views.AlumniListView.as_view(), name="alumni_list"),
    path("manage/users/", views.UserManageListView.as_view(), name="user_manage"),
    path("manage/users/<int:pk>/role/", views.change_role, name="change_role"),
]
