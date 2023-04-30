from ninja import ModelSchema
from .models import User


class UserSchema(ModelSchema):
    """
    Pydantic Representation of the User model
    """

    class Config:
        model = User
        model_fields = ["id", "email", "first_name", "last_name"]


class UserInSchema(ModelSchema):
    """
    User Input schema containing password field too
    """

    class Config:
        model = User
        model_fields = ["email", "first_name", "last_name", "password"]


class LoginSchema(ModelSchema):
    """
    User Input Schema for login to the system
    """

    class Config:
        model = User
        model_fields = ["email", "password"]
