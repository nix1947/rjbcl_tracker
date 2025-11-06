# clients/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # C(R)UD: List View (Read)
    path('', views.ClientListView.as_view(), name='client-list'),

    # C(R)UD: Detail View (Read)
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),

    # (C)RUD: Create View
    path('new/', views.ClientCreateView.as_view(), name='client-create'),

    # CR(U)D: Update View
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client-update'),

    # CRU(D): Delete View
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client-delete'),
]