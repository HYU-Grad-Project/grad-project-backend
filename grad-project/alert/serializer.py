from rest_framework import serializers
from .models import Rule, Alert

class AlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.SerializerMethodField(help_text='룰 이름')
    class Meta:
        model = Alert
        fields = ['id', 'rule_name', 'pod_name', 'status', 'created_at', 'resolved']
        
    def get_rule_name(self, instance):
        return instance.rule.name