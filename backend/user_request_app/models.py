from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from rjbcl.common_data import (
    DEPARTMENTS, GENDER_CHOICES, NATIONALITY_CHOICES, DOCUMENT_TYPE_CHOICES,
    PROVINCE_CHOICES, DESIGNATION_CHOICES, BRANCH_CHOICES

)


class MenuItem(models.Model):
    """Represents all available system modules or permissions."""
    name = models.CharField(max_length=150, unique=True)
    parent_menu = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']
        verbose_name = "ISolution Menu / Module"
        verbose_name_plural = "Isolution Menus / Modules"

    def __str__(self):
        return self.name + " - " + self.parent_menu


class UserRequest(models.Model):
    """Main user request form for software/system access."""
    REQUEST_TYPE_CHOICES = [
        ('New Access', 'New Access'),
        ('Modification', 'Access Modification'),
        ('Deactivation', 'Deactivation'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    request_id = models.AutoField(primary_key=True)
    request_date = models.DateField(auto_now_add=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests_made')
    department = models.CharField(
        max_length=100,
        choices=DEPARTMENTS,
        default='Administration',
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField( verbose_name="RJBCL office email", unique=True)
    phone_no = models.CharField(max_length=20)
    mobile_no = models.CharField(max_length=20)
    ssn = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=30, choices=NATIONALITY_CHOICES)

    # --- Document Information ---
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, default='Citizen')
    citizen_no = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES)
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES, blank=True, null=True)

    # --- Office Information ---
    designation = models.CharField(max_length=100, choices=DESIGNATION_CHOICES)

    # --- System Access Flags ---
    allow_approve_transaction = models.BooleanField(default=False)
    allow_back_date = models.BooleanField(default=False)
    is_regional_head = models.BooleanField(default=False)
    is_branch_manager = models.BooleanField(default=False)
    allow_advance_payment = models.BooleanField(default=False)
    is_me_user = models.BooleanField(default=False)

    contact_email = models.EmailField(verbose_name="Personal Email")
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES, default='New Access')
    description = models.TextField(blank=True, null=True)

    # many-to-many relationship to MenuItem
    permissions_requested = models.ManyToManyField(MenuItem, related_name='user_requests')

    # memo fields
    memo_reference_no = models.CharField(max_length=50, blank=True, null=True)
    memo_date = models.DateField(blank=True, null=True)
    memo_subject = models.CharField(max_length=200, blank=True, null=True)
    approval_form = models.FileField()


    # approval and status
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='requests_approved', null=True, blank=True)
    approval_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Request #{self.request_id} - {self.requested_by.username}"

    class Meta:
        verbose_name = "User Request"
        verbose_name_plural = "Request -> New Isolution User"
        ordering = ['-request_date']
