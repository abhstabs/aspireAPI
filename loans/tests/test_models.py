from datetime import datetime, date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from model_bakery import baker

from loans.models import (
    LoanApplication,
    LoanState,
    LoanRepayment,
    LoanRepaymentState,
    split_amount_for_excess_payment,
    split_amount_for_new_loan,
)
from loans.exceptions import (
    LoanNotApprovedError,
    PaymentPendingError,
    LoanRepaymentComplete,
)


class LoanApplicationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test user
        cls.test_user = get_user_model().objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="test",
            last_name="user",
        )

        # Create a loan application
        cls.test_loan_application = baker.make(
            LoanApplication,
            user=cls.test_user,
            amount=500,
            term=10,
            date=datetime.now().date() - timedelta(days=1),
        )

    def test_pending_amount(self):
        """
        Test pending_amount method of LoanApplication model
        """
        # Create a loan repayment
        baker.make(
            LoanRepayment,
            loan=self.test_loan_application,
            amount=100,
            date_of_payment=datetime.now().date() - timedelta(days=1),
            state=LoanRepaymentState.PAID,
        )

        # Assert pending_amount equals the remaining amount
        self.assertEqual(self.test_loan_application.pending_amount, Decimal("400.00"))

    def test_pending_terms(self):
        """
        Test pending_terms method of LoanApplication model
        """
        # Create two loan repayments
        baker.make(
            LoanRepayment,
            loan=self.test_loan_application,
            amount=50,
            date_of_payment=datetime.now().date() - timedelta(days=1),
            state=LoanRepaymentState.PENDING,
        )

        baker.make(
            LoanRepayment,
            loan=self.test_loan_application,
            amount=50,
            date_of_payment=datetime.now().date() - timedelta(days=2),
            state=LoanRepaymentState.PENDING,
        )

        # Assert pending_terms equals the number of pending repayments
        self.assertEqual(self.test_loan_application.pending_terms, 2)

    def test_update_state(self):
        """
        Test update_state method of LoanApplication model
        """
        # Update loan state to "APPROVED"
        self.test_loan_application.update_state(LoanState.APPROVED)

        # Assert loan state is "APPROVED"
        self.assertEqual(self.test_loan_application.state, LoanState.APPROVED)

    def test_update_as_paid(self):
        """
        Test update_as_paid method of LoanApplication model
        """
        # Create a loan repayment with amount equal to loan amount
        baker.make(
            LoanRepayment,
            loan=self.test_loan_application,
            amount=500,
            date_of_payment=datetime.now().date() - timedelta(days=1),
            state=LoanRepaymentState.PAID,
        )

        # Update loan state to "PAID"
        self.test_loan_application.update_as_paid()

        # Assert loan state is "PAID"
        self.assertEqual(self.test_loan_application.state, LoanState.PAID)

    def test_update_state_and_refresh_object(self):
        """
        Test update_state_and_refresh_object method of LoanApplication model
        """
        # Update loan state to "REJECTED"
        self.test_loan_application.update_state_and_refresh_object(LoanState.REJECTED)

        self.assertEqual(self.test_loan_application.state, LoanState.REJECTED)


class LoanRepaymentTestCase(TestCase):
    def setUp(self):
        self.loan = baker.make(
            LoanApplication,
            amount=Decimal("1000"),
            term=5,
            state=LoanState.APPROVED,
        )
        self.repayment = baker.make(
            LoanRepayment,
            self.loan.term,
            loan=self.loan,
            amount=Decimal("200"),
            state=LoanRepaymentState.PENDING,
            date_of_payment=date.today(),
        )[0]

    def test_create_loan_repayment(self):
        """
        Test creating a new loan repayment
        """
        repayment = baker.make(
            LoanRepayment,
            loan=self.loan,
            amount=Decimal("300"),
            state=LoanRepaymentState.PENDING,
            date_of_payment=date.today(),
        )
        self.assertEqual(str(repayment), f"{repayment.id} - {repayment.amount}")

    def test_save_loan_repayment(self):
        """
        Test saving a loan repayment
        """
        self.repayment.amount = Decimal("300")
        self.repayment.save()
        self.assertEqual(self.repayment.amount, Decimal("300"))
        self.assertEqual(self.repayment.state, LoanRepaymentState.PAID)

    def test_make_payment(self):
        """
        Test making a payment for a loan repayment
        """
        self.repayment.make_payment(Decimal("200"))
        self.assertEqual(self.repayment.state, LoanRepaymentState.PAID)
        self.assertEqual(self.repayment.amount, Decimal("200"))
        self.assertEqual(self.loan.pending_amount, Decimal("800"))
        self.assertEqual(self.loan.pending_terms, 4)

    def test_check_validity_for_payment(self):
        """
        Test checking validity for loan repayment payment
        """

        loan = baker.make(LoanApplication, state=LoanState.PENDING)
        loan_repayment = baker.make(
            LoanRepayment,
            loan=loan,
            state=LoanRepaymentState.PENDING,
            amount=loan.amount / 3,
        )
        self.assertRaises(
            LoanNotApprovedError, loan_repayment.check_validity_for_payment
        )

        loan.state = LoanState.APPROVED
        loan.save()

        loan_repayment.amount = loan.amount
        loan_repayment.save()
        self.assertRaises(
            LoanRepaymentComplete, loan_repayment.check_validity_for_payment
        )


class LoanRepaymentTestCaseNegative(TestCase):
    def setUp(self):
        self.loan = baker.make(
            LoanApplication,
            amount=Decimal("1000"),
            term=5,
            state=LoanState.APPROVED,
        )
        self.repayment = baker.make(
            LoanRepayment,
            self.loan.term,
            loan=self.loan,
            amount=Decimal("200"),
            state=LoanRepaymentState.PENDING,
            date_of_payment=date.today(),
        )[0]

    def test_save_loan_repayment_invalid_amount(self):
        """
        Test saving a loan repayment with an invalid amount
        """
        self.repayment.amount = Decimal("100")
        self.assertRaises(ValueError, self.repayment.save)

    def test_make_payment_invalid_repayment(self):
        """
        Test making a payment for an invalid loan repayment
        """
        self.repayment.state = LoanRepaymentState.PAID
        self.assertRaises(
            LoanRepaymentComplete, self.repayment.make_payment, Decimal("200")
        )

    def test_make_payment_excess_amount(self):
        """
        Test making a payment with an amount greater than the loan amount
        """
        self.assertRaises(ValueError, self.repayment.make_payment, Decimal("1200"))

    def test_make_payment_prior_payment_pending(self):
        """
        Test making a payment when there are prior payments pending
        """
        next_repayment = baker.make(
            LoanRepayment,
            loan=self.loan,
            amount=Decimal("100"),
            state=LoanRepaymentState.PENDING,
            date_of_payment=date.today() + timedelta(days=7),
        )

        self.assertRaises(
            PaymentPendingError, next_repayment.make_payment, Decimal("200")
        )

    def test_split_amount_for_excess_payment(self):
        """
        Test splitting the amount for excess payment
        """
        repayments = baker.make(
            LoanRepayment,
            _quantity=3,
            loan=self.loan,
            amount=Decimal("100"),
            state=LoanRepaymentState.PENDING,
        )
        repayments_pending = split_amount_for_excess_payment(
            Decimal("400"), 4, repayments
        )
        self.assertEqual(len(repayments_pending), 3)
        self.assertEqual(repayments_pending[0].amount, Decimal("100"))
        self.assertEqual(repayments_pending[1].amount, Decimal("100"))
        self.assertEqual(repayments_pending[2].amount, Decimal("200"))

    def test_split_amount_for_new_loan(self):
        """
        Test splitting the amount for a new loan
        """
        repayments = split_amount_for_new_loan(Decimal("1000"), 5, date.today())
        self.assertEqual(len(repayments), 5)
        self.assertEqual(repayments[0].amount, Decimal("200"))
        self.assertEqual(repayments[1].amount, Decimal("200"))
        self.assertEqual(repayments[2].amount, Decimal("200"))
        self.assertEqual(repayments[3].amount, Decimal("200"))
        self.assertEqual(repayments[4].amount, Decimal("200"))
        self.assertEqual(repayments[-1].amount, Decimal("200"))
