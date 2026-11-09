from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Driver, DailyStatus
from .serializers import DriverSerializer, DriverCreateSerializer, DailyStatusSerializer
import logging

logger = logging.getLogger(__name__)


class DriverListView(generics.ListAPIView):
    """Barcha tasdiqlangan haydovchilar ro'yxati"""
    serializer_class = DriverSerializer

    def get_queryset(self):
        queryset = Driver.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class DriverCreateView(generics.CreateAPIView):
    """Yangi haydovchi qo'shish (admin tasdiqlashi kutiladi)"""
    serializer_class = DriverCreateSerializer

    def create(self, request, *args, **kwargs):
        telegram_id = request.data.get('telegram_id')
        driver = Driver.objects.filter(telegram_id=telegram_id).first()
        if driver:
            if driver.status == Driver.STATUS_APPROVED:
                return Response(
                    {
                        'detail': 'Haydovchi allaqachon mavjud va tasdiqlangan',
                        'status': driver.status,
                        'id': driver.id,
                        'driver': DriverSerializer(driver).data
                    },
                    status=status.HTTP_200_OK
                )
            # Pending yoki rejected bo'lsa, ma'lumotlarni yangilab, yana pending qilamiz
            serializer = self.get_serializer(driver, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            driver.status = Driver.STATUS_PENDING
            serializer.save()
            return Response(DriverSerializer(driver).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        driver = Driver.objects.get(id=serializer.instance.id)
        return Response(DriverSerializer(driver).data, status=status.HTTP_201_CREATED, headers=headers)


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Haydovchi ma'lumotlari"""
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


class DriverByTelegramView(APIView):
    """Telegram ID orqali haydovchini olish"""
    def get(self, request, telegram_id):
        try:
            driver = Driver.objects.get(telegram_id=telegram_id)
            serializer = DriverSerializer(driver)
            return Response(serializer.data)
        except Driver.DoesNotExist:
            return Response({'detail': 'Haydovchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)


class DriverApproveView(APIView):
    """Haydovchini tasdiqlash"""
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.status = Driver.STATUS_APPROVED
        driver.save()
        return Response({'detail': 'Haydovchi tasdiqlandi', 'driver': DriverSerializer(driver).data})


class DriverRejectView(APIView):
    """Haydovchini rad etish"""
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.status = Driver.STATUS_REJECTED
        driver.save()
        return Response({'detail': 'Haydovchi rad etildi', 'driver': DriverSerializer(driver).data})


class PendingDriversView(generics.ListAPIView):
    """Admin tasdiqlashini kutayotgan haydovchilar"""
    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(status=Driver.STATUS_PENDING)


class ApprovedDriversView(generics.ListAPIView):
    """Tasdiqlangan haydovchilar"""
    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(status=Driver.STATUS_APPROVED, is_active=True)


# ---- Daily Status Views ----

class TodayStatusListView(generics.ListAPIView):
    """Bugungi kunlik statuslar"""
    serializer_class = DailyStatusSerializer

    def get_queryset(self):
        today = timezone.now().date()
        qs = DailyStatus.objects.filter(date=today).select_related('driver')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        location_filter = self.request.query_params.get('location')
        if location_filter:
            qs = qs.filter(location=location_filter)
        return qs


class SetDailyStatusView(APIView):
    """Haydovchi kunlik statusini o'rnatish"""
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        new_status = request.data.get('status')
        location = request.data.get('location', None)
        moving_direction = request.data.get('moving_direction', None)

        try:
            driver = Driver.objects.get(telegram_id=telegram_id, status=Driver.STATUS_APPROVED)
        except Driver.DoesNotExist:
            return Response({'detail': 'Tasdiqlangan haydovchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        daily_status, created = DailyStatus.objects.get_or_create(
            driver=driver,
            date=today,
            defaults={'status': new_status, 'location': location, 'moving_direction': moving_direction}
        )

        if not created:
            daily_status.status = new_status
            if location is not None:
                daily_status.location = location
            if moving_direction is not None:
                daily_status.moving_direction = moving_direction
            daily_status.save()

        return Response(DailyStatusSerializer(daily_status).data)


class WorkingDriversTodayView(APIView):
    """Bugun ishlaydigan haydovchilar"""
    def get(self, request):
        today = timezone.now().date()
        statuses = DailyStatus.objects.filter(
            date=today,
            status=DailyStatus.STATUS_WORKING,
            driver__status=Driver.STATUS_APPROVED
        ).select_related('driver')
        serializer = DailyStatusSerializer(statuses, many=True)
        return Response(serializer.data)


class DriverLocationUpdateView(APIView):
    """Haydovchi joylashuvini yangilash"""
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        location = request.data.get('location')
        moving_direction = request.data.get('moving_direction')

        try:
            driver = Driver.objects.get(telegram_id=telegram_id, status=Driver.STATUS_APPROVED)
        except Driver.DoesNotExist:
            return Response({'detail': 'Haydovchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        daily_status, _ = DailyStatus.objects.get_or_create(
            driver=driver,
            date=today,
            defaults={'status': DailyStatus.STATUS_WORKING}
        )
        daily_status.location = location
        daily_status.moving_direction = moving_direction
        daily_status.save()

        return Response({'detail': 'Joylashuv yangilandi', 'location': location})
 
 
class ResetDailyLocationsView(APIView):
    """Kunning oxirida yoki yarim kechada haydovchilar joylashuvini tozalash"""
    def post(self, request):
        today = timezone.now().date()
        updated_count = DailyStatus.objects.filter(date=today).update(location=None, moving_direction=None)
        return Response({'detail': f"{updated_count} ta haydovchi joylashuvi tozalandi", 'count': updated_count})
