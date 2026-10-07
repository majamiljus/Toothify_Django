# Maja Miljuš 0576/2022
from django.db import models
from meds.models import Med 
from patients.models import Pat 

# Maja Miljuš 0576/2022: 
class Rating(models.Model):
    """
    Cuva komentar i ocenu od korisnika  :model:`patients.Pat` 
    za doktora :model:`meds.Med`.
    """
    id = models.AutoField(primary_key=True)
    idMed = models.ForeignKey(Med, on_delete=models.CASCADE, db_column='id_med', related_name='rating')
    idPat = models.ForeignKey(Pat, on_delete=models.CASCADE, db_column='id_pat', related_name='ratings')
    star = models.IntegerField(db_column='star', null=False)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AllInterventions(models.Model):
    """
    Cuva sve intervencije koje ordinacija moze da radi 
    """
    id = models.AutoField(primary_key=True)
    description = models.TextField(db_column='description', null=False)
    duration = models.IntegerField(db_column='duration', null=False)  
    price = models.DecimalField(db_column='price', max_digits=8, decimal_places=2, null=False, default=0.00)
    level = models.IntegerField(db_column='level', null=False, default=1)
