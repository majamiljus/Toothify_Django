# Maja Miljuš 0576/2022 
# Irina Majstorovic 0518/2022
# Minja Krivokapić 0615/2022
import json
from django.shortcuts import render,redirect
from django.db.models import Avg
from index.models import AllInterventions, Rating
from meds.models import WorkTime, Med, Vacation
from patients.models import Intervention,Pat
from django.contrib import messages
import os
from datetime import datetime
from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from users.models import Notification
from patients.notifications import send_intervention_scheduled_email
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from meds.models import WorkTime, Vacation
from patients.models import Intervention

# Maja Miljuš 0576/2022: 
# Irina Majstorovic 0518/2022:
def index(request):
    """
    **Opis:**  
    Prikaz početne stranice aplikacije za ulogovanog korisnika.

    **Kontekst:**

    ``gallery_images``
        Lista URL-ova slika iz galerije.

    ``patient_notifications``
        Poslednje tri notifikacije za pacijenta.

    **Template:**
    
    :template:`index.html`
    """
    gallery_folder = os.path.join(settings.BASE_DIR, 'static', 'photos', 'gallery')
    gallery_images = []
    for file_name in os.listdir(gallery_folder):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            gallery_images.append(static(f'photos/gallery/{file_name}'))

    patient_notifications = Notification.objects.filter(
        for_patients=True
    ).order_by('-created_at')[:3]


    context = {
        'gallery_images': gallery_images,
        'patient_notifications': patient_notifications,
    }
    return render(request, 'index.html', context)


# Maja Miljuš 0576/2022: 
def about(request):
    """
    **Opis:**  
    Prikaz stranice "O nama" sa informacijama stomatologa iz :model:`meds.Med`.

    **Kontekst:**

    ``doctors``
        Svi stomatolozi iz :model:`meds.Med` sa:
        
        - ``avg_rating`` – prosecna ocena lekara 

        - ``avg_rating_display`` – string prikaz ocene ili "neocenjen"

    **Template:**
    
    :template:`about.html`
    """
    doctors = Med.objects.all().annotate(avg_rating=Avg('rating__star'))
    for doc in doctors:
        if doc.avg_rating is None:
            doc.avg_rating_display = "neocenjen"
        else:
            doc.avg_rating = round(doc.avg_rating, 2)  # npr. 4.99
            doc.avg_rating_display = f"{doc.avg_rating} / 5"
    context = {
        'doctors': doctors
    }
    return render(request, 'about.html', context)


# Minja Krivokapić 0615/2022: 
def book_int(request):
    """
    **Opis:**  
        Omogucava pacijentu da zakaze intervenciju kod lekara.  

    **Kontekst:**  
        ``interventions``  
            Intervencija iz modela :model:`index.AllInterventions`.  
        ``doctors``  
            Lekarima iz modela :model:`meds.Med`.  
        ``today_time``  
            Trenutno vreme na serveru u formatu "HH:MM".  
        ``today_date``  
            Datum sledeceg ponedeljka, koji je pocetak perioda za zakazivanje.  
        ``max_date``  
            Datum dve nedelje nakon sledećeg ponedeljka, kraj perioda za zakazivanje.  
    
        **Template:**  
            :template:`bookIntervention.html`
    """
    interventions = AllInterventions.objects.all()
    doctors = Med.objects.all()
    now = timezone.localtime()

    def _next_monday(d):
        days_ahead = (0 - d.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return d + timedelta(days=days_ahead)

    today = timezone.localdate()
    start_date = _next_monday(today)
    end_date = start_date + timedelta(days=13)

    if request.method == "POST":
        intervention_desc = request.POST.get('intervention_desc')
        intervention_duration = request.POST.get('intervention_duration')
        doctor_id = request.POST.get('doctor_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        if not (intervention_desc and intervention_duration and doctor_id and date_str and time_str):
            messages.error(request, "Popunite sva polja.")
            return redirect('index:book_int')

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()

        appointment_dt = datetime.combine(date_obj, time_obj)
        appointment_dt = timezone.make_aware(appointment_dt, timezone.get_current_timezone())

        if appointment_dt < now:
            messages.error(request, "Ne možete zakazati intervenciju u prošlosti.")
            return redirect('index:book_int')

        if date_obj < start_date or date_obj > end_date:
            messages.error(request, "Možete zakazati samo od sledećeg ponedeljka u naredne 2 nedelje.")
            return redirect('index:book_int')

        if date_obj.weekday() >= 5:
            messages.error(request, "Ne možete zakazivati vikendom.")
            return redirect('index:book_int')

        doctor = Med.objects.get(id=doctor_id)
        patient = request.user.pat_profile

        intervention = Intervention.objects.create(
            idMed=doctor,
            idPat=patient,
            description=intervention_desc,
            duration=int(intervention_duration),
            status="Zakazan",
            date=date_obj,
            time=time_obj
        )

        send_intervention_scheduled_email(intervention)
        messages.success(request, "Intervencija uspešno zakazana!")
        return redirect('index:book_int')

    context = {
        "interventions": interventions,
        "doctors": doctors,
        "today_time": now.strftime('%H:%M'),
        "today_date": start_date.isoformat(), 
        "max_date": end_date.isoformat(),
    }
    return render(request, 'bookIntervention.html', context)


# Maja Miljuš 0576/2022: 
def get_available_times(request):
    """
    **Opis:**  
    Vraca dostupne termine za izabranog lekara na zadati datum i na osnovu trajanja
    intervencije.

    **Kontekst:**

    ``doctor_id``
        ID lekara za kojeg trazimo dostupne termine

    ``date``
        Datum termina 

    ``duration``
        Trajanje intervencije u minutima

    **Vraca:**

    JSON objekat:
    
    ``times``
        Lista slobodnih termina u formatu "HH:MM"

    **Primer odgovora:**
    
    {
    "times": ["09:00", "09:10", "09:20", ...]
    }
    """
    doctor_id = request.GET.get("doctor_id")
    date_str = request.GET.get("date")
    duration = request.GET.get("duration")

    if not doctor_id or not date_str or not duration:
        return JsonResponse({"times": []})

    date = parse_date(date_str)
    if not date:
        return JsonResponse({"times": []})

    doctor_id = int(doctor_id)
    duration = int(duration)

    wt = WorkTime.objects.filter(idMed_id=doctor_id, date=date).first()

    if not wt:
        return JsonResponse({"times": []})

    if Vacation.objects.filter(
        idMed_id=doctor_id,
        status=1,
        startDate__lte=date,
        endDate__gte=date
    ).exists():
        return JsonResponse({"times": []})

    work_start = datetime.combine(date, wt.startTime)
    work_end   = datetime.combine(date, wt.endTime)

    break_start = datetime.combine(date, wt.breakTime)
    break_end   = break_start + timedelta(minutes=30)

    booked = Intervention.objects.filter(date=date, idMed=doctor_id, status="Zakazan")
    booked_intervals = sorted([
        (datetime.combine(date, b.time), datetime.combine(date, b.time) + timedelta(minutes=b.duration))
        for b in booked
    ])

    slots = []
    current = work_start

    while current + timedelta(minutes=duration) <= work_end:

        if break_start <= current < break_end or break_start < (current + timedelta(minutes=duration)) <= break_end:
            current = break_end
            continue

        next_possible = current
        for b_start, b_end in booked_intervals:
            if current >= b_end + timedelta(minutes=10):
                continue
            if current < b_start - timedelta(minutes=10):
                break
            next_possible = max(next_possible, b_end + timedelta(minutes=10))

        end_dt = next_possible + timedelta(minutes=duration)

        overlaps = [
            (b_start, b_end) 
            for b_start, b_end in booked_intervals
            if not (end_dt + timedelta(minutes=10) <= b_start or next_possible >= b_end + timedelta(minutes=10))
        ]

        if not overlaps and end_dt <= work_end:
            slots.append(next_possible.strftime("%H:%M"))
            current = next_possible + timedelta(minutes=10) 
        else:
            if overlaps:
                latest_end = max(b_end for b_start, b_end in overlaps)
                current = latest_end + timedelta(minutes=10)
            else:
                break


    return JsonResponse({"times": slots})


# Maja Miljuš 0576/2022: 
@login_required
def user_logout(request):
    """
    **Opis:**  
    Odjava ulogovanog korisnika.Prosledjivanje na index aplikaciju i pocetnu stranu.

    **View:**
    :view:`index.index`
    """
    logout(request)
    return redirect('index:index')


# Irina Majstorovic 0518/2022:
@login_required
def index_doctor(request):
    """
    **Opis:**  
    Prikaz pocetne stranice lekara.

    **Template:**

    :template:`indexDoctor.html`
    """
    return render(request, 'indexDoctor.html')


# Maja Miljuš 0576/2022: 
def save_rating(request):
    """
    **Opis:**  
    Cuvanje ili azuriranje ocene za odredjenu intervenciju od strane pacijenta.  

    **Kontekst:**

    ``intervention_id``
        ID intervencije koja se ocenjuje 

    ``med_id``
        ID lekara koji se ocenjuje

    ``star``
        Ocena lekara (integer)

    ``comment``
        Komentar pacijenta o intervenciji (string)

    **Vraca:**

    JSON objekat sa kljucevima:

    ``success``
        True ako je operacija uspesna, False u slucaju greske

    ``updated``
        True ako je ocena azurirana, False ako je kreirana nova ocena

    ``error``
        Poruka greske 

        **Modeli:**
        - :model:`patients.Intervention`
        - :model:`index.Rating`
        - :model:`meds.Med`
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"})

    data = json.loads(request.body)

    intervention_id = data.get("intervention_id")
    med_id = data.get("med_id")
    star = data.get("star")
    comment = data.get("comment")

    try:
        intervention = Intervention.objects.get(id=intervention_id)
        doctor = intervention.idMed
        patient = request.user.pat_profile  # pacijent
    except Intervention.DoesNotExist:
        return JsonResponse({"success": False, "error": "Intervention not found"})

    r, created = Rating.objects.update_or_create(
        idMed=doctor,
        idPat=patient,
        defaults={
            "star": int(star),
            "comment": comment
        }
    )

    return JsonResponse({"success": True, "updated": not created})