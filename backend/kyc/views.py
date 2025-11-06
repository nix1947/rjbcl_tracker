# clients/views.py

from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Client
from .forms import ClientForm

class ClientListView(ListView):
    model = Client
    template_name = 'kyc/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10  # Optional: adds pagination

class ClientDetailView(DetailView):
    model = Client
    template_name = 'kyc/client_detail.html'
    context_object_name = 'client'

class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'kyc/client_form.html'
    success_url = reverse_lazy('client-list') # Redirect to list view on success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Add New Client'
        return context

class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'kyc/client_form.html'
    success_url = reverse_lazy('client-list') # Redirect to list view on success

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Client'
        return context

class ClientDeleteView(DeleteView):
    model = Client
    template_name = 'kyc/client_confirm_delete.html'
    context_object_name = 'client'
    success_url = reverse_lazy('client-list')