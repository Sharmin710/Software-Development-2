from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from .forms import UserRegisterForm, DonorProfileForm, RecipientProfileForm , UserBloodRequestForm, AdminBloodRequestForm
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .models import User, Donor, Recipient, Blood, BloodRequest, Notification  # your custom User model
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from datetime import timedelta


def home(request):
    return render(request, 'home.html')


def is_approved_admin(user):
    return user.is_authenticated and user.is_qualified_admin


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            if user.role == 'admin':
                user.is_approved = False
                messages.info(request, "Admin registration submitted. Awaiting approval.")

            user.save()

            try:
                if user.role == 'donor':
                    default_blood = Blood.objects.filter(blood_group='Unknown').first()
                    if not default_blood:
                        raise Exception("Missing default blood group 'Unknown'.")

                    Donor.objects.create(
                        user=user,
                        name='',
                        phone='',
                        dob='2000-01-01',  # placeholder
                        address='',
                        gender='',
                        health_condition='',
                        blood=default_blood
                    )
                
                elif user.role == 'recipient':
                    default_blood = Blood.objects.filter(blood_group='Unknown').first()
                    if not default_blood:
                        raise Exception("Missing default blood group 'Unknown'.")

                    Recipient.objects.create(
                        user=user,
                        name='',
                        phone='',
                        dob='2000-01-01',  # placeholder
                        address='',
                        gender='',
                        recipient_type='Self',  # or default value as per your model choices
                        medical_condition='',
                        blood=default_blood
                    )

            except Exception as e:
                user.delete()
                messages.error(request, f"Registration failed: {str(e)}")
                return redirect('register')  # back to form

            login(request, user)

            if user.role == 'donor':
                request.session['show_success'] = True
                return redirect('registration_success')
            if user.role == 'admin':
                return redirect('home')
            if user.role == 'recipient':
                return redirect('profile')  # or wherever recipient should go
            else:
                messages.success(request, 'Account created successfully!')
                return redirect('profile')
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})



def registration_success_view(request):
    if not request.session.get('show_success'):
        return redirect('register')  # Or some other safe page

    # Clear flag so user can't access it again
    del request.session['show_success']
    return render(request, 'registration_success.html')


def request_success(request):
    return render(request, 'blood/request_success.html')


@login_required
def donor_profile(request, donor_id):
    donor = get_object_or_404(User, id=donor_id, role='donor')

    # Optional: mark related notification as read
    Notification.objects.filter(donor=donor, recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'recipient/donor_profile.html', {'donor': donor})


@login_required
def profile_redirect_view(request):
    user = request.user
    if user.role == 'donor':
        return redirect('donor_profile')
    elif user.role == 'recipient':
        return redirect('recipient_profile')
    elif user.role == 'admin':
        return redirect('admin_profile')  # if needed
    else:
        return HttpResponseForbidden("Invalid user role.")


@login_required
def donor_profile_view(request):
    user = request.user
    if user.role != 'donor':
        return HttpResponseForbidden("You are not authorized to view this page.")

    try:
        donor = Donor.objects.get(user=user)
    except Donor.DoesNotExist:
        donor = None

    return render(request, 'donor/donor_profile.html', {'donor': donor})


@login_required
def recipient_profile_view(request):
    user = request.user
    if user.role != 'recipient':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Get recipient profile
    try:
        recipient = Recipient.objects.get(user=user)
    except Recipient.DoesNotExist:
        recipient = None

    # Get blood requests created by this user
    blood_requests = BloodRequest.objects.filter(created_by=user).order_by('-created_at')

    return render(request, 'recipient/recipient_profile.html', {
        'user': user,
        'recipient': recipient,
        'blood_requests': blood_requests,
    })


@user_passes_test(is_approved_admin)
def admin_profile_view(request):
    user = request.user
    return render(request, 'admin/admin_profile.html', {'user': user})


@login_required
def edit_donor_profile(request):
    user = request.user
    donor = Donor.objects.filter(user=user).first()

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor)
        if form.is_valid():
            donor = form.save(commit=False)
            donor.user = user
            donor.save()
            return redirect('donor_profile')
    else:
        form = DonorProfileForm(instance=donor)

    return render(request, 'donor/edit_donor_profile.html', {
        'user': user,
        'form': form,
        'donor': donor,
    })


@login_required
def edit_recipient_profile(request):
    try:
        recipient = Recipient.objects.get(user=request.user)
    except Recipient.DoesNotExist:
        messages.error(request, "Recipient profile not found.")
        return redirect('recipient_profile')  # or wherever you want

    if request.method == 'POST':
        form = RecipientProfileForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('recipient_profile')
    else:
        form = RecipientProfileForm(instance=recipient)

    return render(request, 'recipient/edit_recipient_profile.html', {'form': form})


@login_required(login_url='signin')
def accept_blood_request(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)

    if request.user.role != 'donor':
        messages.error(request, "Only donors can accept requests.")
        return redirect('blood_requests')

    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "You are not registered as a donor.")
        return redirect('blood_requests')

    # Check blood group match
    if donor.blood != blood_request.blood:
        messages.error(request, "Your blood group does not match the request.")
        return redirect('blood_requests')

    # Check donation eligibility (90-day rule)
    if not donor.can_donate():
        eligible_date = donor.last_donated + timedelta(days=90)
        messages.error(request, f"You cannot donate yet. Eligible again on {eligible_date.strftime('%Y-%m-%d')}.")
        return redirect('blood_requests')

    if blood_request.status != 'pending':
        messages.warning(request, "This request has already been accepted.")
        return redirect('blood_requests')
    else:
        # Update blood request
        blood_request.status = 'accepted'
        blood_request.donated_by = request.user
        blood_request.donor = request.user
        blood_request.save()

        # Update donor record
        donor.last_donated = timezone.now().date()
        donor.donate_number += 1
        donor.save()

        # ✅ Create a notification for the recipient with donor info
        Notification.objects.create(
            recipient=blood_request.requester,
            donor=request.user,
            message=f"{request.user.first_name} has accepted your blood request.",
            related_request=blood_request
        )

        messages.success(request, "You have accepted this blood request. Donation record updated.")

    return redirect('blood_requests')


@login_required(login_url='signin')
def view_blood_requests(request):
    blood_group = request.GET.get('blood_group')
    blood_list = Blood.objects.all()

    if blood_group:
        requests = BloodRequest.objects.filter(blood__blood_group=blood_group)
    else:
        requests = BloodRequest.objects.all()

    return render(request, 'donor/blood_requests.html', {
        'requests': requests,
        'blood_list': blood_list,
        'selected_group': blood_group
    })


# @login_required
# def fill_request_form(request):
#     if request.method == 'POST':
#         form = BloodRequestForm(request.POST)
#         if form.is_valid():
#             blood_request = form.save(commit=False)
#             blood_request.created_by = request.user

#             # Get recipient associated with this user
#             try:
#                 blood_request.recipient = request.user.recipient  # or Recipient.objects.get(user=request.user)
#             except Recipient.DoesNotExist:
#                 messages.error(request, "You must have a Recipient profile to make a blood request.")
#                 return redirect('profile')  # or wherever you want

#             blood_request.save()
#             return redirect('request_success')  # Your success page
#     else:
#         form = BloodRequestForm()
#     return render(request, 'blood/fill_request_form.html', {'form': form})



def create_blood_request_user(request):
    if request.method == 'POST':
        form = UserBloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requester = request.user
            blood_request.created_by = request.user
            blood_request.save()
            return redirect('request_success')  # Replace with your success URL name
    else:
        form = UserBloodRequestForm()
    return render(request, 'blood/blood_request_form_user.html', {'form': form})


@user_passes_test(is_approved_admin)
def admin_blood_request_list(request):
    requests = BloodRequest.objects.all()
    return render(request, 'admin/blood_request_list.html', {'requests': requests})


@user_passes_test(is_approved_admin)
def edit_blood_request_admin(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)
    if request.method == 'POST':
        form = AdminBloodRequestForm(request.POST, instance=blood_request)
        if form.is_valid():
            form.save()
            return redirect('admin-request-edit', pk=blood_request.pk) # Replace with your admin listing view
    else:
        form = AdminBloodRequestForm(instance=blood_request)
    return render(request, 'admin/blood_request_form_admin.html', {'form': form})


@user_passes_test(is_approved_admin)
def delete_blood_request_admin(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk)
    if request.method == 'POST':
        blood_request.delete()
        messages.success(request, "Blood request deleted successfully.")
        return redirect('admin-request-list')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('admin-request-list')


@login_required
def edit_blood_request(request, request_id):
    blood_request = get_object_or_404(BloodRequest, id=request_id, requester=request.user)

    if request.method == 'POST':
        form = UserBloodRequestForm(request.POST, instance=blood_request)
        if form.is_valid():
            form.save()
            return redirect('recipient_profile')  # or any other success page
    else:
        form = UserBloodRequestForm(instance=blood_request)

    return render(request, 'blood/edit_blood_request.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user

    if user.role == 'donor':
        return render(request, 'donor/donor_profile.html', {'user': user})
    elif user.role == 'recipient':
        return render(request, 'recipient/recipient_profile.html', {'user': user})
    elif user.is_superuser or user.role == 'admin':
        return render(request, 'admin/admin_profile.html', {'user': user}) # Adjust template path if needed

    return render(request, 'profile.html', {'user': user})


@user_passes_test(is_approved_admin)
def admin_dashboard(request):
    # admin logic here
    return render(request, 'admin_dashboard.html')


@login_required(login_url='login')
def notification_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required(login_url='login')
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')  # or any other page


@login_required(login_url='login')
def mark_all_notifications_as_read(request):
    request.user.recipient_notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications')


@login_required(login_url='login')
def mark_as_unread(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = False
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))  # Redirect back


# Helper Functions
def is_admin_higher_priority(current_admin, other_admin):
    return current_admin.priority > other_admin.priority


def custom_login(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            if user.is_banned:
                messages.error(request, "Your account is banned.")
            elif user.role == 'admin' and not user.is_approved:
                messages.error(request, "Admin account is not approved yet.")
            else:
                login(request, user)
                return redirect('profile')
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, 'auth/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')  # or 'home'

