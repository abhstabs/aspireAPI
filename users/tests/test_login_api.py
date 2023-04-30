from users.models import User
from django.test import Client, TestCase

client = Client()


class TestLoginUser(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            password="testpass123",
            email="testloginnew@example.com",
            first_name="Testloginnew",
            last_name="User",
        )
        self.login_url = "/api/users/login/"
        self.credentials = {
            "email": "testloginnew@example.com",
            "password": "testpass123",
        }

    def test_valid_login(self):
        response = client.post(
            self.login_url, self.credentials, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login Successful", str(response.content))

    def test_invalid_login(self):
        self.credentials["password"] = "wrongpassword"
        response = client.post(
            self.login_url, self.credentials, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("User credentials did not match", str(response.content))
