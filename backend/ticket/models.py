from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    is_branch = models.BooleanField(default=False)
    sla_hours = models.IntegerField(default=48, help_text="SLA hours for this department")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        branch_status = " (Branch)" if self.is_branch else " (Department)"
        return f"{self.name}{branch_status}"

    class Meta:
        verbose_name = "Department and Branches"
        verbose_name_plural = "Departments and Branches"


class Category(models.Model):


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Category Type"
        verbose_name_plural = "Categories Types"


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    REQUEST_TYPE_CHOICES = [
        ('New Business', 'New Business'),
        ('Renewal', 'Renewal'),
        ('Loan I', 'Loan Against Policy Individual'),
        ('Loan G', 'Loan Against Policy Group'),
        ('Surrender I', 'Policy Surrender Individual'),
        ('Surrender G', 'Policy Surrender Group'),
        ('Maturity', 'Maturity Claim'),
        ('Reinsurance', 'Reinsurance'),
        ('Actuary', 'Actuary'),
        ('Individual Death Claim', 'Death Claim Individual'),
        ('Group Death Claim', 'Death Claim Group'),
        ('Nomination Change Group', 'Nomination Change Group'),
        ('Nomination Change Individual', 'Nomination Change Individual'),
        ('Address Change', 'Address Change'),
        ('Premium Payment', 'Premium Payment Issue'),
        ('Policy Revival', 'Policy Revival'),
        ('Software Change Request', 'Software Change Request'),
        ('General', 'General'),
    ]

    ISSUE_TYPE_CHOICES = [
        ('Bug Fix', 'Bug and Error Fix'),
        ('Enhancement', 'Enhancement'),
        ('New Feature', 'New Feature'),
        ('Integration', 'Integration'),
        ('Security', 'Security Update'),
        ('Maintenance', 'Maintenance'),
        ('Configuration', 'Configuration'),
    ]

    URGENCY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Pending Customer', 'Pending Customer Response'),
        ('Pending Third Party', 'Pending Third Party'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
        ('Reopened', 'Reopened'),
        ('Transferred', 'Transferred to Another Department'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField()

    # Insurance Specific Fields
    identifier = models.CharField(
        help_text="PolicyNo, AgentCode, RoomNo, Your name",
        max_length=100,
        blank=True,
        null=True
    )

    # Ticket Metadata - FIXED: Changed related_name to be unique
    ticket_priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='ticket_tickets'  # CHANGED: from 'tickets' to 'ticket_tickets'
    )
    current_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')

    # For department transfers - FIXED: Changed related_names to be unique
    originating_department = models.ForeignKey(
        Department,
        help_text="Department where ticket was originally created",
        on_delete=models.PROTECT,
        related_name='ticket_originated_tickets',  # CHANGED: from 'originated_tickets'
        blank=True,
        null=True
    )

    to_department = models.ForeignKey(
        Department,
        help_text="Department where ticket will be sent",
        on_delete=models.PROTECT,
        related_name='ticket_to_department_transfer',  # CHANGED: from 'to_department_transfer'
        blank=True,
        null=True
    )

    transferred_from = models.ForeignKey(
        Department,
        help_text="Department from which ticket was transferred",
        on_delete=models.PROTECT,
        related_name='ticket_transferred_tickets',  # CHANGED: from 'transferred_tickets'
        blank=True,
        null=True
    )
    transfer_notes = models.TextField(blank=True, null=True)

    # Request Type
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)

    # Category and Issue Fields
    category = models.ForeignKey(Category, on_delete=models.PROTECT, blank=True, null=True)
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES, blank=True, null=True)
    urgency_level = models.CharField(max_length=20, choices=URGENCY_CHOICES, blank=True, null=True)
    estimated_effort_hours = models.IntegerField(blank=True, null=True)
    business_impact = models.TextField(blank=True, null=True)

    # Audit Fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_tickets')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_tickets',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    # SLA Management
    sla_due_date = models.DateTimeField(blank=True, null=True)
    sla_breached = models.BooleanField(default=False)

    # Memo required
    memo_required = models.BooleanField(default=False)
    memo = models.FileField(upload_to='ticket_memos/', blank=True, null=True)


    is_final = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number: TICKET-YYYYMMDD-XXXXX
            date_str = timezone.now().strftime('%Y%m%d')
            last_ticket = Ticket.objects.filter(
                created_at__date=timezone.now().date()
            ).order_by('-created_at').first()

            if last_ticket and last_ticket.ticket_number:
                try:
                    last_num = int(last_ticket.ticket_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.ticket_number = f"TICKET-{date_str}-{new_num:05d}"

        # AUTO-SET DEPARTMENT: Set department based on user's department
        if not self.department_id and self.created_by_id:
            user_department = self.get_user_department(self.created_by)
            if user_department:
                self.department = user_department

        # Set originating department for new tickets
        if not self.originating_department and self.department:
            self.originating_department = self.department

        # Auto-set SLA due date based on department and priority
        if not self.sla_due_date and self.department and hasattr(self.department, 'sla_hours'):
            self.sla_due_date = self.calculate_sla_due_date()

        # Update closed_at timestamp when status is changed to Closed
        if self.current_status == 'Closed' and not self.closed_at:
            self.closed_at = timezone.now()
        elif self.current_status != 'Closed':
            self.closed_at = None

        super().save(*args, **kwargs)

    def get_user_department(self, user):
        """
        Get the department for a user.
        """
        # Direct field on User model
        if hasattr(user, 'department') and user.department:
            return user.department

        # Check for any OneToOne related model that has a department field
        for field in user._meta.get_fields():
            if field.one_to_one and hasattr(user, field.name):
                try:
                    related_obj = getattr(user, field.name, None)
                    if related_obj and hasattr(related_obj, 'department') and getattr(related_obj, 'department', None):
                        return related_obj.department
                except:
                    continue

        return None

    def calculate_sla_due_date(self):
        if not hasattr(self.department, 'sla_hours'):
            return timezone.now() + timezone.timedelta(hours=48)

        base_hours = self.department.sla_hours
        priority_multiplier = {
            'Critical': 0.25,
            'High': 0.5,
            'Medium': 1,
            'Low': 2
        }
        due_hours = base_hours * priority_multiplier.get(self.ticket_priority, 1)
        return timezone.now() + timezone.timedelta(hours=due_hours)

    def transfer_to_department(self, new_department, transfer_notes="", user=None):
        """Transfer ticket to another department"""
        old_department = self.department
        self.transferred_from = old_department
        self.to_department = new_department
        self.department = new_department
        self.current_status = 'Transferred'
        self.transfer_notes = transfer_notes

        # Create status history for transfer
        if user:
            TicketStatusHistory.objects.create(
                ticket=self,
                old_status=f"In {old_department.name}",
                new_status=f"Transferred to {new_department.name}",
                changed_by=user,
                notes=transfer_notes
            )

        # Create department transfer record
        DepartmentTransfer.objects.create(
            ticket=self,
            from_department=old_department,
            to_department=new_department,
            transferred_by=user,
            notes=transfer_notes
        )

        self.save()

    @property
    def is_overdue(self):
        """Check if ticket is overdue based on SLA"""
        if self.sla_due_date and timezone.now() > self.sla_due_date:
            return True
        return False

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']


class TicketDiscussion(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('system', 'System Message'),
        ('resolution', 'Resolution Note'),
        ('transfer', 'Department Transfer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='discussions')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')

    # User and Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # For internal notes
    is_internal = models.BooleanField(default=False)

    def __str__(self):
        return f"Discussion on {self.ticket.ticket_number} by {self.created_by.username}"

    class Meta:
        verbose_name = "Ticket Discussion"
        verbose_name_plural = "Ticket Discussions"
        ordering = ['created_at']


class TicketStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.old_status} → {self.new_status}"

    class Meta:
        verbose_name = "Status History"
        verbose_name_plural = "Status History"
        ordering = ['-changed_at']


class ChangeRequestWorkflow(models.Model):
    WORKFLOW_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Blocked', 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='workflow_steps')
    workflow_step = models.CharField(max_length=100)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=50, choices=WORKFLOW_STATUS_CHOICES, default='Pending')
    due_date = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.workflow_step}"

    class Meta:
        verbose_name = "Change Request Workflow"
        verbose_name_plural = "Change Request Workflows"
        ordering = ['due_date']


class DepartmentTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='transfers')
    from_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='ticket_outgoing_transfers'  # CHANGED: from 'outgoing_transfers'
    )
    to_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='ticket_incoming_transfers'  # CHANGED: from 'incoming_transfers'
    )
    transferred_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    transferred_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.from_department} → {self.to_department}"

    class Meta:
        verbose_name = "Department Transfer"
        verbose_name_plural = "Department Transfers"
        ordering = ['-transferred_at']






