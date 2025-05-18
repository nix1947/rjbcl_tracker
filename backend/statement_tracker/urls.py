from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from .viewsets import UserViewSet, BankViewSet, TransactionViewSet, PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import api_index

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'banks', BankViewSet, basename='bank')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=True)),

    # path('', api_index, name='api_index'),  # ✅ Keep at root if needed
    path('api/', include(router.urls)),         # ✅ Make sure router is included right after
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('api/auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
