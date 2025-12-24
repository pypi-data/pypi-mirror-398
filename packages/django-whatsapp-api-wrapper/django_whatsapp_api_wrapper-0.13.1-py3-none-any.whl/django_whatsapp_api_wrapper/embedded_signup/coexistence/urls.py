from django.urls import path
from .views import SyncContactsView, SyncHistoryView

urlpatterns = [
    path('sync-contacts/', SyncContactsView.as_view(), name='coexistence_sync_contacts'),
    path('sync-history/', SyncHistoryView.as_view(), name='coexistence_sync_history'),
]

