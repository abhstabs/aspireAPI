from decimal import Decimal
from typing import List

from ninja import Router
from aspireAPI.schemas import ErrorSchema

from .schemas import (
    LoanApplicationSchema,
    LoanApplicationInputSchema,
    LoanApprovalSchema,
    LoanRepaymentSchema,
    LoanRepaymentInputSchema,
)
from .models import LoanApplication, LoanRepayment
from .utils import create_new_loan
from .exceptions import LoanError

router = Router()


@router.get("", response={200: List[LoanApplicationSchema]})
def get_loans(request):
    """
    Endpoint to fetch all loans for a given user,
    or all loans if the user is Admin. Grouped by state
    """
    if request.user.is_superuser:
        return LoanApplication.objects.all()

    return LoanApplication.objects.filter(user=request.user).order_by("state")


@router.get("{loan_id}", response={200: LoanApplicationSchema, 403: ErrorSchema})
def get_loan(request, loan_id: str):
    """
    Endpoint to get information about a selected loan id
    """
    loan = LoanApplication.objects.get(id=loan_id)
    if not (request.user.is_superuser or request.user == loan.user):
        return 403, ErrorSchema(message="Unauthorized Access. Not enough permissions")

    return loan


@router.post(
    "", response={201: LoanApplicationSchema, 400: ErrorSchema, 403: ErrorSchema}
)
def create_loan_application(request, loan_application: LoanApplicationInputSchema):
    """
    Endpoing to create a new loan application for the user
    """
    if request.user.is_superuser:
        return 403, ErrorSchema(
            message="Loan can be applied using customer account only"
        )

    try:
        loan = create_new_loan(request.user, loan_application)
        return 201, loan
    except ValueError as exception:
        return 400, ErrorSchema(message=str(exception))


@router.put("", response={200: LoanApplicationSchema, 403: ErrorSchema})
def approve_or_reject_loan(request, loan_application: LoanApprovalSchema):
    """
    Endpoint for the Admin user to approve/reject loans
    """
    if not request.user.is_superuser:
        return 403, ErrorSchema(
            message="Forbidden. You do not have permission for this operation"
        )

    loan_object = LoanApplication.objects.get(id=loan_application.id)
    loan_object.update_state_and_refresh_object(loan_application.state)

    return 200, loan_object


@router.put(
    "payment/{repayment_id}",
    response={200: LoanRepaymentSchema, 400: ErrorSchema, 403: ErrorSchema},
)
def pay_amount(request, repayment_id: int, data: LoanRepaymentInputSchema):
    """
    Endpoint for customers to pay the term amount
    """
    repayment_object = LoanRepayment.objects.get(id=repayment_id)

    if repayment_object.loan.user != request.user:
        return 403, ErrorSchema(message="Authorization Error!")

    try:
        repayment_object.make_payment(data.amount)
        return 200, repayment_object
    except (ValueError, LoanError) as exception:
        return 400, ErrorSchema(message=str(exception))
