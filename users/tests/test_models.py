from django.test import TestCase
from django.db.utils import IntegrityError

from model_bakery import baker

from users.models import User


class UserModelTestCase(TestCase):
    def setUp(self):
        self.user = baker.make(User)

    def test_user_str_method(self):
        self.assertEqual(
            str(self.user), f"{self.user.first_name} - {self.user.last_name}"
        )

    def test_create_user(self):
        email = "test@example.com"
        password = "password"
        first_name = "Test"
        last_name = "User"

        user = User.objects.create_user(
            email=email, password=password, first_name=first_name, last_name=last_name
        )

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
        self.assertTrue(user.check_password(password))

    def test_create_superuser(self):
        email = "test@example.com"
        password = "password"
        first_name = "Test"
        last_name = "User"

        superuser = User.objects.create_superuser(
            email=email, password=password, first_name=first_name, last_name=last_name
        )

        self.assertIsNotNone(superuser.id)
        self.assertEqual(superuser.email, email)
        self.assertEqual(superuser.first_name, first_name)
        self.assertEqual(superuser.last_name, last_name)
        self.assertTrue(superuser.check_password(password))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_user_without_email(self):
        with self.assertRaises(TypeError):
            User.objects.create_user(
                first_name="Test", last_name="User", password="password"
            )

    def test_create_user_with_existing_email(self):
        email = "test@example.com"
        password = "password"
        first_name = "Test"
        last_name = "User"

        baker.make(User, email=email)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
