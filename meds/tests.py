#Irina Majstorovic 0518/2022
#Minja Krivokapic 0615/2022
from datetime import timedelta, time as time_cls
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from meds.models import Med, Vacation
from patients.models import Pat, Intervention
from index.models import AllInterventions
from meds.views import vacation as med_request_vacation_view
from meds.views import deleteVacation as med_cancel_vacation_view
from meds.views import cancelIntervention as med_cancel_intervention_view
from datetime import timedelta, time as time_cls
import unittest
from django.urls import reverse
from django.contrib.messages import get_messages
from meds.models import SpecializationUpgradeRequest

#Irina Majstorovic 0518/2022:

class MedControllersTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user_doc = User.objects.create_user(username="doc", password="pass123")
        self.med = Med.objects.create(
            user=self.user_doc,
            name="Doc",
            surname="One",
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
            email="pat@example.com",
            telephone="060000000"
        )

        self.int_type = AllInterventions.objects.create(
            description="Kontrola",
            duration=30,
            price=1000,
            level=1
        )

    def test_med_can_request_vacation_saved_pending(self):
        """
        Podosenje yahteva ya odmor od strane stomatologa
        """

        start = timezone.localdate() + timedelta(days=20)
        end = start + timedelta(days=2)

        req = self.factory.post("/meds/vacation", data={
            "startDate": start.strftime("%Y-%m-%d"),
            "endDate": end.strftime("%Y-%m-%d"),
        })
        req.user = self.user_doc

        resp = med_request_vacation_view(req)
        self.assertEqual(resp.status_code, 302)

        self.assertTrue(
            Vacation.objects.filter(
                idMed=self.med,
                startDate=start,
                endDate=end,
                status=0
            ).exists()
        )

    def test_med_can_cancel_vacation_deletes_from_db(self):
        """
        Otkazivanje odmora → briše se iz baze, tj otkazivanje odmora dok jos uvek nije potvrdjen
        """
        start = timezone.localdate() + timedelta(days=20)
        end = start + timedelta(days=2)

        vac = Vacation.objects.create(idMed=self.med, startDate=start, endDate=end, status=0)

        req = self.factory.post(f"/meds/deleteVacation/{vac.id}/")
        req.user = self.user_doc

        resp = med_cancel_vacation_view(req, vac.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Vacation.objects.filter(id=vac.id).exists())

    def test_med_cancel_intervention_marks_canceled(self):
        """
        Testiranje otkazivanje odmora nakon sto je odobren
        """
        when = timezone.localdate() + timedelta(days=3)

        inter = Intervention.objects.create(
            idMed=self.med,
            idPat=self.pat,
            description="Kontrola",
            duration=30,
            status="Zakazan",
            date=when,
            time=time_cls(10, 0)
        )

        req = self.factory.get(f"/meds/cancelIntervention/{inter.id}/")
        req.user = self.user_doc

        resp = med_cancel_intervention_view(req, inter.id)
        self.assertEqual(resp.status_code, 302)

        inter.refresh_from_db()
        self.assertEqual(inter.status, "Otkazan")

class MedCancelInterventionDoctorTests(TestCase):
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

        self.client.force_login(self.user_doc)

    def test_doctor_cancel_intervention_sets_status_otkazan(self):
        when = timezone.localdate() + timedelta(days=3)

        inter = Intervention.objects.create(
            idMed=self.med,
            idPat=self.pat,
            description=self.int_type.description,
            duration=self.int_type.duration,
            status="Zakazan",
            date=when,
            time=time_cls(10, 0),
        )

        url = reverse("meds:cancelIntervention", args=[inter.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        inter.refresh_from_db()
        self.assertEqual(inter.status, "Otkazan")

    def test_doctor_cancel_nonexistent_intervention_redirects(self):
        url = reverse("meds:cancelIntervention", args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    @unittest.expectedFailure
    def test_spec_doctor_cannot_cancel_past_intervention(self):
        # Spec: radnik može izbrisati samo termine u budućnosti :contentReference[oaicite:2]{index=2}
        when = timezone.localdate() - timedelta(days=1)

        inter = Intervention.objects.create(
            idMed=self.med,
            idPat=self.pat,
            description=self.int_type.description,
            duration=self.int_type.duration,
            status="Zakazan",
            date=when,
            time=time_cls(10, 0),
        )

        url = reverse("meds:cancelIntervention", args=[inter.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        inter.refresh_from_db()
        self.assertEqual(inter.status, "Zakazan")


#Minja Krivokapic 0615/2022:

class EditPatientNotesTests(TestCase):
    def setUp(self):
        self.u_doc = User.objects.create_user(username="doc_notes", password="pass123")
        self.doc = Med.objects.create(
            user=self.u_doc,
            name="Marko",
            surname="Maric",
            description="Opis",
            email="doc_notes@dentasoft.com",
            telephone="061111111",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=2,
        )

        self.u_pat = User.objects.create_user(username="pat_notes", password="pass123")
        self.pat = Pat.objects.create(
            user=self.u_pat,
            name="Igor",
            surname="Igic",
            description="Stare napomene",
            secretNotes="Stare tajne napomene",
            email="pat_notes@dentasoft.com",
            telephone="060000000",
        )

    def test_doctor_can_update_patient_public_and_secret_notes(self):
        self.client.force_login(self.u_doc)

        url = reverse("meds:editKarton", args=[self.pat.id])

        resp = self.client.post(url, data={
            "description": "Nove javne napomene (vidi pacijent).",
            "Doctordescription": "Nove tajne napomene (samo doktor).",
        })

        self.assertEqual(resp.status_code, 302)

        self.pat.refresh_from_db()
        self.assertEqual(self.pat.description, "Nove javne napomene (vidi pacijent).")
        self.assertEqual(self.pat.secretNotes, "Nove tajne napomene (samo doktor).")

    def test_patient_does_not_see_secret_notes_on_own_karton(self):
        self.pat.secretNotes = "OVO NE SME DA SE VIDI PACIJENTU"
        self.pat.save()

        self.client.force_login(self.u_pat)
        url = reverse("patients:karton")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.assertContains(resp, self.pat.description)
        self.assertNotContains(resp, "OVO NE SME DA SE VIDI PACIJENTU")

class SpecializationUpgradeRequestTests(TestCase):
    def setUp(self):
        self.u_doc = User.objects.create_user(username="doc_spec", password="pass123")
        self.doc = Med.objects.create(
            user=self.u_doc,
            name="Jovan",
            surname="Jovic",
            description="Opis",
            email="doc_spec@dentasoft.com",
            telephone="061111111",
            is_active=True,
            vacation_days_total=20,
            vacation_days_remaining=20,
            vacation_days_year=timezone.now().year,
            level_spec=2,
        )

        self.u_admin = User.objects.create_user(
            username="admin_spec",
            password="pass123",
            is_staff=True,
            is_active=True,
        )

    def test_doctor_can_open_request_specialization_page(self):
        self.client.force_login(self.u_doc)
        url = reverse("meds:request_specialization_upgrade")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_doctor_post_creates_pending_request(self):
        self.client.force_login(self.u_doc)
        url = reverse("meds:request_specialization_upgrade")

        resp = self.client.post(url, data={"requested_level": 4})
        self.assertEqual(resp.status_code, 302)

        req = SpecializationUpgradeRequest.objects.get(med=self.doc)
        self.assertEqual(req.status, SpecializationUpgradeRequest.STATUS_PENDING)
        self.assertEqual(req.requested_level, 4)

    def test_doctor_post_updates_existing_pending_request(self):
        SpecializationUpgradeRequest.objects.create(
            med=self.doc,
            requested_level=3,
            status=SpecializationUpgradeRequest.STATUS_PENDING
        )

        self.client.force_login(self.u_doc)
        url = reverse("meds:request_specialization_upgrade")

        resp = self.client.post(url, data={"requested_level": 5})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(SpecializationUpgradeRequest.objects.filter(med=self.doc).count(), 1)
        req = SpecializationUpgradeRequest.objects.get(med=self.doc)
        self.assertEqual(req.requested_level, 5)

    def test_admin_can_approve_request_and_level_updates(self):
        req = SpecializationUpgradeRequest.objects.create(
            med=self.doc,
            requested_level=5,
            status=SpecializationUpgradeRequest.STATUS_PENDING
        )

        self.client.force_login(self.u_admin)
        url = reverse("users:approve_spec_request", args=[req.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        req.refresh_from_db()
        self.doc.refresh_from_db()

        self.assertEqual(req.status, SpecializationUpgradeRequest.STATUS_APPROVED)
        self.assertEqual(self.doc.level_spec, 5)

    def test_admin_can_reject_request_and_note_is_saved(self):
        req = SpecializationUpgradeRequest.objects.create(
            med=self.doc,
            requested_level=5,
            status=SpecializationUpgradeRequest.STATUS_PENDING
        )

        self.client.force_login(self.u_admin)
        url = reverse("users:reject_spec_request", args=[req.id])
        resp = self.client.post(url, data={"admin_note": "Nedostaju dokumenti."})
        self.assertEqual(resp.status_code, 302)

        req.refresh_from_db()
        self.assertEqual(req.status, SpecializationUpgradeRequest.STATUS_REJECTED)
        self.assertEqual(req.admin_note, "Nedostaju dokumenti.")
