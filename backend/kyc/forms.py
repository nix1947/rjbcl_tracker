# clients/forms.py

from django import forms
from django.core.exceptions import ValidationError

from .models import Client
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        # Include all fields from the model
        fields = '__all__'

        # Add widgets for date fields to get a nice date picker
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # This makes the form render fields in a more compact, two-column layout
        # This is a huge benefit of crispy-forms!
        self.helper.layout = Layout(
            Row(
                Column('client_id', css_class='form-group col-md-6 mb-0'),
                Column('is_insured', css_class='form-group col-md-6 mb-0 d-flex align-items-center'),
                css_class='form-row'
            ),
            '---',
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('dob', css_class='form-group col-md-4 mb-0'),
                Column('gender', css_class='form-group col-md-4 mb-0'),
                Column('marital_status', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            '---',
            Row(
                Column('phone_no', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('province', css_class='form-group col-md-4 mb-0'),
                Column('district', css_class='form-group col-md-4 mb-0'),
                Column('local_unit', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('address', css_class='form-group col-md-6 mb-0'),
                Column('temporary_address', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            '---',
            Row(
                Column('profession', css_class='form-group col-md-4 mb-0'),
                Column('income_source', css_class='form-group col-md-4 mb-0'),
                Column('qualification', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('bank_name', css_class='form-group col-md-6 mb-0'),
                Column('bank_account_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            '---',
            Row(
                Column('father_name', css_class='form-group col-md-6 mb-0'),
                Column('mother_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('grandfather_name', css_class='form-group col-md-6 mb-0'),
                Column('spouse_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            # Add a submit button to the helper
            Submit('submit', 'Save Client', css_class='btn-primary mt-3')
        )

    def clean_email(self):
        """
        Example of form-level validation.
        """
        email = self.cleaned_data.get('email')
        if email and "spam.com" in email:
            raise ValidationError("We do not accept emails from spam.com.")
        return email