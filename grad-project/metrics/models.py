from django.db import models

# Create your models here.
class Metrics(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField('이름', db_column='name', max_length=500)
    description = models.CharField('설명', db_column='description', max_length=3000)
    
    class Meta:
        managed = False
        db_table = 'metrics'
        verbose_name='메트릭'
        verbose_name_plural='메트릭'
        
    def __str__(self):
        return self.name.__str__()