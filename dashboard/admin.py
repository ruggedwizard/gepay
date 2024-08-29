from django.contrib import admin
from .models import AccountBalance, Transaction, Profile

# Register the AccountBalance model with the admin interface
admin.site.register(AccountBalance)
admin.site.register(Transaction)
admin.site.register(Profile)

# Register your models here.
