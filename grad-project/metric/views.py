from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.viewsets import ModelViewSet
from .models import Category, Metric
from .serializer import CategorySerializer, CategoryListReadSerializer, MetricSerializer, MetricListReadSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.serializers import Serializer

import httplib2
import json
import yaml
import os
import random
import string

# Create your views here.
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': CategoryListReadSerializer,
        'read': CategorySerializer,
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

class MetricViewSet(ModelViewSet):
    queryset = Metric.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': MetricListReadSerializer,
        'read': MetricSerializer,
        'list_category': MetricListReadSerializer,
        'monitor': MetricSerializer,
        'getget': MetricSerializer,
        'modify_replicaSet': MetricSerializer,
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
    
    @action(methods=['get'], detail=False)
    def list_category(self, request):
        category_id = int(request.GET.get('category_id', 0))
        if category_id == 0:
            metrics = Metric.objects.all()
        else:
            metrics = Metric.objects.filter(category_id=category_id)
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)
    
    @action(methods=['post'], detail=False)
    def monitor(self, request):
        metric_id = int(request.GET.get('metric_id', 0))
        http = httplib2.Http()
        metric = Metric.objects.get(id=metric_id)
        metric_name = metric.name if metric is not None else ''
        
        # Cluster 내의 prometheus pod의 ip 주소를 입력해야함
        prometheus_ip = "http://127.0.0.1:9090"
        url = prometheus_ip + "/api/v1/query?query=" + metric_name
        response, response_body = http.request(url, method="GET", 
                                         headers={'Content-Type': 'application/json;'})
        response_str = response_body.decode('utf-8')
        response_dict = None
        error = None
        try:
            response_dict = json.loads(response_str)
        except ValueError:
            return JsonResponse({"error": "오류가 발생했습니다.[0]"}, status=HTTP_400_BAD_REQUEST)
        except TypeError:
            return JsonResponse({"error": "오류가 발생했습니다.[1]"}, status=HTTP_400_BAD_REQUEST)
        if error is None and response_dict['status'] == 'success' and response_dict['data']['result']:
            pod_value_list = []
            result_list = response_dict['data']['result']
            for result in result_list:
                try:
                    pod_name = result['metric']['pod']
                    value = result['value'][1]
                except KeyError:
                    return JsonResponse({"error": "오류가 발생했습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
                pod_value = {"pod_name": pod_name, "value": value}
                pod_value_list.append(pod_value)
            return Response(pod_value_list)
        else:
            return JsonResponse({"error": "오류가 발생했습니다.[3]"}, status=HTTP_400_BAD_REQUEST)


    @action(methods=['post'], detail=False)
    def getget(self, request):
        metric = Metric.objects.get(id=1)
        
        letters_set = string.ascii_letters
        metric_desc = ''.join(random.sample(letters_set, 10))
        metric.description = metric_desc
        metric.save()
        
        return JsonResponse({"msg": metric_desc})
        
    @action(methods=['post'], detail=False)
    def modify_replicaSet(self, request):
        try:
            replicaSet_num = request.data['replicaSet']
        except KeyError:
            return JsonResponse({"error": "replicaSet의 갯수를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        crd = None
        crd_file_path = 'C:/Users/User/grad-project-backend/grad-project/crd/MongoDBCommunity.yaml'
        with open(crd_file_path, 'r+') as f:
            crd = yaml.load(f, Loader=yaml.FullLoader)
            for k, v in crd.items():
                if isinstance(v, dict) and 'type' in v and v['type'] == 'ReplicaSet':
                    v['members'] = replicaSet_num
        with open(crd_file_path, 'w+') as f:
            yaml.dump(crd, f, default_flow_style=False)
        os.system("kubectl apply -f crd/MongoDBCommunity.yaml")
        return JsonResponse({"msg": "good"})