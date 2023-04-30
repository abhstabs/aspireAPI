from django.contrib import admin

from .models import LoanApplication, LoanRepayment

admin.site.register(LoanApplication)
admin.site.register(LoanRepayment)
