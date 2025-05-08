from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from .models import Bank, Transaction
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True, 
        label="Confirm Password",
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'mobile', 
            'password', 'password2', 'is_active', 'is_staff', 
            'date_joined', 'last_login'
        )
        read_only_fields = (
            'id', 'is_active', 'is_staff', 'date_joined', 'last_login'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'full_name': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        try:
            password2 = attrs.pop('password2', None)
            user_instance = User(**{k: v for k, v in attrs.items() if k != 'password'})
            user_instance.clean()
            if password2 is not None:
                attrs['password2'] = password2
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            mobile=validated_data.get('mobile')
        )
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'mobile',
            'is_active', 'is_staff', 'date_joined', 'last_login'
        )
        read_only_fields = fields

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ('id', 'name', 'description')
        extra_kwargs = {
            'name': {'required': True},
            'description': {'required': False}
        }

    def validate_name(self, value):
        if Bank.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A bank with this name already exists.")
        return value

    def validate(self, attrs):
        try:
            instance = Bank(**attrs)
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs

class TransactionSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    reconciled_by_username = serializers.ReadOnlyField(
        source='reconciled_by.username', 
        allow_null=True
    )
    system_posted_by_username = serializers.ReadOnlyField(
        source='system_posted_by.username', 
        allow_null=True
    )
    system_verified_by_username = serializers.ReadOnlyField(
        source='system_verified_by.username', 
        allow_null=True
    )
    bank_name = serializers.ReadOnlyField(source='bank.name')

    bank = serializers.PrimaryKeyRelatedField(queryset=Bank.objects.all())
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    reconciled_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        allow_null=True, 
        required=False
    )
    system_posted_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        allow_null=True, 
        required=False
    )
    system_verified_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        allow_null=True, 
        required=False
    )

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = (
            'id', 'created_date', 'created_by_username', 
            'reconciled_by_username', 'system_posted_by_username',
            'system_verified_by_username', 'bank_name'
        )
        extra_kwargs = {
            'amount': {'required': True},
            'transaction_type': {'required': True},
            'status': {'required': False},
            'is_verified': {'required': False},
        }

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        try:
            instance = self.instance if self.instance else Transaction()
            for key, value in attrs.items():
                setattr(instance, key, value)
            instance.clean()
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError(e.messages)
        
        # Additional business logic validation
        if attrs.get('transaction_type') == 'Withdrawal' and attrs.get('amount') > 10000:
            raise serializers.ValidationError(
                {"amount": "Withdrawals over $10,000 require special approval."}
            )
            
        return attrs

    def create(self, validated_data):
        # Set default values if not provided
        if 'status' not in validated_data:
            validated_data['status'] = 'Pending'
        if 'is_verified' not in validated_data:
            validated_data['is_verified'] = False
            
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Format decimal fields for display
        representation['amount'] = float(representation['amount'])
        # Add human-readable transaction type
        representation['transaction_type_display'] = instance.get_transaction_type_display()
        return representation
    
    
    


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user exists with this email address.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Confirm New Password",
        style={'input_type': 'password'}
    )
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

## Password reset serializers
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid UID")

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Invalid or expired token.")

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
