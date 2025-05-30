from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

# Create your models here.


# Custom User with role
class User(AbstractUser):
    ROLE_CHOICES = (
        ('recipient', 'Donation Recipient'),
        ('donor', 'Donor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)

    is_approved = models.BooleanField(default=False)   # Admin Status
    is_banned = models.BooleanField(default=False)     # Ban Status

    priority = models.PositiveIntegerField(default=0)  # Higher number = higher priority (only relevant for admins)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_qualified_admin(self):
        return self.role == 'admin' and self.is_approved and not self.is_banned


# Blood Group Table
class Blood(models.Model):
    blood_group = models.CharField(max_length=10)

    def __str__(self):
        return self.blood_group

# Donor Table
class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    dob = models.DateField()
    address = models.TextField()
    gender = models.CharField(max_length=10)
    avail_to_donate = models.BooleanField(default=True)
    donate_number = models.IntegerField(default=0)
    health_condition = models.TextField()
    blood = models.ForeignKey(Blood, on_delete=models.CASCADE)
    last_donated = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    def can_donate(self):
        if not self.last_donated:
            return True
        return timezone.now().date() >= self.last_donated + timedelta(days=90)
    
    
class Recipient(models.Model):
    RECIPIENT_TYPE_CHOICES = [
        ('self', 'Self'),
        ('relative', 'Relative'),
        ('helper', 'Helper'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    dob = models.DateField()
    address = models.TextField()
    gender = models.CharField(max_length=10)
    recipient_type = models.CharField(
        max_length=10,
        choices=RECIPIENT_TYPE_CHOICES,
        default='self',
        help_text="Identify who is filling the request"
    )
    medical_condition = models.TextField(blank=True, null=True)
    blood = models.ForeignKey(Blood, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

# Blood Request Table
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('fulfilled', 'Fulfilled'),
    ('cancelled', 'Cancelled'),
    ('emergency', 'Emergency'),  # ✅ New status added
]

class BloodRequest(models.Model):
    requester = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blood_requests'
    )
    r_email = models.EmailField()
    r_phone = models.CharField(max_length=15)
    r_address = models.TextField()
    r_gender = models.CharField(max_length=10)
    r_age = models.IntegerField()
    r_qty = models.PositiveIntegerField()
    r_sickness = models.TextField()
    patient_name = models.CharField(max_length=100)
    blood_need_when = models.DateTimeField()
    blood = models.ForeignKey('Blood', on_delete=models.CASCADE)

    donor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donated_requests'
    )

    donated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fulfilled_requests'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_blood_requests'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"Request for {self.patient_name} - {self.blood}"

    def is_visible_to(self, user):
        if user.is_superuser:
            return True
        if self.requester == user:
            return True
        if self.donor == user:
            return True
        return False


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipient_notifications")
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="donor_info")  # Optional
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_request = models.ForeignKey(BloodRequest, on_delete=models.SET_NULL, null=True, blank=True)

    def get_donor_profile_url(self):
        if self.donor:
            return reverse('requested_donor_profile', args=[self.donor.id])
        return "#"