from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Metric
from .serializer import MetricSerializer
from rest_framework.response import Response

# Create your views here.

class MetricView(APIView):
    def get(self, request):
        queryset = Metric.objects.all()
        serializer = MetricSerializer(queryset, many=True)
        return Response(serializer.data)
    
# class MetricViewSet(ModelViewSet):
#     queryset = Metric.objects.all()
#     serializer_classes = {
#         'list': MetricSerializer
#     }