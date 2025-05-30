from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Donor, Notification, BloodRequest, User
from django.core.mail import send_mail
from django.conf import settings

# @receiver(post_save, sender=BloodRequest)
# def notify_matching_donors(sender, instance, created, **kwargs):
#     if not created:
#         return

#     # Get matching approved and non-banned donors
#     matching_donors = User.objects.filter(
#         role='donor',
#         is_approved=True,
#         is_banned=False,
#         blood__blood_group=instance.blood.blood_group
#     )

#     for donor in matching_donors:
#         send_mail(
#             subject='Urgent Blood Donation Request',
#             message=f"Dear {donor.username},\n\n"
#                     f"A new request has been made for blood group {instance.blood.blood_group}.\n"
#                     f"Patient: {instance.patient_name}\n"
#                     f"Required Qty: {instance.r_qty} units\n"
#                     f"Date Needed: {instance.blood_need_when.strftime('%Y-%m-%d %H:%M')}\n"
#                     f"Location: {instance.r_address}\n"
#                     f"Contact: {instance.r_email} / {instance.r_phone}\n\n"
#                     f"If you can help, please log in and accept the request.\n\nThank you!",
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[donor.email],
#             fail_silently=True,
#         )


# @receiver(post_save, sender=BloodRequest)
# def notify_donors_on_new_request(sender, instance, created, **kwargs):
#     if created:
#         matching_donors = User.objects.filter(
#             role='donor',
#             is_approved=True,
#             is_banned=False,
#             blood__blood_group=instance.blood.blood_group
#         )

#         for donor in matching_donors:
#             # Create in-app notification
#             Notification.objects.create(
#                 recipient=donor,
#                 message=f"New request for {instance.blood.blood_group} blood needed by {instance.patient_name}."
#             )


@receiver(post_save, sender=BloodRequest)
def handle_blood_request_created(sender, instance, created, **kwargs):
    if created:
        # ✅ Case 1: Notify all donors with matching blood group and availability
        matching_donors = Donor.objects.filter(
            blood=instance.blood,
            avail_to_donate=True,
            user__is_active=True  # optional filter to avoid inactive users
        )

        for donor in matching_donors:
            Notification.objects.create(
                recipient=donor.user,
                message=f"New blood request for {instance.blood.blood_group}. Please check and respond."
            )

        # ✅ Case 2: Direct donor request (if donor is assigned)
        if instance.donor:
            Notification.objects.create(
                recipient=instance.donor,
                message=f"You have been directly requested to donate blood for {instance.patient_name}."
            )

    else:
        # ✅ Case 3: Donor accepted the request (status is 'accepted' and donated_by is set)
        if instance.status == "accepted" and instance.donated_by:
            # Notify the requester (recipient)
            if instance.requester:
                Notification.objects.create(
                    recipient=instance.requester,
                    message=f"{instance.donated_by.username} has accepted your blood request for {instance.patient_name}."
                )

            # Optional confirmation to the donor
            Notification.objects.create(
                recipient=instance.donated_by,
                message=f"You confirmed donation for {instance.patient_name}."
            )