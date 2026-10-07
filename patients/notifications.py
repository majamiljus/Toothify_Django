#Aleksandar Pavlovic 2022/0093

from django.core.mail import send_mail
from django.conf import settings


def send_intervention_scheduled_email(intervention):
    """
    **Opis:**
        Šalje email pacijentu kao potvrdu da je termin uspešno zakazan.

    **Parametri:**
        ``intervention``
            Instanca modela intervencije (sadrži pacijenta, lekara, datum, vreme, trajanje).

    **Povratna vrednost:**
        Nema (funkcija šalje email). U slučaju greške može baciti izuzetak
        jer je ``fail_silently=False``.
    """
    patient = intervention.idPat
    doctor = intervention.idMed

    subject = "Uspešno ste zakazali termin"

    message = (
        f"Poštovani {patient.name} {patient.surname},\n\n"
        f"Uspešno ste zakazali termin u našoj ordinaciji.\n\n"
        f"Datum: {intervention.date.strftime('%d.%m.%Y')}\n"
        f"Vreme: {intervention.time.strftime('%H:%M')}\n"
        f"Lekar: dr {doctor.name} {doctor.surname}\n\n"
        f"Ako niste vi zakazali ovaj termin ili želite da izvršite izmene, "
        f"kontaktirajte ordinaciju.\n\n"
        f"Srdačan pozdrav,\n"
        f"DentaSoft tim"
    )

    recipient_list = [patient.email]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )

def send_intervention_canceled_email(intervention):
    """
    **Opis:**
        Šalje email pacijentu da je prethodno zakazan termin otkazan.

    **Parametri:**
        ``intervention``
            Instanca modela intervencije (podaci o pacijentu, lekaru, datumu i vremenu).

    **Povratna vrednost:**
        Nema (funkcija šalje email). U slučaju greške može baciti izuzetak
        jer je ``fail_silently=False``.
    """
    patient = intervention.idPat
    doctor = intervention.idMed

    subject = "Otkazan termin u ordinaciji"

    message = (
        f"Poštovani {patient.name} {patient.surname},\n\n"
        f"Obaveštavamo Vas da je Vaš termin kod doktora "
        f"{doctor.name} {doctor.surname}, zakazan za datum {intervention.date} "
        f"u {intervention.time}, otkazan.\n\n"
        "Razlog otkazivanja je nemogućnost doktora da obavi pregled u tom terminu.\n\n"
        "Molimo Vas da zakažete novi termin putem aplikacije ili kontaktiranjem ordinacije.\n\n"
        "Hvala na razumevanju,\n"
        "DentaSoft tim"
    )

    recipient_list = [patient.email]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False,
    )
