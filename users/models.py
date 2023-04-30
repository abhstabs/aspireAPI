import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """
    Object Manager class for the User model
    """

    def create_user(self, first_name, last_name, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email, first name, last name, and password.
        """
        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name, last_name=last_name, email=email, **extra_fields
        )
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(
        self, email, first_name="", last_name="", password=None, **extra_fields
    ):
        """
        Creates and saves a superuser with the given email, first name, last name, and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(first_name, last_name, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Django Model to represent the user of the application. Inhertis from AbstractBaseUser
    Email is used as username for the user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True, db_index=True, blank=False, null=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.first_name} - {self.last_name}"
