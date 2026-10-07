#Minja Krivokapic 0615/2022
import json
from datetime import timedelta, time as time_cls
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from meds.models import Med
from patients.models import Pat, Intervention
from index.models import Rating


#Minja Krivokapic 0615/2022:
class AboutPageTests(TestCase):
    def setUp(self):
        self.u_doc1 = User.objects.create_user(username="doc1", password="pass123")
        self.doc1 = Med.objects.create(
            user=self.u_doc1,
            name="Marko",
            surname="Maric",
            description="Opis",
            email="doc1@dentasoft.com",
            telephone="0652222555",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=2,
        )

        # Doctor 2 (will get rating)
        self.u_doc2 = User.objects.create_user(username="doc2", password="pass123")
        self.doc2 = Med.objects.create(
            user=self.u_doc2,
            name="Stefan",
            surname="Stefic",
            description="Opis",
            email="doc2@dentasoft.com",
            telephone="0637775588",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=3,
        )

        self.u_pat = User.objects.create_user(username="pat1", password="pass123")
        self.pat = Pat.objects.create(
            user=self.u_pat,
            name="Milica",
            surname="Micic",
            description="Opis",
            secretNotes="Tajni Opis",
            email="pat@dentasoft.com",
            telephone="0625888777",
        )

        Rating.objects.create(idMed=self.doc2, idPat=self.pat, star=5, comment="Odlicno")

    def test_about_page_returns_200_and_contains_doctors(self):
        url = reverse("index:about")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("doctors", resp.context)

        doctors = list(resp.context["doctors"])
        self.assertTrue(any(d.id == self.doc1.id for d in doctors))
        self.assertTrue(any(d.id == self.doc2.id for d in doctors))

    def test_about_page_marks_unrated_doctor_as_neocenjen(self):
        url = reverse("index:about")
        resp = self.client.get(url)
        doctors = list(resp.context["doctors"])

        d1 = next(d for d in doctors if d.id == self.doc1.id)
        d2 = next(d for d in doctors if d.id == self.doc2.id)

        self.assertEqual(d1.avg_rating_display, "neocenjen")
        self.assertIn("/ 5", d2.avg_rating_display)

class SaveRatingAndCommentTests(TestCase):
    def setUp(self):
        self.u_doc = User.objects.create_user(username="doc", password="pass123")
        self.doc = Med.objects.create(
            user=self.u_doc,
            name="Igor",
            surname="Igic",
            description="Opis",
            email="doc@dentasoft.com",
            telephone="061111111",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=2,
        )

        self.u_pat = User.objects.create_user(username="pat", password="pass123")
        self.pat = Pat.objects.create(
            user=self.u_pat,
            name="Ilija",
            surname="Ilic",
            description="Opis",
            secretNotes="Tajni opis",
            email="pat@dentasoft.com",
            telephone="0652222777",
        )

        self.inter = Intervention.objects.create(
            idMed=self.doc,
            idPat=self.pat,
            description="Kontrola",
            duration=30,
            status="Zavrsen",
            date=timezone.localdate() - timedelta(days=1),
            time=time_cls(10, 0),
        )

    def test_save_rating_rejects_non_post(self):
        url = reverse("index:save_rating")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["success"])

    def test_save_rating_creates_rating_with_comment(self):
        self.client.force_login(self.u_pat)
        url = reverse("index:save_rating")

        payload = {
            "intervention_id": self.inter.id,
            "med_id": self.doc.id,  
            "star": 4,
            "comment": "Sve je bilo korektno.",
        }

        resp = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["updated"])  

        r = Rating.objects.get(idMed=self.doc, idPat=self.pat)
        self.assertEqual(r.star, 4)
        self.assertEqual(r.comment, "Sve je bilo korektno.")

    def test_save_rating_updates_existing_rating(self):
        self.client.force_login(self.u_pat)
        url = reverse("index:save_rating")

        self.client.post(
            url,
            data=json.dumps({
                "intervention_id": self.inter.id,
                "med_id": self.doc.id,
                "star": 2,
                "comment": "Nije bilo bas sjajno.",
            }),
            content_type="application/json",
        )

        resp2 = self.client.post(
            url,
            data=json.dumps({
                "intervention_id": self.inter.id,
                "med_id": self.doc.id,
                "star": 5,
                "comment": "Ispravili su, sada je odlicno.",
            }),
            content_type="application/json",
        )

        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertTrue(data2["success"])
        self.assertTrue(data2["updated"])  

        self.assertEqual(Rating.objects.filter(idMed=self.doc, idPat=self.pat).count(), 1)
        r = Rating.objects.get(idMed=self.doc, idPat=self.pat)
        self.assertEqual(r.star, 5)
        self.assertEqual(r.comment, "Ispravili su, sada je odlicno.")
