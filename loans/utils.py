from typing import List

from django.db import transaction

from users.models import User
from .models import (
    LoanApplication,
    LoanRepayment,
    LOWER_LOAN_LIMIT,
    split_amount_for_new_loan,
)
from .schemas import LoanApplicationInputSchema


def create_new_loan(
    user: User, loan_application: LoanApplicationInputSchema
) -> LoanApplication:
    """
    Utility function to create a new Loan object
    and to create related Repayment object in a DB transaction
    """
    if loan_application.amount < LOWER_LOAN_LIMIT:
        raise ValueError("Loan Amount Requested is too low")

    repayments: List[LoanRepayment] = split_amount_for_new_loan(
        loan_application.amount, loan_application.term, loan_application.date
    )

    with transaction.atomic():
        loan_object = LoanApplication.objects.create(
            user=user, **loan_application.dict()
        )
        for repayment in repayments:
            repayment.loan = loan_object
        LoanRepayment.objects.bulk_create(repayments)
        return loan_object
