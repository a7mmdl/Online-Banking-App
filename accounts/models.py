from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


        
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    account_type = models.CharField(max_length=20)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    account_number = models.CharField(max_length=20)  

    def __str__(self):
        return self.user.username
    



class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
       formatted_timestamp = self.timestamp.strftime('%Y-%m-%d %I:%M %p')
       return f"{self.user.username} - {self.amount} ({self.transaction_type}) at {formatted_timestamp}"



class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'is_staff': False})
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    send_to_all = models.BooleanField(default=False)

    def __str__(self):
        if self.send_to_all:
            return f"Notification sent to all users at {self.created_at}"
        else:
            return f"Notification sent to {self.user.username} at {self.created_at}"

    def save(self, *args, **kwargs):
        if self.send_to_all:
            # Exclude admin user from the list
            all_users = User.objects.exclude(is_staff=True)
            for user in all_users:
                Notification.objects.create(user=user, message=self.message)
        else:
            super(Notification, self).save(*args, **kwargs)



class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.description


class DailyTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transfer_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # New field for transfer limit

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.total_amount}"

    



class AdminMessage(models.Model):
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        local_time = timezone.localtime(self.created_at)
        formatted_time = local_time.strftime("%Y-%m-%d %I:%M %p")

        return f"Email: {self.email}, Message: {self.message[:50]}, Created At: {formatted_time}"




class IssueLoan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_loan_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.user.username}, Loan Amount: {self.loan_amount}, Approved: {self.approved}, Created At: {self.created_at}"




class CreditCardRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    email = models.EmailField()
    dob = models.DateField()
    phone = models.CharField(max_length=20)
    card_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Credit Card Request"


class DebitCardRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    email = models.EmailField()
    dob = models.DateField()
    phone = models.CharField(max_length=20)
    card_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Debit Card Request"
    


class PrepaidCardRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    email = models.EmailField()
    dob = models.DateField()
    phone = models.CharField(max_length=20)
    card_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Prepaid Card Request"

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    



class Installment(models.Model):
    loan = models.ForeignKey(IssueLoan, on_delete=models.CASCADE)
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    selected = models.BooleanField(default=False)
    installment_date = models.DateField(null=True)  # Add this field

    def save(self, *args, **kwargs):
        if not self.installment_date:
            # Calculate installment date based on the current date and installment number
            current_date = timezone.now().date()
            self.installment_date = current_date + timedelta(days=30 * (self.installment_number - 1))
        super().save(*args, **kwargs)
    


class HealthInsuranceIssuance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    number_of_people = models.PositiveIntegerField()
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.user.username}"
    



class CarInsuranceIssuance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    number_of_car = models.PositiveIntegerField()
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.user.username}"
    

class BusinessInsuranceIssuance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.user.username}"
    


class TravelInsuranceIssuance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    number_of_travellers = models.PositiveIntegerField()
    date_issued = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.user.username}"