from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.viewsets import ModelViewSet
from .models import Metric
from .serializer import MetricSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.serializers import Serializer

import httplib2
import json

# Create your views here.   
class MetricViewSet(ModelViewSet):
    queryset = Metric.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': MetricSerializer,
        'read': MetricSerializer,
        'getget': MetricSerializer,
    }

    def get_serializer_class(self):
        if self.serializer_classes:
            action = self.action
            serializer_class = self.serializer_classes.get(action)

            if not serializer_class:
                if action == 'list':
                    action = 'list_read'
                if action == 'retrieve':
                    action = 'read'
                # if action in ['create', 'update', 'partial_update']:
                #     action = 'write'
                serializer_class = self.serializer_classes.get(action, self.serializer_class)

            if not serializer_class:
                serializer_class = Serializer
            return serializer_class
        return super().get_serializer_class()

    @action(methods=['post'], detail=False)
    def getget(self, request):
        http = httplib2.Http()
        metric_name = ''
        try:
            metric_name = request.data['query']
        except KeyError:
            metric_name = ''
        url = "http://127.0.0.1:9090/api/v1/query?query=" + metric_name
        response, response_body = http.request(url, method="GET", 
                                         headers={'Content-Type': 'application/json;'})
        response_str = response_body.decode('utf-8')
        response_dict = None
        error = None
        try:
            response_dict = json.loads(response_str)
        except ValueError:
            error = '오류가 발생했습니다.'
        except TypeError:
            error = '오류가 발생했습니다.'
        if error is None and response_dict['status'] == 'success' and response_dict['data']['result']:
            return Response(response_dict)
        else:
            return JsonResponse({"error": "해당 query에 대한 결과값을 읽을 수 없습니다."}, status=HTTP_400_BAD_REQUEST)