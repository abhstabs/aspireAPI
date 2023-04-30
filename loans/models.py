from datetime import date, datetime, timedelta
from decimal import Decimal

import uuid
from typing import List
from django.contrib.auth import get_user_model
from django.db import models, transaction

from .exceptions import LoanNotApprovedError, LoanRepaymentComplete, PaymentPendingError

LOWER_LOAN_LIMIT = Decimal(100.00)


class LoanState(models.TextChoices):
    """
    Choice class to represent the possible values of Loan Status
    The first is the value inserted into the database
    Second is the human readable form of the value
    """

    PENDING = "PENDING", "PENDING"
    APPROVED = "APPROVED", "APPROVED"
    PAID = "PAID", "PAID"
    REJECTED = "REJECTED", "REJECTED"


class LoanRepaymentState(models.TextChoices):
    """
    Class to represent various states of Repayment
    """

    PENDING = "PENDING", "PENDING"
    PAID = "PAID", "PAID"


class LoanApplication(models.Model):
    """
    Model for Loan Application of a User
    Foreign Key: User
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(
        get_user_model(), related_name="applications", on_delete=models.CASCADE
    )
    term = models.PositiveIntegerField(null=False, blank=False)
    amount = models.DecimalField(
        max_digits=8, decimal_places=2, null=False, blank=False
    )
    date = models.DateField(null=False, blank=False)
    state = models.CharField(
        max_length=20, choices=LoanState.choices, default=LoanState.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Loan Application"
        verbose_name_plural = "Loan Applications"

    def __str__(self) -> str:
        return f"{self.user} - {self.amount} - {self.get_state_display()}"

    @property
    def pending_amount(self) -> Decimal:
        """
        Return the pending amount for loan, i.e., amount not paid yet
        """
        paid_amount: Decimal = (
            self.repayments.filter(state=LoanRepaymentState.PAID)
            .aggregate(models.Sum("amount"))
            .get("amount__sum")
        )
        return self.amount - paid_amount if paid_amount else self.amount

    @property
    def pending_terms(self) -> int:
        """
        Return the no of pending terms for the loan
        """
        return self.repayments.filter(state=LoanRepaymentState.PENDING).count()

    def update_state(self, state: str):
        """
        Update the state of loan according to the input provided
        """
        self.state = state
        self.save()

    def update_as_paid(self):
        """
        Update the state of loan as Paid after all payments are complete
        """
        return self.update_state(LoanState.PAID)

    def update_state_and_refresh_object(self, state: str):
        """
        Update the state of the loan and return the object from the database
        """
        self.update_state(state)
        self.refresh_from_db()


class LoanRepayment(models.Model):
    """
    Model for Loan Repayment
    Foreign Key: LoanApplication
    """

    loan = models.ForeignKey(
        LoanApplication, related_name="repayments", on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=8, decimal_places=2, null=False, blank=False
    )
    date_of_payment = models.DateField(null=False, blank=False)
    state = models.CharField(max_length=20, choices=LoanRepaymentState.choices)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Loan Repayment"
        verbose_name_plural = "Loan Repayments"

    def __str__(self) -> str:
        return f"{self.id} - {self.amount}"

    def save(self, *args, **kwargs):
        """
        Overriding default save functionality for the model
        If payment > amount, adjusting future repayments accordingly
        """

        if not self.pk:
            # object creation, no change needed
            return super().save(*args, **kwargs)

        old_data = LoanRepayment.objects.get(pk=self.pk)
        if self.amount < old_data.amount:
            raise ValueError(
                "Amount Paid should be greater than or equal to Payment amount"
            )

        if self.amount > self.loan.pending_amount:
            raise ValueError("Amount Paid is more than Loan amount")

        pending_loan_terms = self.loan.pending_terms - 1

        if pending_loan_terms == 0:
            with transaction.atomic():
                self.state = LoanRepaymentState.PAID
                super().save(*args, **kwargs)
                return self.loan.update_as_paid()

        if self.amount == old_data.amount:
            # No change in repayment amount
            self.state = LoanRepaymentState.PAID
            return super().save(*args, **kwargs)

        # Amount Paid > Repayment amount, distribute the other Repayments
        pending_loan_amount = self.loan.pending_amount - self.amount
        repayments_pending = list(
            self.loan.repayments.filter(state=LoanRepaymentState.PENDING).exclude(
                id=self.pk
            )
        )
        repayments_pending = split_amount_for_excess_payment(
            pending_loan_amount, pending_loan_terms, repayments_pending
        )
        with transaction.atomic():
            self.state = LoanRepaymentState.PAID
            super().save(*args, **kwargs)
            LoanRepayment.objects.bulk_update(repayments_pending, fields=["amount"])

        return None

    def check_validity_for_payment(self):
        """
        Checks before accepting user payment for loan
        """
        if self.state == LoanRepaymentState.PAID:
            raise LoanRepaymentComplete("Repayment is complete. No need to pay again!")

        if not self.loan.state == LoanState.APPROVED:
            raise LoanNotApprovedError("Cannot Repay an unapproved loan")

        if self.loan.repayments.filter(
            date_of_payment__lt=self.date_of_payment
        ).exists():
            raise PaymentPendingError(
                "Error! Skipping Prior payment. Please pay earlier payments first"
            )

    def make_payment(self, amount: Decimal):
        """
        Method to save the payment to the loan
        """
        self.check_validity_for_payment()
        self.amount = amount
        self.save()
        self.refresh_from_db()
        return self


def add_remaining_amount_to_last_repayment(
    repayments: List[LoanRepayment], amount: Decimal, repayment_amount: Decimal
) -> None:
    # Calculate any remaining amount and add it to the last repayment
    remaining_amount = amount - (repayments[0].amount * Decimal(len(repayments)))
    last_repayment = repayments[-1]
    last_repayment.amount += remaining_amount


def split_amount_for_excess_payment(
    amount: Decimal, num_terms: int, repayments: List[LoanRepayment]
) -> List[LoanRepayment]:
    """
    Divide the amount of loan into equal repayments and
    prevent any rounding error
    """

    repayment_amount = amount / Decimal(num_terms)

    for obj in repayments:
        obj.amount = Decimal(round(repayment_amount, 2))

    add_remaining_amount_to_last_repayment(repayments, amount, repayment_amount)
    return repayments


def split_amount_for_new_loan(
    amount: Decimal, num_terms: int, start_date: date
) -> List[LoanRepayment]:
    """
    Divide the amount of loan into equal repayments and
    prevent any rounding error
    """

    repayment_amount = amount / Decimal(num_terms)
    repayments = [
        LoanRepayment(
            amount=Decimal(round(repayment_amount, 2)),
            state=LoanRepaymentState.PENDING,
            date_of_payment=start_date + timedelta(days=7 * (i + 1)),
        )
        for i in range(num_terms)
    ]

    # Calculate any remaining amount and add it to the last repayment
    add_remaining_amount_to_last_repayment(repayments, amount, repayment_amount)

    return repayments
