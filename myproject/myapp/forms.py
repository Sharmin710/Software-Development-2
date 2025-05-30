# yourapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Donor, BloodRequest, Blood, Recipient

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']


# class BloodRequestForm(forms.ModelForm):
#     class Meta:
#         model = BloodRequest
#         fields = ['r_email', 'r_phone', 'r_address', 'r_gender', 'r_age', 'r_qty', 'r_sickness', 'blood']
#         widgets = {
#             'r_gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
#             'r_address': forms.Textarea(attrs={'rows': 2}),
#             'r_sickness': forms.Textarea(attrs={'rows': 2}),
#         }

class RecipientProfileForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = [
            'name',
            'phone',
            'dob',
            'address',
            'gender',
            'recipient_type',
            'medical_condition',
            'blood',
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'medical_condition': forms.Textarea(attrs={'rows': 2}),
            'gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
        }

class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            'name', 'phone', 'dob', 'address', 'gender',
            'avail_to_donate', 'health_condition', 'blood',
            'last_donated'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }


class UserBloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        exclude = ['status', 'requester', 'created_by', 'donor', 'donated_by']
        widgets = {
            'r_gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'r_address': forms.Textarea(attrs={'rows': 2}),
            'r_sickness': forms.Textarea(attrs={'rows': 2}),
            'blood_need_when': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude "Unknown" blood group from blood field choices
        self.fields['blood'].queryset = Blood.objects.exclude(blood_group='Unknown')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.status = 'pending'  # Always default
        if commit:
            instance.save()
        return instance


class AdminBloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        exclude = ['requester', 'created_by']
        widgets = {
            'r_gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'r_address': forms.Textarea(attrs={'rows': 2}),
            'r_sickness': forms.Textarea(attrs={'rows': 2}),
            'blood_need_when': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
