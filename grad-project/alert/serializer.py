from rest_framework import serializers
from .models import Rule, Alert, RuleMetric

class RuleMetricSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(help_text='id')
    category_id = serializers.SerializerMethodField(help_text='카테고리')
    name = serializers.SerializerMethodField(help_text='이름')
    class Meta:
        model = RuleMetric
        fields = ['id', 'category_id', 'name']
    
    def get_id(self, instance):
        return instance.metric.id
    def get_category_id(self, instance):
        return instance.metric.category.id
    def get_name(self, instance):
        return instance.metric.name

class RuleSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField(help_text='알럿 개수')
    metrics = serializers.SerializerMethodField(help_text='메트릭')
    class Meta:
        model = Rule
        fields = ['id', 'name', 'query', 'operator', 'threshold', 'severity', 'description', 'count', 'relevant_key_name', 'metrics']
        
    def get_count(self, instance):
        return Alert.objects.filter(rule__id = instance.id).count()

    def get_metrics(self, instance):
        rule_metric_instances = RuleMetric.objects.filter(rule__id = instance.id)
        return RuleMetricSerializer(rule_metric_instances, many = True).data
    
class AlertSerializer(serializers.ModelSerializer):
    rule = RuleSerializer(many = False)
    class Meta:
        model = Alert
        fields = ['id', 'fingerprint', 'pod_name', 'created_at', 'resolved_at', 'resolved', 'count', 'rule']