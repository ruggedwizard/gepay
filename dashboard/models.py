

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_picture')
    image = models.ImageField(upload_to='profile_pictures', default='static/images/avatars/blank-profile-picture.png')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

class Transaction(models.Model):
    sender = models.ForeignKey(User, related_name='sent_transactions', on_delete=models.CASCADE, null=True)
    receiver = models.ForeignKey(User, related_name='received_transactions', on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=255, default='default_reference')
    status = models.CharField(max_length=20, default='pending')
    

    def __str__(self):
        return f"Transaction from {self.sender} to {self.receiver} on {self.date}"


class AccountBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_balance')
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Account Balance of {self.user.username}"


        