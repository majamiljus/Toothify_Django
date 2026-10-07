#Irina Majstorovič 2022/0518 
#Minja Krivokapic 2022/0615
from django.db import models
from meds.models import Med
from django.utils import timezone
from django.contrib.auth.models import User

class Pat(models.Model):
    """
    Model koji predstavlja pacijenta.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pat_profile')
    id = models.AutoField(primary_key=True)
    name = models.CharField(db_column='name', max_length=30, null=False)
    surname = models.CharField(db_column='surname', max_length=30, null=False)
    description = models.CharField(db_column='description', max_length=200, null=False)
    secretNotes = models.CharField(db_column='secretNotes', max_length=200, null=False)
    email = models.CharField(db_column='email', max_length=30, null=False)
    telephone = models.CharField(db_column='telephone', max_length=30, null=False)
    image = models.ImageField(upload_to='images', null=True, blank=True,default='images/defaultP.jpg')

class Intervention(models.Model):
    """
    Model koji predstavlja jednu intervenciju pacijenta kod stomatologa.
    """
    id = models.AutoField(primary_key=True)
    idMed = models.ForeignKey(Med, on_delete=models.CASCADE, db_column='id_med', related_name='interventions')
    idPat = models.ForeignKey(Pat, on_delete=models.CASCADE, db_column='id_pat', related_name='interventions')
    description = models.TextField(db_column='description', null=False)
    duration = models.IntegerField(db_column='duration', null = False)
    status = models.CharField(db_column='status', max_length=50, null=False, default='Zakazan')
    date = models.DateField(db_column='date', default=timezone.now)  
    time = models.TimeField(db_column='time', default=timezone.now) 
