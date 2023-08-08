from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from .models import Metrics
from .serializer import MetricsSerializer
from rest_framework.response import Response

# Create your views here.

class MetricsView(APIView):
    def get(self, request):
        queryset = Metrics.objects.all()
        serializer = MetricsSerializer(queryset, many=True)
        return Response(serializer.data)