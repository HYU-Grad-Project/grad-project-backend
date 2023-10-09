from rest_framework import serializers
from .models import Rule, Alert

class AlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.SerializerMethodField(help_text='룰 이름')
    class Meta:
        model = Alert
        fields = ['id', 'rule_name', 'fingerprint', 'pod_name', 'created_at', 'resolved_at', 'resolved', 'count']
        
    def get_rule_name(self, instance):
        return instance.rule.name
    
class RuleSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField(help_text='알럿 개수')
    class Meta:
        model = Rule
        fields = ['id', 'name', 'query', 'operator', 'threshold', 'severity', 'description', 'count']
        
    def get_count(self, instance):
        return Alert.objects.filter(rule__id = instance.id).count()