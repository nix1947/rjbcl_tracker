from django.db import models

# clients/models.py

import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from django.urls import reverse

# --- Validators ---
phone_regex = RegexValidator(
    regex=r'^(?:\+977|0)?\d{9,10}$',
    message="Phone number must be a valid 9 to 10-digit Nepali number (e.g., +97798XXXXXXXX or 98XXXXXXXX)."
)

# --- Choices ---
GENDER_CHOICES = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
)

MARITAL_CHOICES = (
    ('Single', 'Single'),
    ('Married', 'Married'),
    ('Divorced', 'Divorced'),
    ('Widowed', 'Widowed'),
)

PROVINCE_CHOICES = (
    ('Koshi', 'Koshi'),
    ('Madhesh', 'Madhesh'),
    ('Bagmati', 'Bagmati'),
    ('Gandaki', 'Gandaki'),
    ('Lumbini', 'Lumbini'),
    ('Karnali', 'Karnali'),
    ('Sudurpashchim', 'Sudurpashchim'),
)


class Client(models.Model):
    # --- Client/User Section ---
    client_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g., 21/10/2022-L/097/44"
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_CHOICES)

    profession = models.CharField(max_length=100, blank=True)
    income_source = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100, blank=True)

    # --- Contact & Address ---
    phone_no = models.CharField(
        max_length=15,
        validators=[phone_regex],
        verbose_name="Phone Number"
    )
    email = models.EmailField(blank=True, help_text="Optional. E.g., user@example.com")

    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES)
    district = models.CharField(max_length=100)
    local_unit = models.CharField(max_length=100, verbose_name="Local Unit (VDC/Municipality)")
    address = models.CharField(max_length=255, verbose_name="Ward/Tole")
    temporary_address = models.CharField(max_length=255, blank=True)

    # --- Bank Details ---
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)

    # --- Family Details ---
    father_name = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    grandfather_name = models.CharField(max_length=200, blank=True)
    spouse_name = models.CharField(max_length=200, blank=True, help_text="Enter if married")

    # --- Other ---
    is_insured = models.BooleanField(default=False, verbose_name="Is Confirmed Insured?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Model-level validation.
        """
        # 1. Validate Date of Birth
        if self.dob and self.dob > timezone.now().date():
            raise ValidationError({'dob': "Date of Birth cannot be in the future."})

        # 2. Validate Spouse Name
        if self.marital_status == 'Married' and not self.spouse_name:
            raise ValidationError({'spouse_name': "Spouse name is required if marital status is 'Married'."})

    def get_absolute_url(self):
        """
        Returns the URL to display the detail page for this client.
        """
        return reverse('client-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client_id})"