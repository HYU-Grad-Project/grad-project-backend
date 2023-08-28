from django.db import models

# Create your models here.
class Category(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField('이름', db_column='name', max_length=500)
    description = models.CharField('설명', db_column='description', max_length=3000)
    
    class Meta:
        managed = False
        db_table = 'category'
        verbose_name='카테고리'
        verbose_name_plural='카테고리'
        
    def __str__(self):
        return self.name.__str__()

class Metric(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    category = models.ForeignKey(Category, models.DO_NOTHING, help_text = '카테고리', db_column='category_id', verbose_name='카테고리')
    name = models.CharField('이름', db_column='name', max_length=500)
    description = models.CharField('설명', db_column='description', max_length=3000)
    
    class Meta:
        managed = False
        db_table = 'metric'
        verbose_name='메트릭'
        verbose_name_plural='메트릭'
        
    def __str__(self):
        return self.name.__str__()