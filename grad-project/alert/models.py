from django.db import models

# Create your models here.
class Rule(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField('이름', db_column='name', max_length=100)
    query = models.CharField('표현식', db_column='query', max_length=3000)
    operator = models.CharField('연산자', db_column='operator', max_length=30)
    threshold = models.IntegerField('임계값', db_column='threshold')
    severity = models.CharField('심각도', db_column='severity', max_length=50)
    description = models.CharField('설명', db_column='description', max_length=3000)
    
    class Meta:
        managed = False
        db_table = 'rule'
        verbose_name= '룰'
        verbose_name_plural='룰'
        
    def __str__(self):
        return self.name.__str__()

class Alert(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    rule = models.ForeignKey(Rule, models.DO_NOTHING, help_text = '룰', db_column='rule_id', verbose_name='룰')
    fingerprint = models.CharField('fingerprint', db_column='fingerprint', max_length=100)
    pod_name = models.CharField('pod명', db_column='pod_name', max_length=100)
    status = models.CharField('상태', db_column='status', max_length=50)
    created_at = models.DateTimeField('생성시간', help_text='생성시간',
                                        db_column='created_at', auto_now_add=True)
    resolved_at = models.DateTimeField('해결시간', help_text='해결시간',
                                        db_column='resolved_at', auto_now_add=True)
    resolved = models.BooleanField('해결 여부', help_text='해결 여부', db_column='resolved')
    
    class Meta:
        managed = False
        db_table = 'alert'
        verbose_name='알럿'
        verbose_name_plural='알럿'
        
    # def __str__(self):
    #     return self.name.__str__()