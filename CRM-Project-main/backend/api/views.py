from django.shortcuts import render
from .models import User, Record, Customer, Order, Segment, Campaign, CommunicationLog

# Create your views here.

from .serializers import MyTOPS, RegistrationSerializer, RecordSerializer, CustomerSerializer, OrderSerializer, SegmentSerializer, CampaignSerializer, CommunicationLogSerializer
from django.shortcuts import render, get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.urls import reverse_lazy
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.views.generic.edit import CreateView, UpdateView, DeleteView


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTOPS


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protectedView(request):
    output = f"Welcome {request.user}, Authentication SUccessful"
    return Response({"response": output}, status=status.HTTP_200_OK)


@api_view(["GET"])
def view_all_routes(request):
    data = ["api/token/refresh/", "api/register/", "api/token/"]

    return Response(data)


class RecordListCreateAPIView(generics.ListCreateAPIView):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer

class RecordRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer


class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class OrderListCreateAPIView(generics.ListCreateAPIView):
    queryset = Order.objects.select_related('customer').all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


class OrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.select_related('customer').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


def apply_segment_rules(queryset, rules):
    # Very simple rules demo: supports keys: min_spend, max_visits, inactive_days
    from django.utils import timezone
    from datetime import timedelta
    min_spend = rules.get('min_spend')
    max_visits = rules.get('max_visits')
    inactive_days = rules.get('inactive_days')
    if min_spend is not None:
        queryset = queryset.filter(total_spend__gte=min_spend)
    if max_visits is not None:
        queryset = queryset.filter(visits__lte=max_visits)
    if inactive_days is not None:
        cutoff = timezone.now() - timedelta(days=inactive_days)
        queryset = queryset.filter(last_active_at__lt=cutoff)
    return queryset


class SegmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Segment.objects.all().order_by('-created_at')
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        rules = self.request.data.get('rules', {})
        customers = apply_segment_rules(Customer.objects.all(), rules)
        audience_size = customers.count()
        serializer.save(audience_size=audience_size)


class SegmentPreviewAPIView(generics.GenericAPIView):
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        rules = request.data.get('rules', {})
        customers = apply_segment_rules(Customer.objects.all(), rules)
        return Response({"audience_size": customers.count()})


class CampaignListCreateAPIView(generics.ListCreateAPIView):
    queryset = Campaign.objects.select_related('segment').all().order_by('-created_at')
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        campaign = serializer.save()
        # enqueue communications
        customers = apply_segment_rules(Customer.objects.all(), campaign.segment.rules)
        logs = []
        for customer in customers.iterator():
            logs.append(CommunicationLog(campaign=campaign, customer=customer, status='PENDING'))
        CommunicationLog.objects.bulk_create(logs, batch_size=500)
        # Simulate async delivery by hitting local vendor endpoint
        # Keep it synchronous for MVP; can move to Celery/Redis later
        import requests, random, uuid
        for log in CommunicationLog.objects.filter(campaign=campaign):
            payload = {
                "log_id": log.id,
                "to": customer.email if 'customer' in locals() else '',
                "message": campaign.message,
                "vendor_message_id": str(uuid.uuid4())
            }
            try:
                requests.post("http://localhost:8000/api/vendor/send/", json=payload, timeout=3)
            except Exception:
                pass


class CommunicationLogListAPIView(generics.ListAPIView):
    queryset = CommunicationLog.objects.select_related('campaign', 'customer').all().order_by('-created_at')
    serializer_class = CommunicationLogSerializer
    permission_classes = [IsAuthenticated]


class VendorSendAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Simulate 90% success
        import random
        log_id = request.data.get('log_id')
        vendor_message_id = request.data.get('vendor_message_id')
        status_out = 'SENT' if random.random() < 0.9 else 'FAILED'
        # Call delivery receipt
        import requests
        try:
            requests.post("http://localhost:8000/api/delivery/receipt/", json={
                "log_id": log_id,
                "status": status_out,
                "vendor_message_id": vendor_message_id
            }, timeout=3)
        except Exception:
            pass
        return Response({"status": status_out})


class DeliveryReceiptAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        log_id = request.data.get('log_id')
        status_in = request.data.get('status')
        vendor_message_id = request.data.get('vendor_message_id', '')
        log = get_object_or_404(CommunicationLog, id=log_id)
        log.status = status_in
        log.vendor_message_id = vendor_message_id
        log.save(update_fields=['status', 'vendor_message_id', 'updated_at'])
        return Response({"updated": True})