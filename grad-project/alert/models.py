from django.db import models
from metric.models import Metric

# Create your models here.
class Rule(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField('이름', db_column='name', max_length=100)
    query = models.CharField('표현식', db_column='query', max_length=3000)
    operator = models.CharField('연산자', db_column='operator', max_length=30)
    threshold = models.FloatField('임계값', db_column='threshold')
    severity = models.CharField('심각도', db_column='severity', max_length=50)
    description = models.CharField('설명', db_column='description', max_length=3000)
    relevant_key_name = models.CharField('CRD key 값', db_column='relevant_key_name', max_length=100)
    
    class Meta:
        managed = False
        db_table = 'rule'
        verbose_name= '룰'
        verbose_name_plural='룰'
        
    def __str__(self):
        return self.name.__str__()

class RuleMetric(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    rule = models.ForeignKey(Rule, models.DO_NOTHING, help_text = '룰', db_column='rule_id', verbose_name='룰')
    metric = models.ForeignKey(Metric, models.DO_NOTHING, help_text = '메트릭', db_column='metric_id', verbose_name='메트릭')
    
    class Meta:
        managed = False
        db_table = 'rule_metric'
        verbose_name='룰_알럿'
        verbose_name_plural='룰 알럿'
    
class Alert(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    rule = models.ForeignKey(Rule, models.DO_NOTHING, help_text = '룰', db_column='rule_id', verbose_name='룰')
    fingerprint = models.CharField('fingerprint', db_column='fingerprint', max_length=100)
    pod_name = models.CharField('pod명', db_column='pod_name', max_length=100)
    created_at = models.DateTimeField('생성시간', help_text='생성시간',
                                        db_column='created_at')
    resolved_at = models.DateTimeField('해결시간', help_text='해결시간',
                                        db_column='resolved_at')
    resolved = models.BooleanField('해결 여부', help_text='해결 여부', db_column='resolved')
    count = models.IntegerField('발생 횟수', db_column='count')
    
    class Meta:
        managed = False
        db_table = 'alert'
        verbose_name='알럿'
        verbose_name_plural='알럿'
        
    # def __str__(self):
    #     return self.name.__str__()