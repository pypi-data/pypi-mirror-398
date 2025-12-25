from datetime import timedelta

from django.db.models import Manager
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from .base import BaseAPIView
from .serializers import DashboardDateSerializer, DashboardSerializer
from ..utils import to_edatetime, to_edate, EDateTime


class TranslatedListView(generics.ListAPIView, BaseAPIView):
    manager: Manager

    def get_queryset(self):
        self.update_lang()
        return self.manager.all()


@extend_schema(parameters=[DashboardDateSerializer])
class BaseDashboardIndustryView(BaseAPIView):
    serializer_class = DashboardDateSerializer

    def get_period_data(self, request, prev=False):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        period = serializer.validated_data['period']
        datetime = serializer.validated_data['datetime']

        given_period = to_edatetime(datetime).first_second_of_hour() if period == 'hourly' else to_edate(datetime.date())
        if prev:
            prev_period = (given_period - timedelta(hours=1)) if period == 'hourly' else to_edate(given_period).yesterday()
            return period, given_period, prev_period

        return period, given_period


@extend_schema(parameters=[DashboardSerializer])
class BaseDashboardView(BaseAPIView):
    serializer_class = DashboardSerializer

    def get_period_data(self, request, prev=False):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        period = serializer.validated_data['period']
        datetime = serializer.validated_data.get('datetime') or EDateTime.now()

        if period == 'hourly':
            given_period = to_edatetime(datetime).first_second_of_hour()
        elif period == 'today':
            given_period = to_edatetime(datetime).first_second_of_day()
        else:
            given_period = to_edate(datetime.date())
        if prev:
            if period == 'hourly':
                prev_period = given_period - timedelta(hours=1)
            elif period == 'today':
                prev_period = (given_period - timedelta(days=1)).date()
            elif period == 'daily':
                prev_period = to_edate(given_period).yesterday()
            elif period == 'monthly':
                prev_period = to_edate(given_period).first_day_of_last_month()
            else:
                prev_period = to_edate(given_period).first_day_of_last_year()
            return period, given_period, prev_period

        return period, given_period
