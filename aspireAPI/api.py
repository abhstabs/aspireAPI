from ninja import NinjaAPI
from ninja.security import django_auth

from users.api import router as user_router
from loans.api import router as loan_router

api = NinjaAPI(csrf=True)


api.add_router("/users/", user_router, auth=django_auth)
api.add_router("/loans/", loan_router, auth=django_auth)


@api.get("/status/", response={200: str}, auth=None)
def status(request) -> str:
    """
    Status check endpoint.
    """
    return "The server is up!"
