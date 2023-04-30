from datetime import datetime
from decimal import Decimal

from django.test import TestCase, Client
from model_bakery import baker

from loans.models import LoanApplication, LoanRepayment, LoanState, LoanRepaymentState
from users.models import User


class TestLoanAPIs(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = baker.make(User, is_superuser=False)

    def test_get_loans_for_user(self):
        """
        Test API to get all loans for a given user
        """
        baker.make(
            LoanApplication, user=self.user, state=LoanState.PENDING, _quantity=2
        )
        baker.make(
            LoanApplication,
            user=self.user,
            state=LoanState.APPROVED,
            _quantity=3,
        )
        self.client.force_login(self.user)
        response = self.client.get("/api/loans/", format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    def test_get_all_loans_for_admin(self):
        """
        Test API to get all loan applications for the Admin user
        """

        admin = baker.make(User, is_superuser=True)

        baker.make(LoanApplication, user=self.user, state="NEW", _quantity=2)
        baker.make(LoanApplication, user=self.user, state="APPROVED", _quantity=3)
        baker.make(LoanApplication, user=admin, state="NEW", _quantity=1)

        self.client.force_login(admin)
        response = self.client.get("/api/loans/", content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 6)

    def test_get_loan_for_user(self):
        """
        Test Endpoint to get selected loan applications for the user
        """
        loan = baker.make(LoanApplication, user=self.user, state=LoanState.PENDING)
        self.client.force_login(self.user)
        response = self.client.get(f"/api/loans/{loan.id}", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(loan.id))

    def test_get_loan_for_different_user(self):
        """
        Test Endpoint to get selected loan applications for different user
        The return should be 403
        """
        loan = baker.make(LoanApplication, user=self.user, state=LoanState.PENDING)
        user2 = baker.make(User, is_superuser=False)
        self.client.force_login(user2)
        response = self.client.get(f"/api/loans/{loan.id}", format="json")
        self.assertEqual(response.status_code, 403)

    def test_create_loan_application(self):
        """
        Test API endpoint to create a loan application
        """
        data = {"amount": "1000.00", "term": 3, "date": "2023-05-05"}
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/loans/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["id"], str(self.user.id))

    def test_create_loan_application_with_invalid_data(self):
        """
        Test API endpoint with invalid data to check return status code
        """
        data = {"amount": "1000.00", "term": 3}
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/loans/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 422)

    def test_create_loan_application_with_negative_amount(self):
        """
        Test API endpoint with amount < LIMIT decided by the org
        """
        data = {"amount": "-1000.00", "term": 3, "date": "2023-05-05"}
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/loans/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Loan Amount Requested is too low")

    def test_create_loan_application_as_admin(self):
        """
        Test API endpoint for Loan Application creation as admin
        Admin should not be allowed to create loan requests for users
        """
        admin = baker.make(User, is_superuser=True)
        data = {"amount": "1000.00", "term": 3, "date": "2022-05-05"}

        self.client.force_login(admin)
        response = self.client.post(
            "/api/loans/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["message"],
            "Loan can be applied using customer account only",
        )

    def test_approve_loan_as_admin(self):
        """
        Test API endpoint to approve a given loan application as admin
        """
        admin = baker.make(User, is_superuser=True)
        loan = baker.make(LoanApplication, state=LoanState.PENDING)
        data = {"id": loan.id, "state": LoanState.APPROVED}

        self.client.force_login(admin)
        response = self.client.put("/api/loans/", data, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], LoanState.APPROVED)

    def test_reject_loan_as_admin(self):
        """
        Test API endpoint to reject a given loan application as admin
        """
        admin = baker.make(User, is_superuser=True)
        loan = baker.make(LoanApplication, state=LoanState.PENDING)

        data = {"id": loan.id, "state": LoanState.REJECTED}

        self.client.force_login(admin)
        response = self.client.put("/api/loans/", data, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], LoanState.REJECTED)

    def test_approve_loan_by_non_admin(self):
        """
        Test API endpoint to approve loan by using non admin credentials
        """
        user = baker.make(User, is_superuser=False)
        loan_application = baker.make(LoanApplication)

        # Authenticate the user and send PUT request to approve the loan
        self.client.force_login(user)
        response = self.client.put(
            "/api/loans/",
            data={"id": loan_application.id, "state": LoanState.APPROVED},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["message"],
            "Forbidden. You do not have permission for this operation",
        )


class PayAmountTestCase(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.loan = baker.make(
            LoanApplication,
            user=self.user,
            amount=10000,
            term=3,
            state=LoanState.APPROVED,
        )
        self.repayment = baker.make(
            LoanRepayment,
            self.loan.term,
            loan=self.loan,
            amount=self.loan.amount / 3,
            state=LoanRepaymentState.PENDING,
        )[0]
        self.repayment_data = {"amount": Decimal("3334")}
        self.url = f"/api/loans/payment/{self.repayment.id}"

    def test_successful_payment(self):
        """
        Test endpoint in case of successful payment
        """
        self.client.force_login(self.user)

        response = self.client.put(
            self.url,
            data=self.repayment_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["amount"], "3334.00")

    def test_unauthorized_payment(self):
        """
        Test payment for a loan by a differnt user.
        Should return 403
        """

        user2 = baker.make(User)
        self.client.force_login(user=user2)

        response = self.client.put(
            self.url, data=self.repayment_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["message"], "Authorization Error!")

    def test_invalid_payment(self):
        """
        Test endpoint by paying an invalid amount as repayment
        """
        self.client.force_login(user=self.user)
        self.repayment_data["amount"] = Decimal("1000000")
        response = self.client.put(
            self.url, data=self.repayment_data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Amount Paid is more than Loan amount",
            response.json()["message"],
        )
