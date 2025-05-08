# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.shortcuts import render


@api_view(['GET'])
def api_index(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'banks': reverse('bank-list', request=request, format=format),
        'transactions': reverse('transaction-list', request=request, format=format),
        'auth': {
            'login': reverse('token_obtain_pair', request=request, format=format),
            'refresh': reverse('token_refresh', request=request, format=format),
            'password_reset': reverse('password_reset', request=request, format=format),
            'password_reset_confirm': reverse('password_reset_confirm', request=request, format=format),
            'change_password': reverse('change_password', request=request, format=format),
        }
    })



def dashboard(request):
    return render(request, 'dashboard.html')
