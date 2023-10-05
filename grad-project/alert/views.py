from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.viewsets import ModelViewSet
from .models import Rule, Alert
from .serializer import AlertSerializer
from .functions import resolve_alerts
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.serializers import Serializer

from django.core.exceptions import ObjectDoesNotExist
import yaml
import os

# Create your views here.
class AlertViewSet(ModelViewSet):
    queryset = Alert.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': AlertSerializer,
        'read': AlertSerializer,
        'webhook': AlertSerializer,
        'follow_up_2': AlertSerializer,
        'follow_up_3': AlertSerializer,
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

    def list(self, request):
        try:
            resolved = int(request.GET.get('resolved', 0))
        except:
            return JsonResponse({"error": "resolved에 0 또는 1을 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        resolve_alerts()
        alerts = Alert.objects.filter(resolved = resolved)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        resolve_alerts()
        alert = Alert.objects.get(id=pk)
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def webhook(self, request):
        try:
            alert_list = request.data['alerts']
        except KeyError:
            return JsonResponse({"error": "Webhook에서 오류가 발생하였습니다.[0]"}, status=HTTP_400_BAD_REQUEST)
        
        for alert_json in alert_list:
            try:
                alert_name = alert_json['labels']['alertname']
                pod_name = alert_json['labels']['pod']
                rule = Rule.objects.get(name = alert_name)
            except KeyError:
                return JsonResponse({"error": "Webhook에서 오류가 발생하였습니다.[1]"}, status=HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Webhook에서 오류가 발생하였습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
            
            try:
                status = alert_json['status']
                created_at = alert_json['startsAt']
            except KeyError:
                return JsonResponse({"error": "Webhook에서 오류가 발생하였습니다.[3]"}, status=HTTP_400_BAD_REQUEST)
            alert = Alert(rule = rule, pod_name = pod_name, status = status, created_at = created_at, resolved = False)
            alert.save()
        
        return JsonResponse({"msg": str(len(alert_list)) + " alerts are registered"})
    
    @action(methods=['post'], detail=False)
    def follow_up_2(self, request):
        try:
            maxIncomingConnections = request.data['maxIncomingConnections']
        except KeyError:
            return JsonResponse({"error": "maxIncomingConnections를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        crd = None
        current_path = os.getcwd()
        crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
        with open(crd_file_path, 'r+') as f:
            crd = yaml.load(f, Loader=yaml.FullLoader)
            for k, v in crd.items():
                if isinstance(v, dict) and 'additionalMongodConfig' in v:
                    v['additionalMongodConfig']['net']['maxIncomingConnections'] = maxIncomingConnections
        with open(crd_file_path, 'w+') as f:
            yaml.dump(crd, f, default_flow_style=False)
        os.system("kubectl apply -f crd/MongoDBCommunity.yaml")
        return JsonResponse({"msg": "good"})
    
    @action(methods=['post'], detail=False)
    def follow_up_3(self, request):
        try:
            replicaSet_num = request.data['replicaSet']
        except KeyError:
            return JsonResponse({"error": "replicaSet의 갯수를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        crd = None
        current_path = os.getcwd()
        crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
        with open(crd_file_path, 'r+') as f:
            crd = yaml.load(f, Loader=yaml.FullLoader)
            for k, v in crd.items():
                if isinstance(v, dict) and 'type' in v and v['type'] == 'ReplicaSet':
                    v['members'] = replicaSet_num
        with open(crd_file_path, 'w+') as f:
            yaml.dump(crd, f, default_flow_style=False)
        os.system("kubectl apply -f crd/MongoDBCommunity.yaml")
        return JsonResponse({"msg": "good"})