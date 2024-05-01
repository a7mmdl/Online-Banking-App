from django.contrib import admin

# Register your models here.
# banking/admin.py

from django.contrib import admin
from .models import  BusinessInsuranceIssuance, CarInsuranceIssuance, DebitCardRequest, HealthInsuranceIssuance, Installment, Notification, PrepaidCardRequest, Subscriber, Transaction, TravelInsuranceIssuance, UserProfile, Bill, DailyTransfer, AdminMessage, IssueLoan, CreditCardRequest
from django.contrib.auth.admin import UserAdmin



admin.site.register(Transaction)
admin.site.register(UserProfile)
admin.site.register(Bill)
admin.site.register(DailyTransfer)
admin.site.register(AdminMessage)
admin.site.register(IssueLoan)
admin.site.register(CreditCardRequest)
admin.site.register(DebitCardRequest)
admin.site.register(PrepaidCardRequest)
admin.site.register(Subscriber)
admin.site.register(Notification)
admin.site.register(Installment)
admin.site.register(HealthInsuranceIssuance)
admin.site.register(CarInsuranceIssuance)
admin.site.register(BusinessInsuranceIssuance)
admin.site.register(TravelInsuranceIssuance)

#---admin panel customiztaion---
admin.site.site_header="Ahmed's Bank Admin Panel"
admin.site.site_title="Ahmed's Bank Admin Panel"
admin.site.index_titel="welcome to this portal"