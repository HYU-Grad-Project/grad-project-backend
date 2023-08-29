from rest_framework import serializers
from .models import Metric

class MetricSerializer(serializers.ModelSerializer):
    
    category_name = serializers.SerializerMethodField(help_text='카테고리명')
    
    class Meta:
        model = Metric
        fields = ['id', 'category_name', 'name', 'description']
        
    def get_category_name(self, instance):
        return instance.category.name