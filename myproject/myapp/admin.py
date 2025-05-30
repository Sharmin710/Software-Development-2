from django.contrib import admin
from .models import User, Blood, Donor, Recipient, BloodRequest, Notification

# Register your models here.
admin.site.register(User)
admin.site.register(Blood)
admin.site.register(Donor)
admin.site.register(BloodRequest)
admin.site.register(Recipient)
admin.site.register(Notification)