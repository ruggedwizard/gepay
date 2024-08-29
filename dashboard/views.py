from django.shortcuts import render, redirect, get_object_or_404
from .models import AccountBalance, Transaction, Profile
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.http import HttpResponseServerError
from django.urls import reverse
from decimal import Decimal
from django.template import loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from paystackapi.paystack import Paystack
import requests
from django.contrib.auth import update_session_auth_hash
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image
import io
import base64
from rave_python import Rave

PAYSTACK_SECRET_KEY = 'sk_test_a8fb8517f9853bdbbd98380f5e3b8a570e47218c'
FLUTTERWAVE_SECRET_KEY = 'FLWPUBK-6bdaa8fe4a1b2e1bfa23085593aaf650-X'
MONNIFY_API_KEY = 'MK_TEST_PUD6DN6AUB'
MONNIFY_SECRET_KEY = 'H6AHUJ54RWB92ZFS5U7HTKBQYL8408B2'



def landing(request):
    return render(request, 'landing.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/index')  # Redirect to home page after successful login
        else:
            # Handle invalid login
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')

@login_required(login_url='login')
def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password')  # Changed to password1
        password2 = request.POST.get('password2')

        # Check if all fields are filled
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return redirect('register')

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')  
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            return redirect('register')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please choose a different one.")
            return redirect('register')
        
        # Create the user if the username and email are available
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            messages.success(request, "Account registered successfully!")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('register')
    
    return render(request, 'register.html')


@login_required(login_url='login')
def index(request):
    # Retrieve or create the account balance object for the current user
    account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
    profile_picture = request.user.profile_picture.image.url if hasattr(request.user, 'profile_picture') else 'static/images/avatars/blank-profile-picture.png'
    # Call the transaction handling functions (assuming deposit and transfer are defined elsewhere)
    deposit(request)
    transfer(request)

    # Pass the balance amount to the context
    context = {
        'balance_amount': account_balance.balance_amount,
        'profile_picture': profile_picture,
    }

    # Render the index.html template with the context
    return render(request, 'index.html', context)

@login_required(login_url='login')    
def transfer(request):
    return render(request, 'transfer.html')

@login_required(login_url='login')
def recipient(request, username):
    recipient_user = get_object_or_404(User, username=username)
    current_user_balance = AccountBalance.objects.get_or_create(user=request.user)[0]

    if request.method == 'POST':
        transfer_amt = Decimal(request.POST.get('transfer', 0))
        
        # Store sender, receiver, and amount in session
        request.session['sender_username'] = request.user.username
        request.session['receiver_username'] = recipient_user.username
        request.session['amount'] = str(transfer_amt)
        
        # Redirect to pin verification page
        return redirect('verify_pin')

    context = {
        'recipient_username': recipient_user.username,
        'username': username,
        'account_balance': current_user_balance.balance_amount
    }
    return render(request, 'recipient.html', context)

@login_required(login_url='login')
def initiate_transaction(request, sender_username, receiver_username, amount):
    # Assuming sender and receiver are User instances
    sender = request.user
    receiver = User.objects.get(username=receiver_username)
    
    # Store transaction data in session
    request.session['sender_id'] = sender.id
    request.session['receiver_id'] = receiver.id
    request.session['amount'] = amount
    
    # Redirect to transaction success page
    return redirect('transaction_success')

@login_required(login_url='login')
def transaction_success(request):
    # Retrieve sender_username, receiver_username, and amount from session
    sender_username = request.session.get('sender_username')
    receiver_username = request.session.get('receiver_username')
    amount = request.session.get('amount')
    
    # Retrieve sender and receiver objects
    sender = User.objects.get(username=sender_username)
    receiver = User.objects.get(username=receiver_username)
    
    # Create transaction object
    transaction = Transaction.objects.create(sender=sender, receiver=receiver, amount=amount)
    
    # Generate receipt URL (this can be a link to a PDF file)
    receipt_url = "URL_TO_YOUR_RECEIPT_PDF_FILE"
    
    # Render template with transaction details and receipt URL
    template = loader.get_template('transaction_success.html')
    context = {
        'transaction': transaction,
        'receipt_url': receipt_url,
    }
    return HttpResponse(template.render(context, request))

@login_required(login_url='login')
def fetch_users(request):
    if request.method == 'GET' and 'username' in request.GET:
        username = request.GET.get('username')
        users = User.objects.filter(username__icontains=username).values('username')
        user_list = list(users)
        return JsonResponse(user_list, safe=False)
    else:
        users = User.objects.all()
        return render(request, 'recipient.html', {'users': users})

@login_required(login_url='login')
# def deposit(request):
#     if request.method == 'POST':
#         amount = Decimal(request.POST.get('amount', 0))
#         amount_in_kobo = int(amount * 100)

#         if amount_in_kobo >= 10000:  # 100 Naira in kobo
#             paystack_url = "https://api.paystack.co/transaction/initialize"
#             headers = {
#                 "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
#                 "Content-Type": "application/json",
#             }

#             data = {
#                 "email": "ppedwards895@gmail.com",
#                 "amount": amount_in_kobo,
#                 "callback_url": "http://127.0.0.1:8000/"  # Replace with your callback URL
#             }

#             response = requests.post(paystack_url, json=data, headers=headers)
#             print("Paystack response:", response.text)  # Print response for debugging

#             if response.status_code == 200:
#                 response_data = response.json()
#                 if response_data['status']:
#                     authorization_url = response_data['data']['authorization_url']
                    
#                     # Save the transaction with pending status
#                     Transaction.objects.create(
#                         sender=None,
#                         receiver=request.user,
#                         amount=amount,
#                         reference=response_data['data']['reference'],
#                         status='pending'
#                     )

#                     return redirect(authorization_url)
#                 else:
#                     return JsonResponse({"message": f"Paystack error: {response_data.get('message', 'Unknown error')}"}, status=500)
#             else:
#                 return JsonResponse({"message": f"Error initializing transaction on Paystack: {response.text}"}, status=response.status_code)
#         else:
#             messages.error(request, "The minimum deposit amount is N100")

#     return render(request, 'deposit.html')
def deposit(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        amount_in_naira = int(amount)  # Amount in Naira

        if amount_in_naira >= 100:  # Minimum 100 Naira
            flutterwave_url = "https://api.flutterwave.com/v3/payments"  # Standard payments endpoint
            headers = {
                "Authorization": f"Bearer {'FLWPUBK-6bdaa8fe4a1b2e1bfa23085593aaf650-X'}",
                "Content-Type": "application/json",
            }

            data = {
                "tx_ref": f"{request.user.id}-{amount_in_naira}",  # Unique transaction reference
                "amount": str(amount_in_naira),
                "currency": "NGN",
                "redirect_url": "http://127.0.0.1:8000/payment/callback/",  # Replace with your actual callback URL
                "customer": {
                    "email": request.user.email,
                    "phone_number": str(request.user.profile_picture.phone_number or ''),
                    "name": f"{request.user.first_name} {request.user.last_name}",
                },
                "customizations": {
                    "title": "Account Deposit",
                    "description": "Deposit funds into your account",
                    "logo": "https://yourdomain.com/static/logo.png",  # Replace with your actual logo URL
                }
            }

            try:
                response = requests.post(flutterwave_url, json=data, headers=headers)
                response.raise_for_status()  # Raise an HTTPError for bad responses

                response_data = response.json()
                if response_data.get('status') == 'success':
                    authorization_url = response_data['data']['link']
                    
                    # Save the transaction with a 'pending' status
                    Transaction.objects.create(
                        sender=request.user,
                        receiver=request.user,  # Assuming the user is both sender and receiver for deposit
                        amount=amount,
                        reference=response_data['data']['tx_ref'],
                        status='pending'
                    )

                    return redirect(authorization_url)
                else:
                    return JsonResponse({"message": f"Flutterwave error: {response_data.get('message', 'Unknown error')}"}, status=500)
            except requests.exceptions.RequestException as e:
                return JsonResponse({"message": f"Error initializing transaction on Flutterwave: {str(e)}"}, status=500)
        else:
            messages.error(request, "The minimum deposit amount is N100")

    return render(request, 'deposit.html')
# def deposit(request):
#     if request.method == 'POST':
#         amount = Decimal(request.POST.get('amount', 0))
#         amount_in_naira = int(amount)  # Amount in Naira

#         if amount_in_naira >= 20:  # Minimum 20 Naira as per Monnify docs
#             try:
#                 access_token = get_access_token()
#             except Exception as e:
#                 return JsonResponse({"message": f"Error generating token: {str(e)}"}, status=500)

#             monnify_url = "https://api.monnify.com/api/v1/merchant/transactions/init-transaction"
#             headers = {
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-Type": "application/json"
#             }

#             data = {
#                 "amount": amount_in_naira,
#                 "currencyCode": "NGN",
#                 "paymentReference": f"{request.user.id}-{amount_in_naira}",  # Unique transaction reference
#                 "customerName": f"{request.user.first_name} {request.user.last_name}",
#                 "customerEmail": request.user.email,
#                 "paymentDescription": "Deposit funds into your account",
#                 "redirectUrl": "http://127.0.0.1:8000/payment/callback/",  # Replace with your actual callback URL
#                 "paymentMethods": "CARD",  # You can specify the payment method if needed
#             }

#             try:
#                 response = requests.post(monnify_url, json=data, headers=headers)
#                 response.raise_for_status()  # Raise an HTTPError for bad responses
#                 response_data = response.json()
                
#                 if response_data.get('responseCode') == '00':
#                     authorization_url = response_data.get('paymentLink')  # Adjust based on actual response

#                     # Save the transaction with a 'pending' status
#                     Transaction.objects.create(
#                         sender=request.user,
#                         receiver=request.user,  # Assuming the user is both sender and receiver for deposit
#                         amount=amount,
#                         reference=response_data['paymentReference'],
#                         status='pending'
#                     )

#                     return redirect(authorization_url)
#                 else:
#                     return JsonResponse({"message": f"Monnify error: {response_data.get('responseMessage', 'Unknown error')}"}, status=500)
#             except requests.exceptions.RequestException as e:
#                 return JsonResponse({"message": f"Error initializing transaction on Monnify: {str(e)}"}, status=500)
#         else:
#             messages.error(request, "The minimum deposit amount is N20")

#     return render(request, 'deposit.html')

# def get_access_token():
#     auth_url = "https://api.monnify.com/api/v1/auth/login"
#     api_key = 'MK_TEST_PUD6DN6AUB'
#     api_secret = 'H6AHUJ54RWB92ZFS5U7HTKBQYL8408B2'
    
#     # Generate the base64-encoded credentials
#     credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
#     auth_headers = {
#         "Authorization": f"Basic {credentials}",
#         "Content-Type": "application/json"
#     }
    
#     try:
#         response = requests.post(auth_url, headers=auth_headers, json={})
#         response.raise_for_status()  # Raise an HTTPError for bad responses
#         response_data = response.json()
        
#         if response_data.get('responseCode') == '0':
#             return response_data['responseBody']['accessToken']
#         else:
#             raise Exception(f"Error generating token: {response_data.get('responseMessage')}")
#     except requests.exceptions.RequestException as e:
#         raise Exception(f"Error generating token: {str(e)}")

def payment_callback(request):
    tx_ref = request.GET.get('tx_ref')
    transaction_id = request.GET.get('transaction_id')
    status = request.GET.get('status')

    if status == 'successful':
        # Verify transaction with Flutterwave
        flutterwave_url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        }
        response = requests.get(flutterwave_url, headers=headers)
        response_data = response.json()
        
        if response_data.get('status') == 'success' and response_data['data']['status'] == 'successful':
            # Handle successful payment
            # Example: Update transaction status in the database
            transaction = Transaction.objects.get(reference=tx_ref)
            transaction.status = 'completed'
            transaction.save()
            return HttpResponse("Payment successful!")
        else:
            # Handle failed verification
            return HttpResponse("Payment verification failed.")
    else:
        # Handle other statuses
        return HttpResponse("Payment not successful.")

@login_required(login_url='login')
def verify_pin(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        
        if user is not None:
            sender_username = request.session.get('sender_username')
            receiver_username = request.session.get('receiver_username')
            amount = Decimal(request.session.get('amount', '0'))

            if sender_username and receiver_username and amount > 100:
                sender = User.objects.get(username=sender_username)
                receiver = User.objects.get(username=receiver_username)
                sender_balance = AccountBalance.objects.get(user=sender)
                receiver_balance, _ = AccountBalance.objects.get_or_create(user=receiver)

                if sender_balance.balance_amount >= amount:
                    # Deduct amount from sender's balance
                    sender_balance.balance_amount -= amount
                    sender_balance.save()

                    # Add amount to receiver's balance
                    receiver_balance.balance_amount += amount
                    receiver_balance.save()

                    # Create transaction record
                    Transaction.objects.create(
                        sender=sender,
                        receiver=receiver,
                        amount=amount,
                        status='completed'
                    )

                    return redirect('transaction_success')
                else:
                    messages.error(request, 'Insufficient balance!')
            else:
                messages.error(request, 'Session data missing or invalid!')
        else:
            messages.error(request, 'Invalid password!')

    return render(request, 'verify_pin.html')
    


@login_required(login_url='login')
def profile(request):
    user = request.user

    # Retrieve the profile picture or default image
    profile_picture = user.profile_picture.image.url if hasattr(user, 'profile_picture') and user.profile_picture.image else 'static/images/avatars/blank-profile-picture.png'

    # Retrieve phone number from the ProfilePicture model
    phone_number = getattr(user.profile_picture, 'phone_number', 'Not provided')

    context = {
        'full_name': user.username,
        'email': user.email,
        'account_balance': getattr(user.account_balance, 'balance_amount', 0),
        'profile_picture': profile_picture,
        'phone_number': phone_number
    }

    return render(request, 'profile.html', context) 

@login_required(login_url='login')
def history(request):
    try:
        if request.user.is_authenticated:
            # Retrieve or create AccountBalance for the authenticated user
            account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
            
            # Retrieve and order transaction history for the authenticated user
            transaction_history = Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-date')
            
            return render(request, 'history.html', {'account_balance': account_balance, 'created': created, 'transaction_history': transaction_history})
        else:
            return HttpResponseServerError("User is not authenticated.")
    except AccountBalance.DoesNotExist:
        return HttpResponseServerError("Account balance not found for the authenticated user.")
    except Transaction.DoesNotExist:
        return HttpResponseServerError("Transaction history not found for the authenticated user.")
    except Exception as e:
        return HttpResponseServerError("An error occurred: {}".format(str(e)))

@login_required(login_url='login')

def settings(request):
    user = request.user
    # Ensure ProfilePicture instance exists
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']

            # Validate the file type
            if not profile_picture.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                messages.error(request, 'Invalid file type. Only PNG and JPEG images are allowed.')
                return redirect('settings')

            # Validate the file size
            if profile_picture.size > 2 * 1024 * 1024:  # Limit size to 2MB
                messages.error(request, 'File size exceeds 2MB limit.')
                return redirect('settings')

            # Optional: Validate the image content
            try:
                image = Image.open(profile_picture)
                image.verify()  # Verify that it's an actual image
            except (IOError, SyntaxError) as e:
                messages.error(request, 'Invalid image file.')
                return redirect('settings')

            # Handle the valid image file
            profile.image = profile_picture
            profile.save()
            messages.success(request, 'Profile picture updated successfully.')
            return redirect('settings')

        # Handle user info update
        if 'username' in request.POST and 'email' in request.POST and 'phone_number' in request.POST:
            username = request.POST['username']
            email = request.POST['email']
            phone_number = request.POST['phone_number']

            # Update the user model fields
            user.username = username
            user.email = email
            user.save()

            # Update phone_number in ProfilePicture
            profile.phone_number = phone_number
            profile.save()

            messages.success(request, 'User info updated successfully.')
            return redirect('settings')

        # Handle password change
        if 'current_password' in request.POST and 'new_password' in request.POST:
            current_password = request.POST['current_password']
            new_password = request.POST['new_password']
            if authenticate(username=user.username, password=current_password):
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('settings')
            else:
                messages.error(request, 'Current password is incorrect.')

    # Prepare context for rendering the template
    context = {
        'profile_picture': profile.image,
    }

    return render(request, 'settings.html', context)
