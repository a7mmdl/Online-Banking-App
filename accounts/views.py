import datetime
import json
import os
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
import stripe
from .forms import WithdrawForm, DepositForm, FundTransferForm, EditUserForm
from .models import AdminMessage, Bill, BusinessInsuranceIssuance, CarInsuranceIssuance, CreditCardRequest, DailyTransfer, DebitCardRequest, HealthInsuranceIssuance, Installment, IssueLoan, Notification, PrepaidCardRequest, Subscriber, Transaction, TravelInsuranceIssuance, UserProfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db.models import Sum
from django.contrib.auth import authenticate, login  
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation
from django.db import IntegrityError
from datetime import date, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction as db_transaction
from django.utils import timezone
from django.urls import reverse
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
import logging

#stripe.api_key = "sk_test_51NDroPIh1B4tQ2x2a6dFn3y3F6AycTVM7PPX2wSg6kUaIE4U97nHWFlmSLvCtIkBqCfJSGBcSNEF8FhK7AfXYAAa00pebUdeNP"

def index(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Check if the email is already subscribed
            if not Subscriber.objects.filter(email=email).exists():
                subscriber = Subscriber(email=email)
                subscriber.save()
                messages.success(request, 'Thank you for subscribing!')
            else:
                messages.error(request, 'You are already subscribed.')
        else:
            messages.error(request, 'Please provide a valid email address.')
        return redirect('index')
    return render(request, 'index.html')



def about(request):
    return render(request, 'about.html')




def register(request):
    if request.user.is_authenticated:
        return redirect('onlinebanking') 
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        account_type = request.POST.get('account_type')
        account_number = request.POST.get('account_number')  
        password = request.POST.get('password')

        if all([first_name, last_name, username, email, phone_number, account_type, account_number, password]):
            try:
                # Checking if account number already exists
                existing_profile = UserProfile.objects.filter(account_number=account_number).exists()
                if existing_profile:
                    raise IntegrityError  # Raise IntegrityError if account number already exists

                # Creating the user instance first
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                # Now creating the associated UserProfile
                profile = UserProfile.objects.create(
                    user=user,
                    phone_number=phone_number,
                    account_type=account_type,
                    account_number=account_number,
                )
                messages.success(request, 'User created successfully. Please login.')
                return redirect('login')
            except IntegrityError:
                messages.error(request, 'Account number already exists. Please choose a different account number.')
        else:
            # Handle invalid form data here
            pass
    return render(request, 'register2.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    

def login_view(request):
    if request.user.is_authenticated:
        return redirect('onlinebanking') 
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            # If user is authenticated, log them in
            login(request, user)
            # Redirect to index page after successful login
            return redirect('onlinebanking')
        else:
            # If authentication fails, display error message
            messages.error(request, 'Invalid username or password.')

    # Render the login page template
    return render(request, 'login.html')




@login_required
def online_banking(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user)
    total_balance = UserProfile.objects.filter(user=user).aggregate(total_balance=Sum('balance'))['total_balance'] or 0
    return render(request, 'onlinebanking.html', {'transactions': transactions, 'total_balance': total_balance})




def theme(request):
    # Retrieve the theme preference from the session if available, otherwise default to False
    is_dark_theme = request.session.get('is_dark_theme', False)
    return {'is_dark_theme': is_dark_theme}

@login_required
def fund_transfer(request):
    recipients = UserProfile.objects.exclude(user__username='admin').exclude(user=request.user)
    if request.method == 'POST':
        if 'transfer_limit' in request.POST:
            # Handling the form submission for setting the transfer limit
            transfer_limit = request.POST.get('transfer_limit')
            try:
                transfer_limit = Decimal(transfer_limit)
                # Update or create user's daily transfer record with the new limit
                user_daily_transfer, created = DailyTransfer.objects.get_or_create(user=request.user, date=date.today())
                user_daily_transfer.transfer_limit = transfer_limit
                user_daily_transfer.save()
                # Redirect to the same page or another appropriate page after setting the limit
                return redirect('fundtransfer')
            except (ValueError, Decimal.InvalidOperation):
                messages.error(request, 'Invalid transfer limit. Please enter a valid amount.')
        else:
            # Handling the form submission for fund transfer
            amount = request.POST.get('amount')
            account_number = request.POST.get('account_number')  # Get recipient's account number
            try:
                amount = Decimal(amount)  # Convert to Decimal
                recipient_profile = UserProfile.objects.get(account_number=account_number)
                sender_profile = UserProfile.objects.get(user=request.user)

                # Check if the recipient is the sender
                if recipient_profile.user == request.user:
                    messages.error(request, "You cannot transfer funds to yourself.")
                    return redirect('fundtransfer')

                # Check if the amount exceeds the daily limit
                today = date.today()
                user_daily_transfer, created = DailyTransfer.objects.get_or_create(user=request.user, date=today)

                # Reset daily transfer limit if it's not for the current date
                if user_daily_transfer.date != today:
                    user_daily_transfer.total_amount = 0
                    user_daily_transfer.save()

                if user_daily_transfer.transfer_limit and user_daily_transfer.total_amount + amount > user_daily_transfer.transfer_limit:
                    remaining_limit = user_daily_transfer.transfer_limit - user_daily_transfer.total_amount
                    messages.error(request, f"Transfer amount exceeds your daily limit. Your remaining transfer limit for the day is {remaining_limit} AED.")
                elif amount > sender_profile.balance:
                    messages.error(request, 'Insufficient balance. Please enter the correct amount to transfer.')
                else:
                    # Proceed with the transfer
                    sender_profile.balance -= amount
                    sender_profile.save()
                    Transaction.objects.create(user=request.user, amount=-amount, transaction_type=f'Transfer to {recipient_profile.user.first_name} {recipient_profile.user.last_name}')
                    recipient_profile.balance += amount
                    recipient_profile.save()
                    Transaction.objects.create(user=recipient_profile.user, amount=amount, transaction_type=f'Transfer from {request.user.first_name} {request.user.last_name}')

                    # Update daily transfer record
                    user_daily_transfer.total_amount += amount
                    user_daily_transfer.save()

                    return redirect('onlinebanking')
            except (ValueError, UserProfile.DoesNotExist):
                messages.error(request, 'Invalid amount or recipient. Please enter valid data.')
    # Retrieve transfer limit for the logged-in user
    user_transfer_limit = None
    if request.user.is_authenticated:
        try:
            user_transfer_limit = DailyTransfer.objects.get(user=request.user, date=date.today()).transfer_limit
        except ObjectDoesNotExist:
            pass  # Handle the case when DailyTransfer object does not exist for the user

    return render(request, 'fundtransfer.html', {'recipients': recipients, 'user_transfer_limit': user_transfer_limit})


def check_account(request):
    account_number = request.GET.get('account_number')
    try:
        user_profile = UserProfile.objects.get(account_number=account_number)
        full_name = f"{user_profile.user.first_name} {user_profile.user.last_name}"
        return JsonResponse({'exists': True, 'full_name': full_name})
    except UserProfile.DoesNotExist:
        return JsonResponse({'exists': False})



def delete_transaction(request, transaction_id):
    # Retrieve the transaction object
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Delete the transaction
    transaction.delete()
    
    # Redirect to the transaction list page or any other appropriate page
    return redirect('onlinebanking')



def withdraw(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount > Decimal('0'):  # Ensure the amount is positive
                account = UserProfile.objects.get(user=request.user)
                if amount <= account.balance:
                    account.balance -= amount
                    account.save()
                    Transaction.objects.create(user=request.user, amount=-amount, transaction_type='Withdraw')  # Store amount as negative
                    return redirect('onlinebanking')
                else:
                    # Display an error message if the withdrawal amount is greater than the account balance
                    messages.error(request, 'Insufficient balance. Please enter a valid amount to withdraw.')
            else:
                # Display an error message if the withdrawal amount is not positive
                messages.error(request, 'Please enter a valid amount.')
        except Decimal.InvalidOperation:
            # Display an error message if the amount is not a valid Decimal
            messages.error(request, 'Please enter a valid amount.')
    return render(request, 'withdraw.html')


def deposit(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount > Decimal('0'):  # Ensure the amount is positive
                account = UserProfile.objects.get(user=request.user)
                account.balance += amount  # Add the amount to the balance
                account.save()
                Transaction.objects.create(user=request.user, amount=amount, transaction_type='Deposit')
                return redirect('onlinebanking')
            else:
                # Display an error message if the deposit amount is not positive
                messages.error(request, 'Please enter a valid amount.')
        except Decimal.InvalidOperation:
            # Display an error message if the amount is not a valid Decimal
            messages.error(request, 'Please enter a valid amount.')
    return render(request, 'deposit.html')

@login_required
def bill_payment(request):
    if request.method == 'POST':
        bill_id = request.POST.get('bill_id')
        user_profile = UserProfile.objects.get(user=request.user)
        bill = Bill.objects.filter(id=bill_id, user=request.user).first()  # Filter bills for the current user
        
        if bill:
            if user_profile.balance >= bill.price:
                user_profile.balance -= bill.price
                user_profile.save()
                
                Transaction.objects.create(user=request.user, amount=-bill.price, transaction_type='Bill Payment')
                
                messages.success(request, f"Successfully paid {bill.description} bill.")
                
                # Delete the bill object after successful payment
                bill.delete()
            else:
                messages.error(request, "Insufficient balance. Please recharge your account.")
        else:
            messages.error(request, "You are not authorized to pay this bill or it does not exist.")
            
    user_profile = UserProfile.objects.get(user=request.user)
    bills = Bill.objects.filter(user=request.user)  # Filter bills for the current user
    context = {'user_profile': user_profile, 'bills': bills}
    return render(request, 'billpayment.html', context)


def chatbot_page(request):
    return render(request, 'chatbot.html')



@login_required
def transaction_data(request):
    # Fetch transaction data for the authenticated user
    transactions = Transaction.objects.filter(user=request.user)

    # Construct data in a format suitable for the chart
    data = []
    for transaction in transactions:
        data.append({
            'timestamp': transaction.timestamp.strftime('%Y-%m-%d'),  # Format timestamp as needed
            'amount': float(transaction.amount),  # Convert amount to float
        })

    # Return data as JSON response
    return JsonResponse(data, safe=False)


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('onlinebanking')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Email does not exist in our system.')
            return redirect('forgot_password')

        # Generate token for password reset
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(str(user.pk).encode())

        reset_link = f"http://127.0.0.1:8000/reset-password/{uidb64}/{token}/"

        # Send reset email
        send_mail(
            'Password Reset',
            f'Click the link to reset your password: {reset_link} If you haven''t requested this, please ignore this email',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        messages.success(request, 'Password reset link sent to your email.')
        return redirect('login')  # You can change this to any other URL you want

    return render(request, 'forgetpassword.html')

def reset_password(request, uidb64, token):
    UserModel = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password successfully changed.')
                return redirect('login')  # Redirect to login page with success message
            else:
                messages.error(request, 'Old password is incorrect.')
                return redirect('reset_password', uidb64=uidb64, token=token)

        return render(request, 'reset_password.html')
    else:
        messages.error(request, 'Invalid password reset link.')
        return redirect('login')


def contact_us(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        message_text = request.POST.get('message')
        AdminMessage.objects.create(email=email, message=message_text)
        
        # Add a success message
        messages.success(request, 'Your message has been successfully delivered. We will contact you shortly.')
        
        # Redirect to the same contact page
        return redirect('contact_us')  
    return render(request, 'contactus.html')






@login_required
def request_loan(request):
    # Define the maximum loan amount
    MAX_LOAN_AMOUNT = Decimal('1000000')  # 1 million
    MIN_LOAN_AMOUNT = Decimal('2000')

    if request.method == 'POST':
        # Check if user already has 3 loans
        user = request.user
        num_existing_loans = IssueLoan.objects.filter(user=user).count()
        if num_existing_loans >= 3:
            messages.error(request, "You already have 3 active loans. Please repay previous loans to be able to issue a new one.")
            return render(request, 'request_loan.html')

        loan_amount_str = request.POST.get('amount')
        if not loan_amount_str:
            return render(request, 'request_loan.html', {'error': 'Loan amount is required'})
        
        try:
            loan_amount = Decimal(loan_amount_str)
            if loan_amount < MIN_LOAN_AMOUNT:
                messages.error(request, "Minimum loan amount is 2000 AED.")
                return render(request, 'request_loan.html')
        except InvalidOperation:
            return render(request, 'request_loan.html', {'error': 'Invalid loan amount'})

        # Check if the loan amount exceeds the maximum allowable amount
        if loan_amount > MAX_LOAN_AMOUNT:
            messages.error(request, "Loan amount cannot exceed 1 million AED.")
            return render(request, 'request_loan.html')

        user_profile, created = UserProfile.objects.get_or_create(user=user)
        user_profile.balance += loan_amount
        user_profile.save()
        
        # Set created_at field to current time
        created_at = timezone.now()
        
        # Create a single IssueLoan object with associated user, loan amount, and created_at time
        new_loan = IssueLoan.objects.create(user=user, loan_amount=loan_amount, created_at=created_at)
        
        # Add loan_amount to original_loan_amount
        new_loan.original_loan_amount = loan_amount
        new_loan.save()
        
        # Create a single transaction record for the total loan amount
        Transaction.objects.create(user=user, amount=loan_amount, transaction_type='Loan Received')
        
        return redirect('view_loans')

    return render(request, 'request_loan.html')

@login_required
def view_loans(request):
    # Fetch IssueLoan objects for the logged-in user
    loans = IssueLoan.objects.filter(user=request.user)
    
    # If no loans found, display a message
    if not loans:
        return render(request, 'view_loans.html')
    
    current_time = timezone.now()
    for loan in loans:
        # Calculate the time difference between the current time and the loan creation time
        time_difference = current_time - loan.created_at
        
        # If the loan was created within the last 30 seconds, set a flag to show the delete button
        loan.show_delete_button = time_difference.total_seconds() <= 30
        
        # Check if interest has already been calculated for this loan
        if not loan.interest_amount:
            # Calculate and store interest only if it hasn't been calculated yet
            if loan.loan_amount >= loan.original_loan_amount:
                loan.interest_amount = Decimal('0.05') * loan.loan_amount
                loan.save()  # Save the loan with the calculated interest
                
                # Add the calculated interest to the loan amount
                loan.loan_amount += loan.interest_amount
                loan.save()  # Save the loan with updated loan amount
            
        # Check if the loan amount has been reduced (indicating a payment)
        if loan.original_loan_amount and loan.loan_amount < loan.original_loan_amount:
            # Set the interest amount to 0 since a payment has been made
            loan.interest_amount = Decimal(0)
            loan.save()
    
    if request.method == 'POST':
        # Handle loan deletion
        loan_id = request.POST.get('loan_id') 
        try:
            # Get the loan record to be deleted
            loan = IssueLoan.objects.get(id=loan_id)
            
            # Check if payment has been made (loan amount reduced)
            if loan.original_loan_amount and loan.loan_amount < loan.original_loan_amount:
                # If payment has been made, display an error message
                messages.error(request, "Payment has already been processed. The loan cannot be canceled.")
                return redirect('view_loans')

            # Deduct only the principal loan amount from the account balance
            user_profile = loan.user.userprofile
            loan_amount = loan.original_loan_amount if loan.original_loan_amount else loan.loan_amount
            user_profile.balance -= loan_amount
            user_profile.save()
            
            # Create a transaction record for the loan cancellation
            Transaction.objects.create(user=request.user, amount=-loan_amount, transaction_type='Loan cancelled')
            
            # Delete the transaction record for the loan request
            Transaction.objects.filter(user=request.user, amount=loan_amount, transaction_type='Loan Received').delete()
            
            # Delete the loan record
            loan.delete()
            
            messages.success(request, f"Loan of {loan_amount} AED deleted successfully.")
            return redirect('view_loans')
        except IssueLoan.DoesNotExist:
            messages.error(request, "Loan record does not exist.")
            return redirect('view_loans')

    return render(request, 'view_loans.html', {'loans': loans})



def pay_loan(request):
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')
        loan = IssueLoan.objects.get(id=loan_id)
        loan_amount = loan.loan_amount
        interest_amount = loan.interest_amount

        # Get the payment amount filled by the customer
        payment_amount_str = request.POST.get('payment_amount')
        try:
            payment_amount = Decimal(payment_amount_str)
        except ValueError:
            messages.error(request, "Invalid payment amount.")
            return redirect('view_loans')

        # Check if the payment amount is less than the minimum
        if payment_amount < Decimal('2'):
            messages.error(request, "Minimum installment amount that can be paid is 2 AED.")
            return redirect('view_loans')

        # Retrieve the user's profile to get the latest balance
        user_profile = UserProfile.objects.get(user=request.user)

        # Check if the account balance is sufficient for the payment amount
        if user_profile.balance < payment_amount:
            messages.error(request, "Insufficient funds to repay the loan.")
            return redirect('view_loans')

        # Calculate interest (5% of the loan amount)
        interest = Decimal(loan_amount) * Decimal('0.05')

        # Check if the payment amount exceeds the total amount
        if payment_amount > loan_amount:
            messages.error(request, "Payment amount exceeds the total amount.")
            return redirect('view_loans')

        # Check if the payment amount is equal to the interest amount
        if payment_amount == interest_amount:
            messages.error(request, "Please enter amount greater than the interest amount, it cannot be equal.")
            return redirect('view_loans')

        # Check if the payment amount is less than the interest amount
        if payment_amount < interest_amount:
            messages.error(request, "Payment amount should be greater than the calculated interest amount.")
            return redirect('view_loans')

        # Set up Stripe API
        stripe.api_key = os.environ.get('STRIPE_API_KEY')

        # Create a Stripe Checkout session with the payment amount
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Loan repayment',
                    },
                    'unit_amount': int(payment_amount * 100),  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success')) + f'?loan_id={loan_id}&paid_amount={payment_amount}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled')),
        )

        # Redirect to Stripe Checkout page
        return redirect(session.url)

    return redirect('view_loans')



def payment_success(request):
    logger = logging.getLogger(__name__)

    # Get loan ID and paid amount from the query parameters
    loan_id = request.GET.get('loan_id')
    paid_amount = request.GET.get('paid_amount')  # assuming this is passed from the success URL

    if loan_id and paid_amount:
        try:
            # Get the loan object
            loan = IssueLoan.objects.get(id=loan_id)
            loan_amount = loan.loan_amount
            interest_amount = loan.interest_amount

            # Convert paid amount to Decimal
            paid_amount_decimal = Decimal(paid_amount)

            # Check if payment exceeds the loan amount
            if paid_amount_decimal > loan_amount:
                messages.warning(request, "Paid amount exceeds the loan amount.")
                return redirect('view_loans')

            # Deduct payment amount from the loan amount and the interest amount
            loan.loan_amount -= paid_amount_decimal
            loan.interest_amount -= paid_amount_decimal
            loan.save()

            # Deduct the paid amount from the user's account balance
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.balance -= paid_amount_decimal
            user_profile.save()

            # Check if the paid amount fully covers the interest
            if paid_amount_decimal >= interest_amount:
                # Update the loan object with the new loan amount
                remaining_loan_amount = loan_amount - paid_amount_decimal
                if remaining_loan_amount <= 0:
                    # Delete the loan first before showing the message
                    loan.delete()
                    Transaction.objects.create(user=request.user, amount=-paid_amount_decimal, transaction_type='Loan Fully Repaid')
                    messages.success(request, "Loan fully repaid.")
                    return redirect('view_loans')
                    
                # Update the loan amount
                loan.loan_amount = remaining_loan_amount
                loan.save()

                # Set the interest amount to 0 since payment is done
                loan.interest_amount = Decimal(0)
                loan.save()

                # Check if the remaining loan amount is less than or equal to 1, and delete the loan
                int_remaining_loan_amount = int(remaining_loan_amount)
                if int_remaining_loan_amount <= 1:
                    loan.delete()
                    messages.success(request, "Loan fully repaid.")
                    Transaction.objects.create(user=request.user, amount=-paid_amount_decimal, transaction_type='Loan Fully Repaid')
                    return redirect('view_loans')

                # If remaining amount is greater than 1, displaying success message
                messages.success(request, f"Successfully paid {paid_amount} AED. Remaining loan amount: {remaining_loan_amount} AED.")
                Transaction.objects.create(user=request.user, amount=-paid_amount_decimal, transaction_type='Loan Repayment')
                return redirect('view_loans')

        except IssueLoan.DoesNotExist:
            logger.error(f"IssueLoan object with ID {loan_id} does not exist.")
            messages.error(request, "Failed to process loan repayment.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            messages.error(request, "Failed to process loan repayment.")
    else:
        messages.error(request, "Failed to process loan repayment.")

    return redirect('view_loans')





def payment_cancelled(request):
    messages.warning(request, "Payment cancelled.")
    return redirect('view_loans')






@login_required
def pay_with_installments(request, loan_id):
    try:
        loan = IssueLoan.objects.get(id=loan_id)
        total_repayment_amount = loan.loan_amount + loan.interest_amount
        
        # Check if any installment is already selected
        if Installment.objects.filter(loan=loan, selected=True).exists():
            # If installment is already selected, fetch existing installments
            installments = Installment.objects.filter(loan=loan)
            
            # Check if the loan amount has changed since installment creation
            if installments.exists() and loan.loan_amount != sum(installment.amount for installment in installments):
                # Recalculate installment amounts based on the new loan amount
                new_installment_amount = loan.loan_amount / len(installments)
                for installment in installments:
                    installment.amount = new_installment_amount
                    installment.save()
                
            return render(request, 'pay_with_installments.html', {'loan': loan, 'total_repayment_amount': total_repayment_amount, 'installments': installments})
        else:
            if request.method == 'POST':
                installment_count = int(request.POST.get('installment_count'))
                if installment_count < 2 or installment_count > 12:
                    messages.error(request, "Please select a valid number of installments between 2 and 12.")
                    return redirect('pay_with_installments', loan_id=loan_id)
                
                # Calculate installment amount
                installment_amount = loan.loan_amount / installment_count
                
                # Check if installment amount is at least 2
                if installment_amount < 2:
                    messages.error(request, "Installments cannot be paid for amounts below 2.")
                    return redirect('pay_with_installments', loan_id=loan_id)
                
                # Round down to avoid rounding errors causing total to exceed loan amount
                installment_amount = installment_amount.quantize(Decimal('.01'), rounding=ROUND_DOWN)

                # Calculate remaining amount after evenly distributing among installments
                remaining_amount = loan.loan_amount - (installment_amount * installment_count)

                # Adjust last installment amount to account for remaining amount
                last_installment_amount = installment_amount + remaining_amount

                # Create installment objects
                for i in range(1, installment_count):
                    Installment.objects.create(loan=loan, installment_number=i, amount=installment_amount, selected=True)

                # Create last installment with adjusted amount
                Installment.objects.create(loan=loan, installment_number=installment_count, amount=last_installment_amount, selected=True)

                # Redirect to the same page to display installment options
                return redirect('pay_with_installments', loan_id=loan_id)

            return render(request, 'pay_with_installments.html', {'loan': loan, 'total_repayment_amount': total_repayment_amount, 'installment_count_options': range(2, 13)})

    except IssueLoan.DoesNotExist:
        messages.error(request, "Loan record does not exist.")
        return redirect('view_loans')

@login_required
def pay_installment(request, loan_id):
    if request.method == 'POST':
        try:
            loan = IssueLoan.objects.get(id=loan_id)
            installment_id = request.POST.get('installment_id')
            installment = Installment.objects.get(id=installment_id)
            
            # Existing payment logic
            payment_amount_str = request.POST.get('installment_amount')
            try:
                payment_amount = Decimal(payment_amount_str)
            except ValueError:
                messages.error(request, "Invalid payment amount.")
                return redirect('view_loans')

            if payment_amount < Decimal('2'):
                messages.error(request, "Minimum installment amount that can be paid is 2 AED.")
                return redirect('view_loans')

            user_profile = UserProfile.objects.get(user=request.user)

            if user_profile.balance < payment_amount:
                messages.error(request, "Insufficient funds to repay the installment.")
                return redirect('view_loans')

            if payment_amount > loan.loan_amount:
                messages.error(request, "Payment amount exceeds the total amount.")
                return redirect('view_loans')

            if payment_amount == loan.interest_amount:
                messages.error(request, "Please enter an amount greater or lesser than the interest amount.")
                return redirect('view_loans')

            stripe.api_key = os.environ.get('STRIPE_API_KEY')

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'aed',
                        'product_data': {
                            'name': 'Installment repayment',
                        },
                        'unit_amount': int(payment_amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('payment_installment_success')) + f'?loan_id={loan_id}&paid_amount={payment_amount}',
                cancel_url=request.build_absolute_uri(reverse('payment_installment_cancelled')),
            )

            # Redirect to the Stripe payment page
            return redirect(session.url)

        except (IssueLoan.DoesNotExist, Installment.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, "Loan record, installment, or user profile does not exist.")
            return redirect('view_loans')

    return redirect('view_loans')


@login_required
def payment_installment_success(request):
    if request.method == 'GET':
        loan_id = request.GET.get('loan_id')
        paid_amount = Decimal(request.GET.get('paid_amount', 0))

        try:
            # Get the loan object
            loan = IssueLoan.objects.get(id=loan_id)
            user_profile = UserProfile.objects.get(user=request.user)

            # Find the installment corresponding to the paid amount
            installment = Installment.objects.filter(loan=loan, amount=paid_amount, paid=False).first()

            if installment:
                # Mark the installment as paid and delete it
                installment.paid = True
                installment.delete()

                # Deduct the paid amount from the user's account balance and loan amount
                user_profile.balance -= paid_amount
                loan.loan_amount -= paid_amount
                user_profile.save()
                loan.save()

                # Create a transaction object for the installment payment
                Transaction.objects.create(user=request.user, amount=-paid_amount, transaction_type='Installment Successful')
                messages.success(request, f"Installment of {paid_amount} AED paid successfully.")

                # If the loan amount is 1 or less, delete the loan
                if loan.loan_amount <= Decimal('1'):
                    loan.delete()
                    messages.success(request, "Loan fully repaid.")

                # Redirect back to the 'pay_with_installments' page
                return redirect('pay_with_installments', loan_id=loan_id)

            else:
                messages.error(request, "No corresponding installment found for the paid amount.")
                # Redirect back to the 'pay_with_installments' page
                return redirect('pay_with_installments', loan_id=loan_id)

        except IssueLoan.DoesNotExist:
            messages.error(request, "Loan record does not exist.")

    messages.error(request, "Invalid request.")
    return redirect('view_loans')


@login_required
def payment_installment_cancelled(request):
    messages.warning(request, "Installment payment cancelled.")
    return redirect('view_loans')



def filter_transactions(request):
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')
    
    if start_date_str and end_date_str:
        start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str, "%m/%d/%Y"))
        end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str, "%m/%d/%Y"))
        # Filter transactions for the logged-in user
        transactions = Transaction.objects.filter(user=request.user, timestamp__range=[start_date, end_date])
    else:
        transactions = []
    
    return render(request, 'onlinebanking.html', {'transactions': transactions, 'start_date': start_date_str, 'end_date': end_date_str})




@login_required
def download_transaction_history_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transaction_history.pdf"'

    transactions = Transaction.objects.filter(user=request.user)
    user_profile = UserProfile.objects.get(user=request.user)
    total_balance = user_profile.balance

    # Create a PDF document
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Define the table data and style
    data = [['Transaction Type', 'Amount', 'Date']]
    for transaction in transactions:
        data.append([transaction.transaction_type, str(transaction.amount), transaction.timestamp.strftime('%b %d, %Y %I:%M %p')])
    data.append(['Total Balance:', '', str(total_balance)])  # Add total balance as summary

    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    # Add table to elements
    elements.append(table)

    # Build PDF
    doc.build(elements)
    return response

def issue_cards(request):
    return render(request, 'issuecards.html')



@login_required
def issue_credit_card(request):
    user = request.user
    
    if request.method == 'POST':
        # Check if the credit card application already exists for the logged-in user
        if CreditCardRequest.objects.filter(user=user).exists():
            messages.error(request, "An application for a credit card already exists in our system.")
            return redirect('issue_credit_card')  # Redirect to the same page
        
        firstname = request.POST.get('firstname')
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        phone = request.POST.get('phone')
        card_type = request.POST.get('card_type')

        # Store form data in cache
        request.session['credit_card_data'] = {
            'firstname': firstname,
            'email': email,
            'dob': dob,
            'phone': phone,
            'card_type': card_type
        }
        
        # Check if the user's account balance is sufficient for the payment
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.balance < 200:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_credit_card')  # Redirect to the same page
        
        # Process payment only if the user has sufficient balance
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Credit Card Application Fees',
                        'description': 'Credit card application fees',
                    },
                    'unit_amount': 20000,  # Amount in cents (200 AED)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_credit_card')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_credit_card')),
        )
        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)
    
    return render(request, 'issuecreditcard.html')

def payment_success_credit_card(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    if user_profile.balance < 200:
        messages.error(request, "Insufficient funds for the payment.")
    else:
        # Deduct the payment amount from the user's account balance
        user_profile.balance -= 200
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-200,
            transaction_type='Credit card application payment'
        )

        # Retrieve form data from cache
        credit_card_data = request.session.get('credit_card_data')
        if credit_card_data:
            # Create CreditCardRequest object using form data
            CreditCardRequest.objects.create(user=user, **credit_card_data)
            messages.success(request, "Your credit card is issued, card will be delieverd to you shortly")
            # Clear the stored form data from the session
            del request.session['credit_card_data']
        else:
            messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_credit_card')

@login_required
def payment_cancelled_credit_card(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_credit_card')

@login_required
def issue_debit_card(request):
    if request.method == 'POST':
        user = request.user
        # Check if a debit card application already exists for the user
        if DebitCardRequest.objects.filter(user=user).exists():
            messages.error(request, "An application for a debit card already exists in our system.")
            return redirect('issue_debit_card')  # Redirect to the same page
        
        firstname = request.POST.get('firstname')
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        phone = request.POST.get('phone')
        card_type = request.POST.get('card_type')
        
        # Create a new debit card request
        DebitCardRequest.objects.create(user=user, firstname=firstname, email=email, dob=dob, phone=phone, card_type=card_type)
        
        messages.success(request, "Your debit card is issued, card will be delieverd to you shortly")
        return redirect('issue_debit_card')  # Redirect to the same page
    
    return render(request, 'issuedebitcard.html')


@login_required
def view_credit_card_requests(request):
    # Fetch CreditCardRequest objects for the logged-in user
    credit_card_requests = CreditCardRequest.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Handle credit card request cancellation
        request_id = request.POST.get('request_id')
        try:
            # Get the credit card request record to be deleted
            credit_card_request = CreditCardRequest.objects.get(id=request_id)
            
            # Delete the credit card request record
            credit_card_request.delete()
            
            messages.success(request, "Credit card request canceled successfully.")
            return redirect('view_credit_card_requests')
        except CreditCardRequest.DoesNotExist:
            messages.error(request, "Credit card request does not exist.")
            return redirect('view_credit_card_requests')

    # Render the template with the credit card requests data
    return render(request, 'viewcreditcard.html', {'credit_card_requests': credit_card_requests})



@login_required
def view_debit_card_requests(request):
    debit_card_requests = DebitCardRequest.objects.filter(user=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        try:
            request_obj = DebitCardRequest.objects.get(id=request_id)
            
            request_obj.delete()
            
            messages.success(request, "Debit card request canceled successfully.") 
            return redirect('view_debit_card_requests')
        except DebitCardRequest.DoesNotExist:
            messages.error(request, "Debit card request does not exist.")  
            return redirect('view_debit_card_requests')

    return render(request, 'viewdebitcard.html', {'debit_card_requests': debit_card_requests})




@login_required
def issue_prepaid_card(request):
    user = request.user
    
    if request.method == 'POST':
        # Check if the credit card application already exists for the logged-in user
        if PrepaidCardRequest.objects.filter(user=user).exists():
            messages.error(request, "An application for a pre-paid card already exists in our system.")
            return redirect('issue_prepaid_card')  # Redirect to the same page
        
        firstname = request.POST.get('firstname')
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        phone = request.POST.get('phone')
        card_type = request.POST.get('card_type')

        # Store form data in cache
        request.session['prepaid_card_data'] = {
            'firstname': firstname,
            'email': email,
            'dob': dob,
            'phone': phone,
            'card_type': card_type
        }
        
        # Check if the user's account balance is sufficient for the payment
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.balance < 100:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_prepaid_card')  # Redirect to the same page
        
        # Process payment only if the user has sufficient balance
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Prepaid Card Application Fees',
                        'description': 'Credit card application fees',
                    },
                    'unit_amount': 10000,  # Amount in cents (100 AED)
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_prepaid_card')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_prepaid_card')),
        )
        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)
    
    return render(request, 'issueprepaidcard.html')


def payment_success_prepaid_card(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    if user_profile.balance < 100:
        messages.error(request, "Insufficient funds for the payment.")
    else:
        # Deduct the payment amount from the user's account balance
        user_profile.balance -= 100
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-100,
            transaction_type='Prepaid card application payment'
        )

        # Retrieve form data from cache
        prepaid_card_data = request.session.get('prepaid_card_data')
        if prepaid_card_data:
            # Create CreditCardRequest object using form data
            PrepaidCardRequest.objects.create(user=user, **prepaid_card_data)
            messages.success(request, "Your pre-paid card is issued, card will be delieverd to you shortly")
            # Clear the stored form data from the session
            del request.session['prepaid_card_data']
        else:
            messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_prepaid_card')

def payment_cancelled_prepaid_card(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_prepaid_card')

@login_required
def view_prepaid_card_requests(request):
    # Fetch PrepaidCardRequest objects for the logged-in user
    prepaid_card_requests = PrepaidCardRequest.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Handle prepaid card request cancellation
        request_id = request.POST.get('request_id')
        try:
            # Get the prepdaid card request record to be deleted
            prepaid_card_request = PrepaidCardRequest.objects.get(id=request_id)
            
            # Delete the prepaid card request record
            prepaid_card_request.delete()
            
            messages.success(request, "Prepaid card request canceled successfully.")
            return redirect('view_prepaid_card_requests')
        except CreditCardRequest.DoesNotExist:
            messages.error(request, "Prepaid card request does not exist.")
            return redirect('view_prepaid_card_requests')

    # Render the template with the prepaid card requests data
    return render(request, 'viewprepaidcard.html', {'prepaid_card_requests': prepaid_card_requests})


@login_required
def update_user(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        # Extract form data from request.POST dictionary
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        account_type = request.POST.get('account_type')

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update user profile details
        user_profile.phone_number = phone_number
        user_profile.account_type = account_type
        user_profile.save()

        messages.success(request, 'Your profile has been updated successfully.')
        return redirect('update_user')  # Redirect to profile page after successful update
    
    context = {
        'user': user,
        'user_profile': user_profile,
    }
    
    return render(request, 'userupdate.html', context)

def deactivate_account(request):
    if request.method == 'POST':
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        
        # Delete user and profile
        user_profile.delete()
        user.delete()
        logout(request)  # Logout the user
        messages.success(request, 'Your account has been deactivated successfully.')
        return redirect('login')  # Redirect to login page after deactivation
    

def currency_converter(request):
    return render(request, 'currency_converter.html')




def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.method == 'POST':
        notification.delete()
        
    # Get the referer URL from the request headers
    referer = request.META.get('HTTP_REFERER')
    
    # If referer exists and is safe, redirect back to it
    if referer and referer.startswith(request.build_absolute_uri('/')):
        return redirect(referer)
    else:
        # If referer is not safe or doesn't exist, redirect to a default URL
        return redirect(reverse('index'))


@login_required
def clear_all_notifications(request):
    if request.method == 'POST':
        # Filter notifications by the current user and delete them
        notifications = Notification.objects.filter(user=request.user)
        notifications.delete()
        # Redirect back to the referring page (or any other desired page)
        return redirect(request.META.get('HTTP_REFERER', '/'))



def issue_insurance(request):
    return render(request, 'issue_insurance.html')





@login_required
def issue_health_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if request.method == 'POST':

        user = request.user
        num_existing_health_insurance = HealthInsuranceIssuance.objects.filter(user=user).count()
        if num_existing_health_insurance >= 3:
            messages.error(request, "You already have 3 active insaurence. Please wait for expiry or cancel to re-apply.")
            return render(request, 'issue_health_insurance.html')

 
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        account_number = request.POST.get('account_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        number_of_people = int(request.POST.get('number_of_people'))  # Converting to integer
        
        # Calculate total price based on the number of people
        price_per_person = 3000  # 3000 AED per person
        total_price = price_per_person * number_of_people

        # Check if the user's account balance is sufficient for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_health_insurance')  # Redirect to the same page
        
        # Store form data in cache with the correct key 'health_insurance_data'
        request.session['health_insurance_data'] = {
        'firstname': firstname,
        'lastname': lastname,
        'account_number': account_number,
        'email': email,
        'phone': phone,
        'number_of_people': number_of_people,
        }
        
        # Process payment only if the user has sufficient balance
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Health Insurance Issuance Fees',
                        'description': 'Health insurance issuance fees',
                    },
                    'unit_amount': total_price * 100,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_health_insurance')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_health_insurance')),
        )
        

        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'issue_health_insurance.html', context)



def payment_success_health_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Retrieve form data from session
    health_insurance_data = request.session.get('health_insurance_data')

    # Check if form data exists
    if health_insurance_data:
        # Extract number of people from form data
        number_of_people = int(health_insurance_data.get('number_of_people'))
        
        # Calculate total price based on the number of people
        total_price = number_of_people * 3000

        # Check if user has sufficient balance for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_health_insurance')

        # Deduct the payment amount from the user's account balance
        user_profile.balance -= total_price
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-total_price,
            transaction_type='Health insurance issuance payment'
        )

        # Create HealthInsuranceIssuance object using form data
        HealthInsuranceIssuance.objects.create(user=user, **health_insurance_data)
        messages.success(request, "Your health insurance issuance has been applied successfully.")
        
        # Clear the stored form data from the session
        del request.session['health_insurance_data']

    else:
        messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_health_insurance')
@login_required
def payment_cancelled_health_insurance(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_health_insurance')




@login_required
def view_health_insurance_requests(request):
    # Fetch HealthInsuranceIssuance objects for the logged-in user
    health_insurance_requests = HealthInsuranceIssuance.objects.filter(user=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        try:
            # Get the health insurance request record to be deleted
            health_insurance_request = HealthInsuranceIssuance.objects.get(id=request_id)
            
            # Refund the insurance price back to the user's account balance
            refund_amount = health_insurance_request.number_of_people * 3000
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.balance += refund_amount
            user_profile.save()
            
            # Create a transaction record for the refund
            Transaction.objects.create(
                user=request.user,
                amount=refund_amount,
                transaction_type='Refund for insurance cancellation'
            )
            
            # Delete the health insurance request record
            health_insurance_request.delete()
            
            messages.success(request, "Insurance request deleted successfully. Refund processed.")
            return redirect('view_health_insurance_requests')
        except HealthInsuranceIssuance.DoesNotExist:
            messages.error(request, "Insurance request data does not exist.")
            return redirect('view_health_insurance_requests')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('view_health_insurance_requests')

    # Render the template with the health insurance requests data
    return render(request, 'viewhealthinsurance.html', {'health_insurance_requests': health_insurance_requests})



#ANOTHER BATCH ANOTHER BATCH ####





@login_required
def issue_car_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if request.method == 'POST':

        user = request.user
        num_existing_car_insurance = CarInsuranceIssuance.objects.filter(user=user).count()
        if num_existing_car_insurance >= 3:
            messages.error(request, "You already have 3 active insaurence. Please wait for expiry or cancel to re-apply.")
            return render(request, 'issue_car_insurance.html')

 
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        account_number = request.POST.get('account_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        number_of_car = int(request.POST.get('number_of_car'))  # Convert to integer
        
        # Calculate total price based on the number of car
        price_per_car = 1500  # 1500 AED per car
        total_price = price_per_car * number_of_car

        # Check if the user's account balance is sufficient for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_car_insurance')  # Redirect to the same page
        
        # Store form data in cache with the correct key 'health_insurance_data'
        request.session['car_insurance_data'] = {
        'firstname': firstname,
        'lastname': lastname,
        'account_number': account_number,
        'email': email,
        'phone': phone,
        'number_of_car': number_of_car,
        }
        
        # Process payment only if the user has sufficient balance
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Car Insurance Issuance Fees',
                        'description': 'Car insurance issuance fees',
                    },
                    'unit_amount': total_price * 100,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_car_insurance')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_car_insurance')),
        )
        

        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'issue_car_insurance.html', context)



def payment_success_car_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Retrieve form data from session
    car_insurance_data = request.session.get('car_insurance_data')

    # Check if form data exists
    if car_insurance_data:
        # Extract number of people from form data
        number_of_car = int(car_insurance_data.get('number_of_car'))
        
        # Calculate total price based on the number of people
        total_price = number_of_car * 1500

        # Check if user has sufficient balance for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_car_insurance')

        # Deduct the payment amount from the user's account balance
        user_profile.balance -= total_price
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-total_price,
            transaction_type='Car insurance issuance payment'
        )

        # Create HealthInsuranceIssuance object using form data
        CarInsuranceIssuance.objects.create(user=user, **car_insurance_data)
        messages.success(request, "Your car insurance issuance has been applied successfully.")
        
        # Clear the stored form data from the session
        del request.session['car_insurance_data']

    else:
        messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_car_insurance')
@login_required
def payment_cancelled_car_insurance(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_car_insurance')




@login_required
def view_car_insurance_requests(request):
    # Fetch HealthInsuranceIssuance objects for the logged-in user
    car_insurance_requests = CarInsuranceIssuance.objects.filter(user=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        try:
            # Get the health insurance request record to be deleted
            car_insurance_request = CarInsuranceIssuance.objects.get(id=request_id)
            
            # Refund the insurance price back to the user's account balance
            refund_amount = car_insurance_request.number_of_car * 1500
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.balance += refund_amount
            user_profile.save()
            
            # Create a transaction record for the refund
            Transaction.objects.create(
                user=request.user,
                amount=refund_amount,
                transaction_type='Refund for insurance cancellation'
            )
            
            # Delete the health insurance request record
            car_insurance_request.delete()
            
            messages.success(request, "Insurance request deleted successfully. Refund processed.")
            return redirect('view_car_insurance_requests')
        except CarInsuranceIssuance.DoesNotExist:
            messages.error(request, "Insurance request data does not exist.")
            return redirect('view_car_insurance_requests')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('view_car_insurance_requests')

    # Render the template with the health insurance requests data
    return render(request, 'viewcarinsurance.html', {'car_insurance_requests': car_insurance_requests})



#RENDER NEW VIEW VIEW #############





@login_required
def issue_business_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if request.method == 'POST':
        user = request.user
        num_existing_business_insurance = BusinessInsuranceIssuance.objects.filter(user=user).count()
        if num_existing_business_insurance >= 3:
            messages.error(request, "You already have 3 active insurances. Please wait for expiry or cancel to re-apply.")
            return render(request, 'issue_business_insurance.html')

        # Store form data in cache with the correct key 'business_insurance_data'
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        account_number = request.POST.get('account_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        # Check user's account balance
        total_price = 10000  # Assuming fixed price of 10000 AED
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_business_insurance')

        # Remove 'number_of_business' from form data
        request.session['business_insurance_data'] = {
            'firstname': firstname,
            'lastname': lastname,
            'account_number': account_number,
            'email': email,
            'phone': phone,
        }

        # Process payment
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Business Insurance Issuance Fees',
                        'description': 'Business insurance issuance fees',
                    },
                    'unit_amount': total_price * 100,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_business_insurance')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_business_insurance')),
        )
        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'issue_business_insurance.html', context)




def payment_success_business_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Retrieve form data from session
    business_insurance_data = request.session.get('business_insurance_data')

    # Check if form data exists
    if business_insurance_data:
        # Calculate total price (assuming fixed price of 10000 AED)
        total_price = 10000

        # Check if user has sufficient balance for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_business_insurance')

        # Deduct the payment amount from the user's account balance
        user_profile.balance -= total_price
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-total_price,
            transaction_type='Business insurance issuance payment'
        )

        # Create BusinessInsuranceIssuance object using form data
        BusinessInsuranceIssuance.objects.create(user=user, **business_insurance_data)
        messages.success(request, "Your business insurance issuance has been applied successfully.")
        
        # Clear the stored form data from the session
        del request.session['business_insurance_data']

    else:
        messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_business_insurance')
@login_required
def payment_cancelled_business_insurance(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_business_insurance')




@login_required
def view_business_insurance_requests(request):
    # Fetch BusinessInsuranceIssuance objects for the logged-in user
    business_insurance_requests = BusinessInsuranceIssuance.objects.filter(user=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        try:
            # Get the business insurance request record to be deleted
            business_insurance_request = BusinessInsuranceIssuance.objects.get(id=request_id)
            
            # Refund the insurance price back to the user's account balance
            refund_amount = 10000  # Assuming fixed price of 10000 AED per insurance issuance
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.balance += refund_amount
            user_profile.save()
            
            # Create a transaction record for the refund
            Transaction.objects.create(
                user=request.user,
                amount=refund_amount,
                transaction_type='Refund for insurance cancellation'
            )
            
            # Delete the business insurance request record
            business_insurance_request.delete()
            
            messages.success(request, "Insurance request deleted successfully. Refund processed.")
            return redirect('view_business_insurance_requests')
        except BusinessInsuranceIssuance.DoesNotExist:
            messages.error(request, "Insurance request data does not exist.")
            return redirect('view_business_insurance_requests')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('view_business_insurance_requests')

    # Render the template with the business insurance requests data
    return render(request, 'viewbusinessinsurance.html', {'business_insurance_requests': business_insurance_requests})



# ANOTHER BUT LAST BATCH ####





@login_required
def issue_travel_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if request.method == 'POST':

        user = request.user
        num_existing_travel_insurance = TravelInsuranceIssuance.objects.filter(user=user).count()
        if num_existing_travel_insurance >= 3:
            messages.error(request, "You already have 3 active insaurence. Please wait for expiry or cancel to re-apply.")
            return render(request, 'issue_travel_insurance.html')

 
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        account_number = request.POST.get('account_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        number_of_travellers = int(request.POST.get('number_of_travellers'))  # Convert to integer
        
        # Calculate total price based on the number of car
        price_per_travellers = 500  # 1500 AED per car
        total_price = price_per_travellers * number_of_travellers

        # Check if the user's account balance is sufficient for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_travel_insurance')  # Redirect to the same page
        
        # Store form data in cache with the correct key 'health_insurance_data'
        request.session['travel_insurance_data'] = {
        'firstname': firstname,
        'lastname': lastname,
        'account_number': account_number,
        'email': email,
        'phone': phone,
        'number_of_travellers': number_of_travellers,
        }
        
        # Process payment only if the user has sufficient balance
        stripe.api_key = os.environ.get('STRIPE_API_KEY')
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'aed',
                    'product_data': {
                        'name': 'Travel Insurance Issuance Fees',
                        'description': 'Travel insurance issuance fees',
                    },
                    'unit_amount': total_price * 100,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success_travel_insurance')) + f'?user_id={user.id}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled_travel_insurance')),
        )
        

        
        # Redirect the user to the Stripe-hosted checkout page
        return redirect(session.url)

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'issue_travel_insurance.html', context)



def payment_success_travel_insurance(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    
    # Retrieve form data from session
    travel_insurance_data = request.session.get('travel_insurance_data')

    # Check if form data exists
    if travel_insurance_data:
        # Extract number of people from form data
        number_of_travellers = int(travel_insurance_data.get('number_of_travellers'))
        
        # Calculate total price based on the number of people
        total_price = number_of_travellers * 500

        # Check if user has sufficient balance for the payment
        if user_profile.balance < total_price:
            messages.error(request, "Insufficient funds for the payment.")
            return redirect('issue_travel_insurance')

        # Deduct the payment amount from the user's account balance
        user_profile.balance -= total_price
        user_profile.save()

        # Create a transaction record for the payment
        Transaction.objects.create(
            user=user,
            amount=-total_price,
            transaction_type='Travel insurance issuance payment'
        )

        # Create HealthInsuranceIssuance object using form data
        TravelInsuranceIssuance.objects.create(user=user, **travel_insurance_data)
        messages.success(request, "Your travel insurance issuance has been applied successfully.")
        
        # Clear the stored form data from the session
        del request.session['travel_insurance_data']

    else:
        messages.error(request, "Failed to retrieve form data. Please try again.")

    return redirect('issue_travel_insurance')
@login_required
def payment_cancelled_travel_insurance(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect('issue_travel_insurance')




@login_required
def view_travel_insurance_requests(request):
    # Fetch HealthInsuranceIssuance objects for the logged-in user
    travel_insurance_requests = TravelInsuranceIssuance.objects.filter(user=request.user)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        try:
            # Get the health insurance request record to be deleted
            travel_insurance_request = TravelInsuranceIssuance.objects.get(id=request_id)
            
            # Refund the insurance price back to the user's account balance
            refund_amount = travel_insurance_request.number_of_travellers * 500
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.balance += refund_amount
            user_profile.save()
            
            # Create a transaction record for the refund
            Transaction.objects.create(
                user=request.user,
                amount=refund_amount,
                transaction_type='Refund for insurance cancellation'
            )
            
            # Delete the health insurance request record
            travel_insurance_request.delete()
            
            messages.success(request, "Insurance request deleted successfully. Refund processed.")
            return redirect('view_travel_insurance_requests')
        except TravelInsuranceIssuance.DoesNotExist:
            messages.error(request, "Insurance request data does not exist.")
            return redirect('view_travel_insurance_requests')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('view_travel_insurance_requests')

    # Rendering the template with the health insurance requests data
    return render(request, 'viewtravelinsurance.html', {'travel_insurance_requests': travel_insurance_requests})


