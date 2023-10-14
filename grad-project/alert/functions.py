from django.http import JsonResponse
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.response import Response
from .models import Alert

import httplib2
import json

# 호출 횟수가 10회 이상인 Unresolved Alerts에 대한 확인
def resolve_alerts():
    alerts = Alert.objects.filter(resolved=False, count__gte = 10)
    for alert in alerts:
        rule = alert.rule
        pod_name = alert.pod_name
        query = rule.query
        query_result = 0
        operator = rule.operator
        threshold = rule.threshold
        
        http = httplib2.Http()
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
            return JsonResponse({"error": "Alert Read 오류가 발생했습니다.[0]"}, status=HTTP_400_BAD_REQUEST)
        except TypeError:
            return JsonResponse({"error": "Alert Read 오류가 발생했습니다.[1]"}, status=HTTP_400_BAD_REQUEST)
        if error is None and response_dict['status'] == 'success' and response_dict['data']['result']:
            result_list = response_dict['data']['result']
            pod_found = False
            for result in result_list:
                if result['metric']['pod'] == pod_name:
                    pod_found = True
                    query_result = int(float(result['value'][1]))
            if not pod_found:
                return JsonResponse({"error": "Alert Read 오류가 발생했습니다.[2]"}, status=HTTP_400_BAD_REQUEST)
        
        if operator == 'EQUAL':
            if query_result != threshold:
                alert.resolved = True
                alert.save()
        elif operator == 'NOT_EQUAL':
            if query_result == threshold:
                alert.resolved = True
                alert.save()
        elif operator == 'GREATER':
            if query_result <= threshold:
                alert.resolved = True
                alert.save()
        elif operator == 'GREATER_EQUAL':
            if query_result < threshold:
                alert.resolved = True
                alert.save()
        elif operator == 'LESS':
            if query_result >= threshold:
                alert.resolved = True
                alert.save()
        elif operator == 'LESS_EQUAL':
            if query_result > threshold:
                alert.resolved = True
                alert.save()