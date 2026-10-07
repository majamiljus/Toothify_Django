#Minja Krivokapic 0615/2022 
#Irina Majstorovic 2022/0518
#Aleksandar Pavlovic 0093/2022
#Maja Miljus 0576/2022
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

#Minja Krivokapic 0615/2022:
#Aleksandar Pavlovic 0093/2022:
class Med(models.Model):
    """
    Model čuva osnovne podatke o doktoru
    - lične podatke (ime, prezime, email, telefon)
    - opis i nivo specijalizacije
    - profilnu sliku
    - status verifikacije i aktivnost naloga
    - informacije o godišnjem odmoru (ukupan broj dana, preostali dani i godina na koju se odnose)
    """
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="med"
    )
    is_active = models.BooleanField(default=True)
    name = models.CharField(db_column='name', max_length=30, null=False)
    surname = models.CharField(db_column='surname', max_length=30, null=False)
    description = models.CharField(db_column='description', max_length=200, null=False)
    email = models.CharField(db_column='email', max_length=30, null=False)
    telephone = models.CharField(db_column='telephone', max_length=30, null=False)
    level_spec = models.IntegerField(db_column='level_spec', null=False, default=1)
    image = models.ImageField(upload_to='images', null=True, blank=True, default='images/default.jpg') 
    is_verified = models.BooleanField(default=False)
    vacation_days_total = models.PositiveSmallIntegerField(default=20)
    vacation_days_remaining = models.PositiveSmallIntegerField(default=20)
    vacation_days_year = models.PositiveSmallIntegerField(default=timezone.now().year)

#Minja Krivokapic 0615/2022:
class Vacation(models.Model):
    """
    Model čuva podatke o periodu odsustva doktora (:model:`meds.Med`),
    uključujući datum početka i završetka odmora, kao i status zahteva.
    """
    id = models.AutoField(primary_key=True)
    idMed = models.ForeignKey(
        Med,
        on_delete=models.CASCADE,
        db_column='id_med',
        related_name='vacations'
    )
    startDate = models.DateField(db_column='start_date', null=False)
    endDate = models.DateField(db_column='end_date', null=False)
    status = models.IntegerField(db_column='status', null=False, default=0)

#Minja Krivokapic 0615/2022:
#Irina Majstorovic 2022/0518:
class WorkTime(models.Model):
    """
    Predstavlja radno vreme doktora za odredjeni datum.
    """
    id = models.AutoField(primary_key=True)
    idMed = models.ForeignKey(
        Med,
        on_delete=models.CASCADE,
        db_column='id_med',
        related_name='work_times'
    )
    date = models.DateField(db_column='date', null=False)
    startTime = models.TimeField(db_column='start_time', null=False)
    endTime = models.TimeField(db_column='end_time', null=False)
    breakTime = models.TimeField(db_column='break_time', null=False, default='12:00')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['idMed', 'date'], name='unique_override_per_date_and_med')
        ]

#Maja Miljus 0576/2022:
class SpecializationUpgradeRequest(models.Model):
    """
    Model koji predstavlja zahtev lekara za unapredjenje specijalizacije.
    Ima vezu sa adminom koji odlucuje (:model:`auth.User`) i lekarom koji salje zahtev (:model:`meds.Med`).
    """
    STATUS_REJECTED = -1
    STATUS_PENDING = 0
    STATUS_APPROVED = 1

    med = models.ForeignKey(Med, on_delete=models.CASCADE, related_name="spec_requests")
    requested_level = models.PositiveSmallIntegerField()
    status = models.SmallIntegerField(default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    admin_note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["med"],
                #condition=Q(status=STATUS_PENDING),
                condition=Q(status=0),
                name="unique_pending_spec_request_per_med"
            )
        ]

    def __str__(self):
        return f"{self.med.email} -> {self.requested_level} (status={self.status})"

