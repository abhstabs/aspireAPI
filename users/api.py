from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout
from ninja import Router

from aspireAPI.schemas import ErrorSchema
from .schemas import UserSchema, UserInSchema, LoginSchema
from .models import User

router = Router()


@router.get("me/", response={200: UserSchema, 401: ErrorSchema})
def me(request):
    """
    Get details of the current user
    """
    return 200, request.user


@router.post("", response={201: UserSchema, 400: ErrorSchema}, auth=None)
def create_user(request, user: UserInSchema):
    """
    Endpoint to create a new user for the application.
    Authentication is turned off for the endpoint
    """
    try:
        return 201, User.objects.create_user(**user.dict())
    except IntegrityError:
        return 400, ErrorSchema(
            message="Email already registered. Please login with registered email"
        )


@router.post("login/", auth=None, response={200: str, 403: ErrorSchema})
def login_user(request, credentials: LoginSchema):
    """
    Endpoint to login user to the system.
    Authentication used is username password based authentication
    Authentication is turned off for the endpoint.
    """
    user = authenticate(
        request, username=credentials.email, password=credentials.password
    )
    if not user:
        return 403, ErrorSchema(
            message="User credentials did not match. Please try again"
        )

    login(request, user)
    return 200, "Login Successful"


@router.post("logout/", response={204: None})
def logout_user(request):
    """
    Endpoint to logut the current user from system
    """
    logout(request)
    return 204, None
