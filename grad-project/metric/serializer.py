from rest_framework import serializers
from .models import Category, Metric

class CategoryListReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
        
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class MetricListReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ['id', 'name']

class MetricSerializer(serializers.ModelSerializer):
    
    category_name = serializers.SerializerMethodField(help_text='카테고리명')
    
    class Meta:
        model = Metric
        fields = ['id', 'category_name', 'name', 'description']
        
    def get_category_name(self, instance):
        return instance.category.name