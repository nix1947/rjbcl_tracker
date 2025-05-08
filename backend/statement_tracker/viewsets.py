from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.decorators import api_view  
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from .serializers import PasswordResetRequestSerializer
from django.utils import timezone
from .models import Bank, Transaction
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserDetailSerializer, BankSerializer, TransactionSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import PasswordChangeSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserSerializer  # Handles password input and validation
        return UserDetailSerializer  # For retrieve, list (doesn't expose password fields)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserDetailSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class BankViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows banks to be viewed or edited.
    """
    queryset = Bank.objects.all().order_by('name')
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows transactions to be viewed or edited.
    """
    queryset = Transaction.objects.all().order_by('-created_date')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    
    def get_queryset(self):
        """
        Optionally filter transactions by user if not admin
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def verify(self, request, pk=None):
        transaction = self.get_object()
        if transaction.is_verified:
            return Response(
                {'status': 'transaction already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.is_verified = True
        transaction.save(update_fields=['is_verified'])
        return Response({'status': 'transaction verified'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reconcile(self, request, pk=None):
        transaction = self.get_object()
        if transaction.status == 'Reconciled':
            return Response(
                {'status': 'transaction already reconciled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.status = 'Reconciled'
        transaction.reconciled_by = request.user
        transaction.reconciled_date = timezone.now().date()
        transaction.save(update_fields=['status', 'reconciled_by', 'reconciled_date'])
        return Response({'status': 'transaction reconciled'})
    
    



class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully"})
        return Response(serializer.errors, status=400)
    
    
## Reset password views
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f"http://yourdomain.com/reset-password-confirm/?uidb64={uid}&token={token}"

            subject = 'Password Reset Request'
            message = f'Hello {user.username},\n\nUse the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            return Response({"message": "Password reset link sent to your email."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password has been reset successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
