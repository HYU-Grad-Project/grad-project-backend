from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.viewsets import ModelViewSet
from .models import Rule, Alert
from .serializer import AlertSerializer, RuleSerializer
from .functions import resolve_alerts
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.serializers import Serializer

from django.core.exceptions import ObjectDoesNotExist
import yaml
import os
import httplib2
import json

# Create your views here.
class AlertViewSet(ModelViewSet):
    queryset = Alert.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': AlertSerializer,
        'read': AlertSerializer,
        'webhook': AlertSerializer,
        'advice': AlertSerializer,
        'follow_up': AlertSerializer,
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
        try:
            rule_id = int(request.GET.get('rule_id', 0))
        except:
            return JsonResponse({"error": "rule_id를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        
        resolve_alerts()
        
        if rule_id == 0:
            alerts = Alert.objects.filter(resolved = resolved)
        else:
            alerts = Alert.objects.filter(resolved = resolved, rule__id = rule_id)
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
                resolved_at = alert_json['endsAt']
                fingerprint = alert_json['fingerprint']
            except KeyError:
                return JsonResponse({"error": "Webhook에서 오류가 발생하였습니다.[3]"}, status=HTTP_400_BAD_REQUEST)
            
            if status == 'firing':
                try:
                    prev_alert = Alert.objects.get(fingerprint=fingerprint)
                    prev_alert.count += 1
                    prev_alert.save()
                except ObjectDoesNotExist:
                    alert = Alert(rule = rule, fingerprint = fingerprint, pod_name = pod_name, 
                                created_at = created_at, resolved = False, count = 1)
                    alert.save()
            elif status == 'resolved':
                try:
                    alert = Alert.objects.get(fingerprint=fingerprint)
                except ObjectDoesNotExist:
                    return JsonResponse({"error": "등록되지 않은 alert이 존재합니다."})
                alert.resolved = True
                alert.resolved_at = resolved_at
                alert.save()
        return JsonResponse({"msg": str(len(alert_list)) + " alerts are registered(or modified)"})
    
    @action(methods=['post'], detail=False)
    def advice(self, request):
        try:
            alert_id = request.data['alert_id']
        except KeyError:
            return JsonResponse({"error": "alert_id를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        alert = Alert.objects.get(id=alert_id)
        rule = alert.rule
        pod_name = alert.pod_name
        threshold = rule.threshold
        
        relevant_key_name = rule.relevant_key_name
        current_value = 0
        recommended_value = 0
        mongodb_connections_current = 0
        
        if rule.id == 2:
            crd = None
            current_path = os.getcwd()
            crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'additionalMongodConfig' in v:
                        current_value = int(float(v['additionalMongodConfig']['net']['maxIncomingConnections']))

            http = httplib2.Http()
            prometheus_ip = os.environ.get("PROMETHEUS_IP", 'http://127.0.0.1')
            url = prometheus_ip + ":9090/api/v1/query?query=" + "mongodb_connections_current"
            response, response_body = http.request(url, method="GET", 
                                            headers={'Content-Type': 'application/json;'})
            response_str = response_body.decode('utf-8')
            response_dict = None
            error = None
            try:
                response_dict = json.loads(response_str)
            except ValueError:
                return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[0]"}, status=HTTP_400_BAD_REQUEST)
            except TypeError:
                return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[1]"}, status=HTTP_400_BAD_REQUEST)
            if error is None and response_dict['status'] == 'success' and response_dict['data']['result']:
                result_list = response_dict['data']['result']
                pod_found = False
                for result in result_list:
                    if result['metric']['pod'] == pod_name:
                        pod_found = True
                        mongodb_connections_current = int(float(result['value'][1]))
                if not pod_found:
                    return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
            
            # mongodb_connections_current 값을 기준으로 Rule의 threshold보다 5 % 적은 값을 갖도록 recommended_value 설정
            recommended_value = int(mongodb_connections_current * 100 / (threshold - 5))
        
        elif rule.id == 3:
            crd = None
            current_path = os.getcwd()
            crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'type' in v and v['type'] == 'ReplicaSet':
                        current_value = int(float(v['members']))
            
            recommended_value = current_value + 1
        
        elif rule.id == 4:
            crd = None
            current_path = os.getcwd()
            crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'additionalMongodConfig' in v:
                        current_value = float(v['additionalMongodConfig']['storage']['wiredTiger']['engineConfig']['cacheSizeGB'])
            
            http = httplib2.Http()
            prometheus_ip = os.environ.get("PROMETHEUS_IP", 'http://127.0.0.1')
            url = prometheus_ip + ":9090/api/v1/query?query=" + "mongodb_wiredTiger_cache_bytes_currently_in_the_cache"
            response, response_body = http.request(url, method="GET", 
                                            headers={'Content-Type': 'application/json;'})
            response_str = response_body.decode('utf-8')
            response_dict = None
            error = None
            try:
                response_dict = json.loads(response_str)
            except ValueError:
                return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[0]"}, status=HTTP_400_BAD_REQUEST)
            except TypeError:
                return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[1]"}, status=HTTP_400_BAD_REQUEST)
            if error is None and response_dict['status'] == 'success' and response_dict['data']['result']:
                result_list = response_dict['data']['result']
                pod_found = False
                for result in result_list:
                    if result['metric']['pod'] == pod_name:
                        pod_found = True
                        mongodb_wiredTiger_cache_bytes_currently_in_the_cache = int(float(result['value'][1]))
                if not pod_found:
                    return JsonResponse({"error": "Advice 생성 중 오류가 발생했습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
            
            # mongodb_wiredTiger_cache_bytes_currently_in_the_cache 값을 기준으로 Rule의 threshold보다 0.1 % 적은 값을 갖도록 recommended_value 설정
            recommended_value = int(mongodb_wiredTiger_cache_bytes_currently_in_the_cache * 100 / (threshold - 0.1)) / 10 ** 9
        
        else:
            return JsonResponse({"error": "존재하지 않는 Rule입니다. Alert의 Rule을 확인해주세요."}, status=HTTP_400_BAD_REQUEST)
        
        response_dict = {}
        response_dict['relevant_key_name'] = relevant_key_name
        response_dict['current_value'] = current_value
        response_dict['recommended_value'] = recommended_value
        return JsonResponse(response_dict)
    
    @action(methods=['post'], detail=False)
    def follow_up(self, request):
        try:
            alert_id = request.data['alert_id']
        except KeyError:
            return JsonResponse({"error": "alert_id를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        try:
            value = request.data['value']
        except KeyError:
            return JsonResponse({"error": "value를 입력해주세요."}, status=HTTP_400_BAD_REQUEST)
        
        rule = Alert.objects.get(id=alert_id).rule
        crd = None
        current_path = os.getcwd()
        crd_file_path = current_path + '/crd/MongoDBCommunity.yaml'
        
        if rule.id == 2:
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'additionalMongodConfig' in v:
                        v['additionalMongodConfig']['net']['maxIncomingConnections'] = value
            with open(crd_file_path, 'w+') as f:
                yaml.dump(crd, f, default_flow_style=False)
        
        elif rule.id == 3:
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'type' in v and v['type'] == 'ReplicaSet':
                        v['members'] = value
            with open(crd_file_path, 'w+') as f:
                yaml.dump(crd, f, default_flow_style=False)
        
        elif rule.id == 4:
            with open(crd_file_path, 'r+') as f:
                crd = yaml.load(f, Loader=yaml.FullLoader)
                for k, v in crd.items():
                    if isinstance(v, dict) and 'additionalMongodConfig' in v:
                        v['additionalMongodConfig']['storage']['wiredTiger']['engineConfig']['cacheSizeGB'] = value
            with open(crd_file_path, 'w+') as f:
                yaml.dump(crd, f, default_flow_style=False)
        
        else:
            return JsonResponse({"error": "존재하지 않는 Rule입니다. Alert의 Rule을 확인해주세요."}, status=HTTP_400_BAD_REQUEST)
        
        os.system("kubectl apply -f crd/MongoDBCommunity.yaml")
        
        return JsonResponse({"msg": rule.name + "에 대한 후속 조치가 완료되었습니다."})
    
class RuleViewSet(ModelViewSet):
    queryset = Rule.objects.all()
    permission_classes = [permissions.AllowAny]
    
    serializer_classes = {
        'list': RuleSerializer,
        'read': RuleSerializer,
        'monitor': RuleSerializer,
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
    def monitor(self, request):
        rule_id = int(request.GET.get('rule_id', 0))
        http = httplib2.Http()
        try:
            rule = Rule.objects.get(id=rule_id)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "오류가 발생했습니다.[4]"}, status=HTTP_400_BAD_REQUEST)
        query = rule.query.replace("+", "%2B") if rule is not None else ''

        prometheus_ip = os.environ.get("PROMETHEUS_IP", 'http://127.0.0.1')
        url = prometheus_ip + ":9090/api/v1/query?query=" + query
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
                    origin = result['metric']['instance']
                    value = result['value'][1]
                except KeyError:
                    return JsonResponse({"error": "오류가 발생했습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
                pod_value = {"pod_name": pod_name, "origin": origin, "value": value}
                pod_value_list.append(pod_value)
            return Response(pod_value_list)
        else:
            return JsonResponse({"error": "오류가 발생했습니다.[3]"}, status=HTTP_400_BAD_REQUEST)