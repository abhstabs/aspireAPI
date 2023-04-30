class LoanError(Exception):
    """
    Exception class for Loan Related Errors
    """

    pass


class LoanNotApprovedError(LoanError):
    """
    Exception in case trying to do operations a loan that is not approved
    """

    pass


class LoanRepaymentComplete(LoanError):
    """
    Exception in case of trying to pay already paid installment/Repayment
    """

    pass


class PaymentPendingError(LoanError):
    """
    Exception if trying to skip a payment while repaying
    """

    pass
