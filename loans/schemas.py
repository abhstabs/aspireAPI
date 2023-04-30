from decimal import Decimal
from typing import List

from ninja import ModelSchema

from users.schemas import UserSchema
from .models import LoanApplication, LoanRepayment


class LoanRepaymentSchema(ModelSchema):
    """
    Schema representation of Loan Repayment model for output
    """

    class Config:
        model = LoanRepayment
        model_fields = ["id", "amount", "date_of_payment", "state"]


class LoanRepaymentInputSchema(ModelSchema):
    """
    Schema representation of Loan Repayment model for output
    """

    class Config:
        model = LoanRepayment
        model_fields = ["amount"]


class LoanApplicationInputSchema(ModelSchema):
    """
    Pydantic/Schema represenation of Loan Application Input Data
    Only contains Term, Amount, and Date
    """

    class Config:
        model = LoanApplication
        model_fields = ["term", "amount", "date"]


class LoanApplicationSchema(ModelSchema):
    """
    Schema representation of Loan Application Output Data
    Contains the Loan Application id, Term, Amount, Date and State
    """

    pending_amount: Decimal
    pending_terms: int
    repayments: List[LoanRepaymentSchema]
    user: UserSchema

    class Config:
        model = LoanApplication
        model_fields = ["id", "term", "amount", "date", "state", "user"]

    def resolve_repayments(self, obj):
        return obj.repayments.all().order_by("state")


class LoanApprovalSchema(ModelSchema):
    """
    Schema representation of Loan Application Approval Data
    Contains Loan Application id and State
    """

    class Config:
        model = LoanApplication
        model_fields = ["id", "state"]
