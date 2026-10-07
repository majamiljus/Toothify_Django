#Irina Majstorovič 2022/0518
from datetime import timedelta, time as time_cls, date as date_cls
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.messages import get_messages
from meds.models import Med, WorkTime
from patients.models import Pat, Intervention
from index.models import AllInterventions

def next_monday(d: date_cls) -> date_cls:
    days_ahead = (0 - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return d + timedelta(days=days_ahead)

class PatientSchedulingTests(TestCase):
    def setUp(self):
        self.user_doc = User.objects.create_user(username="doc", password="pass123")
        self.med = Med.objects.create(
            user=self.user_doc,
            name="Doc",
            surname="One",
            description="desc",
            email="doc@example.com",
            telephone="061111111",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=5,
        )

        self.user_pat = User.objects.create_user(username="pat", password="pass123")
        self.pat = Pat.objects.create(
            user=self.user_pat,
            name="Pat",
            surname="One",
            description="desc",
            secretNotes="secret",
            email="pat@example.com",
            telephone="060000000",
        )

        self.int_type = AllInterventions.objects.create(
            description="Kontrola",
            duration=30,
            price=1000,
            level=1
        )

        today = timezone.localdate()
        self.start_date = next_monday(today)
        self.end_date = self.start_date + timedelta(days=13)
        self.good_date = self.start_date  # monday

        WorkTime.objects.create(
            idMed=self.med,
            date=self.good_date,
            startTime=time_cls(8, 0),
            endTime=time_cls(16, 0),
            breakTime=time_cls(12, 0),
        )

        self.client.force_login(self.user_pat)

    def test_patient_successfully_schedules_intervention(self):
        url = reverse("patients:med", args=[self.med.id])
        resp = self.client.post(url, data={
            "intervention": str(self.int_type.id),
            "date": self.good_date.strftime("%Y-%m-%d"),
            "time": "10:00",
        })
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(Intervention.objects.filter(
            idMed=self.med,
            idPat=self.pat,
            date=self.good_date,
            time=time_cls(10, 0),
            status="Zakazan"
        ).exists())




    def test_patient_cannot_schedule_outside_working_hours_last_possible_time_message(self):
        # work ends 16:00, duration 30 => poslednji start 15:30
        url = reverse("patients:med", args=[self.med.id])
        resp = self.client.post(url, data={
            "intervention": str(self.int_type.id),
            "date": self.good_date.strftime("%Y-%m-%d"),
            "time": "15:40",
        })
        self.assertContains(resp, "Poslednji mogući termin")
        self.assertContains(resp, "15:30")
        self.assertFalse(Intervention.objects.filter(idMed=self.med, date=self.good_date, time=time_cls(15, 40)).exists())

    def test_patient_cannot_schedule_during_break(self):
        # break 12:00-12:30, duration 30, termin u 12:10 upada u pauzu
        url = reverse("patients:med", args=[self.med.id])
        resp = self.client.post(url, data={
            "intervention": str(self.int_type.id),
            "date": self.good_date.strftime("%Y-%m-%d"),
            "time": "12:10",
        })
        self.assertContains(resp, "Lekar ima pauzu")
        self.assertFalse(Intervention.objects.filter(idMed=self.med, date=self.good_date, time=time_cls(12, 10)).exists())

    def test_patient_cancel_intervention_not_allowed_today_or_tomorrow(self):
        # napravi intervenciju za sutra
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        inter = Intervention.objects.create(
            idMed=self.med,
            idPat=self.pat,
            description=self.int_type.description,
            duration=self.int_type.duration,
            status="Zakazan",
            date=tomorrow,
            time=time_cls(10, 0),
        )

        url = reverse("patients:cancel_intervention", args=[inter.id])
        resp = self.client.post(url, follow=True)

        msgs = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any("Ne možete otkazati dan pre termina" in m for m in msgs))

        inter.refresh_from_db()
        self.assertEqual(inter.status, "Zakazan")


