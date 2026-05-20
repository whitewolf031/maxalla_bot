from django.urls import path
from . import views

urlpatterns = [
    path('', views.DriverListView.as_view(), name='driver-list'),
    path('create/', views.DriverCreateView.as_view(), name='driver-create'),
    path('<int:pk>/', views.DriverDetailView.as_view(), name='driver-detail'),
    path('telegram/<int:telegram_id>/', views.DriverByTelegramView.as_view(), name='driver-by-telegram'),
    path('<int:pk>/approve/', views.DriverApproveView.as_view(), name='driver-approve'),
    path('<int:pk>/reject/', views.DriverRejectView.as_view(), name='driver-reject'),
    path('pending/', views.PendingDriversView.as_view(), name='driver-pending'),
    path('approved/', views.ApprovedDriversView.as_view(), name='driver-approved'),

    # Daily status
    path('status/today/', views.TodayStatusListView.as_view(), name='status-today'),
    path('status/set/', views.SetDailyStatusView.as_view(), name='status-set'),
    path('status/working/', views.WorkingDriversTodayView.as_view(), name='status-working'),
    path('status/location/', views.DriverLocationUpdateView.as_view(), name='status-location'),
]
