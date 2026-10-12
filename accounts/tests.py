from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Event, JobPost

from .models import User


def make_user(username, role=User.Role.USER, password="S3cure-pass!"):
    return User.objects.create_user(username, f"{username}@example.com", password, role=role)


class AuthTests(TestCase):
    def test_register_creates_general_user_and_profile(self):
        resp = self.client.post(reverse("accounts:register"), {
            "username": "newbie", "first_name": "N", "last_name": "B", "email": "n@example.com",
            "password1": "Tr1cky-passw0rd", "password2": "Tr1cky-passw0rd", "role": "admin",  # must be ignored
        })
        self.assertRedirects(resp, reverse("accounts:profile_edit"))
        user = User.objects.get(username="newbie")
        self.assertEqual(user.role, User.Role.USER)
        self.assertTrue(hasattr(user, "profile"))

    def test_duplicate_email_rejected(self):
        make_user("a")
        resp = self.client.post(reverse("accounts:register"), {
            "username": "b", "email": "A@example.com", "password1": "Tr1cky-passw0rd", "password2": "Tr1cky-passw0rd",
        })
        self.assertContains(resp, "already exists")

    def test_login_with_email(self):
        make_user("carol")
        self.assertTrue(self.client.login(username="carol@example.com", password="S3cure-pass!"))

    def test_superuser_gets_admin_role(self):
        su = User.objects.create_superuser("root", "root@example.com", "pw")
        self.assertEqual(su.role, User.Role.ADMIN)


class RoleTests(TestCase):
    def setUp(self):
        self.user = make_user("user")
        self.staff = make_user("staff", User.Role.STAFF)
        self.admin = make_user("admin", User.Role.ADMIN)
        self.event_data = {"title": "Reunion", "description": "Hi", "location": "Dhaka", "start_at": "2030-01-01T10:00"}

    def test_only_staff_and_admin_create_events(self):
        url = reverse("portal:event_create")
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url, self.event_data).status_code, 302)
        self.assertEqual(Event.objects.count(), 0)  # denied, redirected home
        self.client.force_login(self.staff)
        self.client.post(url, self.event_data)
        self.assertEqual(Event.objects.count(), 1)

    def test_job_owner_rules(self):
        job = JobPost.objects.create(title="Dev", company="X", location="Y", description="d",
                                     contact_email="a@b.com", posted_by=self.user)
        other = make_user("other")
        url = reverse("portal:job_delete", args=[job.pk])
        self.client.force_login(other)
        self.client.post(url)
        self.assertTrue(JobPost.objects.filter(pk=job.pk).exists())  # not owner -> denied
        self.client.force_login(self.staff)
        self.client.post(url)
        self.assertFalse(JobPost.objects.filter(pk=job.pk).exists())  # staff may moderate

    def test_admin_only_role_change(self):
        url = reverse("accounts:change_role", args=[self.user.pk])
        self.client.force_login(self.staff)
        self.client.post(url, {"role": "admin"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.USER)
        self.client.force_login(self.admin)
        self.client.post(url, {"role": "staff"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.STAFF)

    def test_pages_require_login(self):
        resp = self.client.get(reverse("portal:job_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp["Location"])

    def test_job_search_and_pagination(self):
        for i in range(12):
            JobPost.objects.create(title=f"Engineer {i}", company="Acme", location="Dhaka", description="d",
                                   contact_email="a@b.com", posted_by=self.user)
        self.client.force_login(self.user)
        resp = self.client.get(reverse("portal:job_list"), {"q": "Engineer", "location": "dhaka"})
        self.assertEqual(len(resp.context["jobs"]), 9)
        self.assertEqual(self.client.get(reverse("portal:job_list"), {"q": "zzz"}).context["jobs"].count(), 0)


class ApiTests(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_register_token_and_job_flow(self):
        r = self.api.post("/api/auth/register/", {"username": "mob", "email": "m@example.com", "password": "Tr1cky-passw0rd"})
        self.assertEqual(r.status_code, 201)
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {r.data['token']}")
        self.assertEqual(self.api.get("/api/me/").data["role"], "user")

        # A user cannot promote themselves through the API
        self.api.patch("/api/me/", {"role": "admin", "first_name": "Mo"}, format="json")
        me = self.api.get("/api/me/").data
        self.assertEqual((me["role"], me["first_name"]), ("user", "Mo"))

        r = self.api.post("/api/jobs/", {"title": "QA", "company": "Z", "location": "Dhaka",
                                         "job_type": "full_time", "description": "d", "contact_email": "q@z.com"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["posted_by"], "mob")
        self.assertEqual(self.api.get("/api/jobs/?search=QA").data["count"], 1)

        # General users cannot create events
        r = self.api.post("/api/events/", {"title": "E", "description": "d", "location": "L", "start_at": "2030-01-01T10:00:00Z"})
        self.assertEqual(r.status_code, 403)

    def test_unauthenticated_api_blocked(self):
        self.assertEqual(self.api.get("/api/jobs/").status_code, 401)

    def test_staff_can_create_event_via_api(self):
        staff = make_user("st", User.Role.STAFF)
        self.api.force_authenticate(staff)
        start = (timezone.now() + timedelta(days=3)).isoformat()
        r = self.api.post("/api/events/", {"title": "E", "description": "d", "location": "L", "start_at": start})
        self.assertEqual(r.status_code, 201)
