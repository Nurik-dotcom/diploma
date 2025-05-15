from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Transaction, SuspiciousLog, User
admin.site.register(User)
admin.site.register(Transaction)
admin.site.register(SuspiciousLog)