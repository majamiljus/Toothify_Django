#Aleksandar Pavlovic 0093/2022
#Maja Miljuš 0576/2022

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from meds.models import Med
from users.models import Notification
from index.models import AllInterventions
from datetime import time as time_cls, timedelta
from django.utils import timezone
from meds.models import Vacation, WorkTime
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

#Aleksandar Pavlovic 0093/2022 testovi:
class AdminCreateDoctorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

    def test_admin_can_open_create_doctor_page(self):
        url = reverse("users:create_doctor")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_create_doctor_creates_user_and_med(self):
        url = reverse("users:create_doctor")

        payload = {
            "username": "doktorDjango@dentasoft.com",
            "password1": "test12345",
            "password2": "test12345",
            "name": "Igor",
            "surname": "Igoric",
            "description": "Opis doktora",
            "telephone": "0657777252",
            "level_spec": 2,
            # image ne saljemo, treba default
        }

        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(User.objects.filter(username="doktorDjango@dentasoft.com").exists())
        user = User.objects.get(username="doktorDjango@dentasoft.com")

        self.assertTrue(Med.objects.filter(user=user).exists())
        med = Med.objects.get(user=user)

        self.assertEqual(med.email, "doktorDjango@dentasoft.com")
        self.assertEqual(med.name, "Igor")
        self.assertEqual(med.surname, "Igoric")
        self.assertEqual(med.level_spec, 2)
        self.assertTrue(bool(med.image)) 

class AdminDeactivateDoctorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin@example.com",
            password="pass12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

        self.doc_user = User.objects.create_user(
            username="doc@example.com",
            password="pass12345",
            is_active=True
        )
        self.med = Med.objects.create(
            user=self.doc_user,
            name="Doc",
            surname="One",
            description="desc",
            email="doc@example.com",
            telephone="061111111",
            is_active=True,
            level_spec=2,
        )

    def test_admin_deactivate_doctor_sets_med_and_user_inactive(self):
        url = reverse("users:deactivate_doctor", args=[self.med.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.med.refresh_from_db()
        self.doc_user.refresh_from_db()

        self.assertFalse(self.med.is_active)
        self.assertFalse(self.doc_user.is_active)

class AdminAddNotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

    def test_admin_can_create_notification(self):
        url = reverse("users:add_notification")
        payload = {
            "title": "Radno vreme",
            "text": "U petak skraceno radno vreme.",
            "for_patients": "on",
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(Notification.objects.filter(title="Radno vreme").exists())
        n = Notification.objects.get(title="Radno vreme")
        self.assertEqual(n.author, self.admin)
        self.assertTrue(n.for_patients)

    def test_admin_cannot_create_notification_if_missing_title_or_text(self):
        url = reverse("users:add_notification")

        resp = self.client.post(url, data={"title": "", "text": "Tekst"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

        resp = self.client.post(url, data={"title": "Naslov", "text": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

class AdminDeleteNotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

        self.n = Notification.objects.create(
            author=self.admin,
            title="Test",
            text="Test tekst",
            for_patients=False
        )

    def test_delete_notification_on_post(self):
        url = reverse("users:delete_notification", args=[self.n.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Notification.objects.filter(id=self.n.id).exists())

    def test_get_does_not_delete_notification(self):
        url = reverse("users:delete_notification", args=[self.n.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Notification.objects.filter(id=self.n.id).exists())

class AdminAddInterventionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

    def test_add_intervention_success(self):
        url = reverse("users:add_intervention")
        payload = {
            "description": "Kontrola",
            "duration": "30",
            "price": "1000.00",
            "level": "1",
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(AllInterventions.objects.filter(description="Kontrola").exists())

    def test_add_intervention_fails_if_missing_description(self):
        url = reverse("users:add_intervention")
        payload = {"description": "", "duration": "30", "price": "1000.00", "level": "1"}
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AllInterventions.objects.count(), 0)

    def test_add_intervention_fails_if_duration_not_int(self):
        url = reverse("users:add_intervention")
        payload = {"description": "Kontrola", "duration": "xx", "price": "1000.00", "level": "1"}
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AllInterventions.objects.count(), 0)

    def test_add_intervention_fails_if_level_not_int(self):
        url = reverse("users:add_intervention")
        payload = {"description": "Kontrola", "duration": "30", "price": "1000.00", "level": "xx"}
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AllInterventions.objects.count(), 0)

    def test_add_intervention_fails_if_price_not_number(self):
        url = reverse("users:add_intervention")
        payload = {"description": "Kontrola", "duration": "30", "price": "abc", "level": "1"}
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AllInterventions.objects.count(), 0)

class AdminDeleteInterventionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

        self.i = AllInterventions.objects.create(
            description="BrisanjeTest",
            duration=30,
            price=1000,
            level=1
        )

    def test_delete_intervention_on_post(self):
        url = reverse("users:delete_intervention", args=[self.i.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(AllInterventions.objects.filter(id=self.i.id).exists())

class AdminApproveVacationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="Admin",
            password="test12345",
            is_staff=True,
            is_active=True
        )
        self.client.force_login(self.admin)

        self.doc_user = User.objects.create_user(
            username="doc@dentasoft.com",
            password="test12345",
            is_active=True
        )
        self.med = Med.objects.create(
            user=self.doc_user,
            name="Doc",
            surname="Docic",
            description="opis",
            email="doc@dentasoft.com",
            telephone="069233669",
            is_active=True,
            level_spec=2,
        )

    def test_approve_vacation_sets_status_and_deletes_worktime_in_range(self):
        start = timezone.localdate() + timedelta(days=5)
        end = start + timedelta(days=2)

        vac = Vacation.objects.create(idMed=self.med, startDate=start, endDate=end, status=0)

        WorkTime.objects.create(idMed=self.med, date=start, startTime=time_cls(8, 0), endTime=time_cls(16, 0), breakTime=time_cls(12, 0))
        WorkTime.objects.create(idMed=self.med, date=end, startTime=time_cls(8, 0), endTime=time_cls(16, 0), breakTime=time_cls(12, 0))

        url = reverse("users:approve_vacation", args=[vac.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        vac.refresh_from_db()
        self.assertEqual(vac.status, 1)
        self.assertEqual(WorkTime.objects.filter(idMed=self.med, date__range=(start, end)).count(), 0)

class DoctorAddNotificationTests(TestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="doc@dentasoft.com",
            password="test12345",
            is_active=True
        )
        self.med = Med.objects.create(
            user=self.doctor_user,
            name="Doc",
            surname="Docic",
            description="opis",
            email="doc@dentasoft.com",
            telephone="061111111",
            is_active=True,
            level_spec=2,
        )
        self.client.force_login(self.doctor_user)

    def test_doctor_can_create_notification(self):
        url = reverse("meds:addNotificationMeds")  

        payload = {
            "title": "Obavestenje",
            "text": "Ordinacija radi do 14h.",  
            "for_patients": "on",
        }

        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(Notification.objects.filter(title="Obavestenje").exists())
        n = Notification.objects.get(title="Obavestenje")
        self.assertEqual(n.author, self.doctor_user)

    def test_doctor_cannot_create_notification_if_missing_title_or_text(self):
        url = reverse("meds:addNotificationMeds")  

        resp = self.client.post(url, data={"title": "", "text": "Tekst"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

        resp = self.client.post(url, data={"title": "Naslov", "text": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

class DeactivateAccountTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(
            username="user@dentasoft.com",
            password="test12345",
            is_active=True
        )
        self.client.force_login(self.u)

    def test_user_can_deactivate_account_sets_user_inactive(self):
        url = reverse("users:deactivate")
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)

        self.u.refresh_from_db()
        self.assertFalse(self.u.is_active)

#Maja Miljuš 0576/2022 testovi:
User = get_user_model()

class TestRegistracijaNovogKorisnikaSaValidnimPodacima(TestCase):
    def test_registracija_uspesna(self):
        url = reverse('users:signup')  
        data = {
            "username": "novi@korisnik.com",
            "password1": "Test1234!",
            "password2": "Test1234!",
            "name": "Maja",
            "surname": "Miljus",
            "description": "Test user",
            "telephone": "0601234567",
        }
        files = {
            "image": SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        }
        resp = self.client.post(url, data=data, files=files)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username="novi@korisnik.com").exists())

class TestRegistracijaSaPostojecomEmailAdresom(TestCase):
    def setUp(self):
        User.objects.create_user(username="postojeci@korisnik.com", password="Test1234!")

    def test_registracija_neuspesna(self):
        url = reverse('users:signup')
        data = {
            "username": "postojeci@korisnik.com",
            "password1": "Test1234!",
            "password2": "Test1234!",
            "name": "Maja",
            "surname": "Miljus",
            "description": "Test user",
            "telephone": "0601234567",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Корисник са тим корисничким именом већ постоји.")

class TestRegistracijaPogresnaPotvrdaLozinke(TestCase):
    def test_registracija_neuspesna(self):
        url = reverse('users:signup')
        payload = {
            'username': 'pogresnalozinka@korisnik.com',
            'password1': 'Test12345',
            'password2': 'Test123',
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='pogresnalozinka@korisnik.com').exists())

class TestRegistracijaObaveznoPoljeNijeUneto(TestCase):
    def test_obavezno_polje_prazno(self):
        url = reverse('users:signup')
        payload = {
            'username': '',
            'password1': 'Test12345',
            'password2': 'Test12345',
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.exists())

class TestRegistracijaTelefonImaManjeOd9Cifara(TestCase):
    def test_telefon_too_short(self):
        url = reverse('users:signup')
        payload = {
            'username': 'telefon@korisnik.com',
            'password1': 'Test12345',
            'password2': 'Test12345',
            'telephone': '06123'
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='telefon@korisnik.com').exists())

class TestRegistracijaTelefonImaViseOd11Cifara(TestCase):
    def test_telefon_too_long(self):
        url = reverse('users:signup')
        payload = {
            'username': 'telefon@korisnik.com',
            'password1': 'Test12345',
            'password2': 'Test12345',
            'telephone': '061234567890123'
        }
        resp = self.client.post(url, data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='telefon@korisnik.com').exists())

class TestPrijavaPacijenta(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username='pacijent@dentasoft.com', password='pass12345')

    def test_login_pacijent(self):
        url = reverse('users:login')
        resp = self.client.post(url, data={'username': 'pacijent@dentasoft.com', 'password': 'pass12345'})
        self.assertEqual(resp.status_code, 302)

class TestPrijavaDoktora(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username='doktor@dentasoft.com', password='pass12345')
        self.med = Med.objects.create(user=self.u, name='Petar', surname='Petrovic', email='doktor@dentasoft.com', telephone='061111111')

    def test_login_doktor(self):
        url = reverse('users:login')
        resp = self.client.post(url, data={'username': 'doktor@dentasoft.com', 'password': 'pass12345'})
        self.assertEqual(resp.status_code, 302)

class TestPrijavaAdmina(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin@dentasoft.com', password='pass12345', is_staff=True)

    def test_login_admin(self):
        url = reverse('users:login')
        resp = self.client.post(url, data={'username': 'admin@dentasoft.com', 'password': 'pass12345'})
        self.assertEqual(resp.status_code, 302)

class TestPrijavaSaPogresnomEmailAdresom(TestCase):
    def setUp(self):
        User.objects.create_user(username="korisnik@dentasoft.com", password="Test1234!")

    def test_prijava_pogresan_email(self):
        url = reverse('users:login')
        data = {
            "username": "nepostoji@dentasoft.com",
            "password": "Test1234!"
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Молим вас унесите исправно корисничко име и лозинку")
        
class TestPrijavaSaPogresnomLozinkom(TestCase):
    def setUp(self):
        User.objects.create_user(username="korisnik@dentasoft.com", password="Test1234!")

    def test_login_fail_wrong_password(self):
        url = reverse('users:login')
        data = {
            "username": "korisnik@dentasoft.com",
            "password": "PogresnaLozinka"
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Молим вас унесите исправно корисничко име и лозинку")

class TestResetLozinke(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username='reset@dentasoft.com', password='pass12345')

    def test_reset_password_view_accessible(self):
        url = reverse('users:password_reset')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)