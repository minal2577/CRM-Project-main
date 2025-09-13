from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("token/", views.MyTokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh-token"),
    path("register/", views.RegisterView.as_view(), name="register-user"),
    path("test/", views.protectedView, name="test"),
    path("", views.view_all_routes, name="all-routes"),
    path(
        "records/", views.RecordListCreateAPIView.as_view(), name="record-list-create"
    ),
    path(
        "records/<int:pk>/",
        views.RecordRetrieveUpdateDestroyAPIView.as_view(),
        name="record-retrieve-update-destroy",
    ),
    path("customers/", views.CustomerListCreateAPIView.as_view(), name="customer-list-create"),
    path("customers/<int:pk>/", views.CustomerRetrieveUpdateDestroyAPIView.as_view(), name="customer-retrieve-update-destroy"),
    path("orders/", views.OrderListCreateAPIView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", views.OrderRetrieveUpdateDestroyAPIView.as_view(), name="order-retrieve-update-destroy"),
    path("segments/", views.SegmentListCreateAPIView.as_view(), name="segment-list-create"),
    path("segments/preview/", views.SegmentPreviewAPIView.as_view(), name="segment-preview"),
    path("campaigns/", views.CampaignListCreateAPIView.as_view(), name="campaign-list-create"),
    path("logs/", views.CommunicationLogListAPIView.as_view(), name="comm-log-list"),
    path("vendor/send/", views.VendorSendAPIView.as_view(), name="vendor-send"),
    path("delivery/receipt/", views.DeliveryReceiptAPIView.as_view(), name="delivery-receipt"),
]
