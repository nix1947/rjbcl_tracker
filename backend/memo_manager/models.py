from django.db import models
from django.utils import timezone
from django.conf import settings
from rjbcl.common_data import FISCAL_YEAR_CHOICES
from ticket.models import Department
from tinymce.models import HTMLField



# Choices for the Memo Type flag
MEMO_TYPE_CHOICES = [
    ('OUT', 'विभागबाट जारी (Outgoing/Given by Department)'),
    ('CEO', 'सीईओबाट स्वीकृत (CEO Approved/Received by Department)'),
]


class MemoRecord(models.Model):
    """
    A single class to record both outgoing memos and CEO-approved memos.
    """

    # CORE DETAILS
    memo_type = models.CharField(
        max_length=3,
        choices=MEMO_TYPE_CHOICES,
        default='CEO',
        verbose_name="मेमोको प्रकार (Memo Type)"
    )
    # ... (other core fields remain the same)
    fy_title = models.CharField(
        max_length=10,
        choices=FISCAL_YEAR_CHOICES,
        verbose_name="आ.व. (Fiscal Year)"
    )
    date_of_record = models.DateField(
        default=timezone.now,
        verbose_name="मिति (Date of Issue/Approval)"
    )

    # MEMO CONTENT
    title = models.CharField(
        max_length=255,
        verbose_name="विषय (Title/Subject)"
    )
    description = HTMLField(
        blank=True,
        verbose_name="छोटो विवरण (Short Description)"
    )
    memo_document = models.FileField(
        upload_to='memos/%Y/%m/',
        verbose_name="मेमोको फाइल (Memo Document File)",
        blank=True,
        null=True
    )

    # AUDIT & CONTROL FIELDS
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="सिर्जना गर्ने (Created By)",
        related_name='memos_created'
    )
    created_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="सिर्जना गर्ने विभाग (Creating Department)",
        related_name='memos_created_by'
    )

    # NEW FIELD: Secondary Department (Recipient/Related)
    related_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="सम्बन्धित विभाग (Related/Recipient Department)",
        # This will be used to grant viewing access to the outgoing department
        related_name='memos_related_to'
    )

    # CONTROL FLAG
    is_final = models.BooleanField(
        default=False,
        verbose_name="अन्तिम (Finalized/Locked)"
    )

    class Meta:
        verbose_name = "मेमो रेकर्ड"
        verbose_name_plural = "मेमो रेकर्डहरू"
        ordering = ['-date_of_record', 'fy_title']

    def __str__(self):
        type_display = dict(MEMO_TYPE_CHOICES).get(self.memo_type, self.memo_type)
        final_status = "(Final)" if self.is_final else ""
        return f"[{type_display}] {self.title} {final_status}"