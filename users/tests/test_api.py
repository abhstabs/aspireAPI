from django.test import TestCase, Client
from model_bakery import baker

from users.models import User


class TestUserEndpoints(TestCase):
    def setUp(self):
        self.client = Client()
        user = baker.make(
            User,
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        self.client.force_login(user)
        self.base_url = "/api/users/"

    def test_me_endpoint_with_authenticated_user(self):
        """
        Test that me endpoint returns correct details of the authenticated user.
        """
        url = f"{self.base_url}me/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "test@example.com")

    def test_me_endpoint_with_unauthenticated_user(self):
        """
        Test that me endpoint returns 401 unauthorized status code if user is not authenticated.
        """
        self.client.logout()
        url = f"{self.base_url}me/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Unauthorized")

    def test_create_user_endpoint_with_valid_data(self):
        """
        Test that create user endpoint creates a new user with valid data and
        returns 201 created status code.
        """
        url = f"{self.base_url}"
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "password123",
        }
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "newuser@example.com")

    def test_create_user_endpoint_with_existing_email(self):
        """
        Test that create user endpoint
        returns 400 bad request status code if email is already registered.
        """
        baker.make(User, email="existing@example.com", password="password123")
        url = f"{self.base_url}"
        data = {
            "email": "existing@example.com",
            "password": "password456",
            "first_name": "TestNew",
            "last_name": "User",
        }
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Email already registered. Please login with registered email",
        )

    def test_login_user_endpoint_with_invalid_credentials(self):
        """
        Test that login user endpoint returns 403 forbidden status code if credentials are invalid.
        """
        baker.make(User, email="testfailurelogin@example.com", password="password123")
        url = f"{self.base_url}login/"
        data = {"email": "testfailurelogin@example.com", "password": "invalidpassword"}
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["message"],
            "User credentials did not match. Please try again",
        )

    def test_logout_user_endpoint(self):
        """
        Test that logout user endpoint logs out the current user and returns 204 no content status code.
        """
        url = f"{self.base_url}logout/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_status_api(self):
        """
        Test to check if the status API returns a 200 status code
        """
        url = "/api/status/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "The server is up!")
