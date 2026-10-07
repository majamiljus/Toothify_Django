#Irina Majstorović 2022/0518
#Minja Krivokapić 2022/0615
#Maja Miljuš 2022/0576
from .notifications import send_intervention_scheduled_email
from datetime import datetime, timedelta, timezone
from django.shortcuts import render, redirect
from .models import *
from meds.models import  WorkTime, Med, Vacation
from index.models import Rating ,AllInterventions 
from datetime import datetime, timedelta
from meds.models import WorkTime
import os
from django.db.models import Case, When, IntegerField
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from django.utils.dateparse import parse_date
from patients.models import Intervention
from datetime import date as date_cls


#Irina Majstorović 2022/0518
def _next_monday(d: date_cls) -> date_cls:
    """
    Vraca datum sledeceg ponedeljka nakon datog datuma.
    Ako je prosledjeni datum ponedeljak, vraca ponedeljak naredne nedelje.

    Povratna vrednost:
        Objekat tipa `date` koji predstavlja sledeci ponedeljak
    """
    days_ahead = (0 - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return d + timedelta(days=days_ahead)


#Minja Krivokapić 2022/0615
def med(request, idMed):
    """
    Prikazuje stranicu lekara i omogućava pacijentu zakazivanje intervencija.

    - GET zahtev:
        - prikazuje informacije o lekaru
        - prikazuje listu svih dostupnih intervencija koje lekar može da izvrši
        - prikazuje zauzete i slobodne termine za izabrani datum
        - prikazuje komentare pacijenata za lekara
    - POST zahtev:
        - omogućava pacijentu da zakaže intervenciju za izabrani datum i vreme
        - kreira novi zapis u tabeli :model:`patients.Intervention` sa statusom "Zakazan" ako je uspešno odrađeno

    **Template:**
    :template:`med.html`
    """
    idPat = request.user.pat_profile
    message = ''
    code = 0
    interventions = Intervention.objects.filter(idPat=idPat)

    today = datetime.now().date()
    startDate = _next_monday(today)
    endDate = startDate + timedelta(days=13)

    if request.method == "POST":
        intervention = request.POST.get("intervention")
        date = request.POST.get("date")
        time = request.POST.get("time")


        inter = AllInterventions.objects.get(pk=int(intervention))
        description = inter.description
        date1 = datetime.strptime(date, "%Y-%m-%d").date()
        weekday = date1.weekday()
        workTime = WorkTime.objects.filter(idMed_id=idMed, date=date1).first()

        
        if date1 < startDate or date1 > endDate:
            message = "Možeš da zakazuješ samo od sledećeg ponedeljka u naredne 2 nedelje."
            code = 1

        if weekday >= 5 and not message:
            message = "Ne možeš da zakazuješ vikendom."
            code = 1

        if not workTime and not message:
            message = "Doktor nema definisano radno vreme za izabrani datum."
            code = 1
        if not message:
            on_vacation = Vacation.objects.filter(
                idMed_id=idMed,
                startDate__lte=date1,
                endDate__gte=date1
            ).exists()
            if on_vacation:
                message = "Doktor je na odmoru izabranog datuma."
                code = 1

        time1 = datetime.strptime(time, "%H:%M").time()
        start1 = datetime.combine(date1, time1)
        end1 = start1 + timedelta(minutes=inter.duration)



        workStart = datetime.combine(date1, workTime.startTime)
        workEnd = datetime.combine(date1, workTime.endTime)


        if (start1 < workStart or end1 > workEnd) and not message:
            latestStart = workEnd - timedelta(minutes=inter.duration)
            message = f"Poslednji mogući termin za ovu intervenciju je u {latestStart.strftime('%H:%M')}."
            code = 1

        breakStart = datetime.combine(date1, workTime.breakTime)
        breakEnd = breakStart + timedelta(minutes=30)
        if start1 < breakEnd and end1 > breakStart and not message:
            message = f"Lekar ima pauzu od {workTime.breakTime.strftime('%H:%M')} do {breakEnd.strftime('%H:%M')}."
            code = 1

        if not message:
            doctor = Med.objects.get(id=idMed)
            Intervention.objects.create(
                idMed=doctor,
                idPat=idPat,
                description=description,
                duration=int(inter.duration),
                status="Zakazan",
                date=date1,
                time=time1
            )


            message = 'Uspešno ste zakazali termin.'
            code = 0

    rates = Rating.objects.filter(idMed=idMed)

    avgRate = rates.aggregate(avg=models.Avg('star'))['avg'] if rates.exists() else None
    myRate = Rating.objects.filter(idMed=idMed, idPat=idPat).first()

    if avgRate is None:
        avgRateDisplay = "neocenjen"
    else:
        avgRate = round(avgRate, 2)
        avgRateDisplay = f"{avgRate} / 5"

    med = Med.objects.get(id=idMed)
    med = {
        "name": med.name,
        "surname": med.surname,
        "email": med.email,
        "telephone": med.telephone,
        "description": med.description,
        "avgRate": avgRate,
        "avgRateDisplay": avgRateDisplay,
        "image": med.image.url if med.image else "/static/photos/default.jpg"
    }

    available = []
    weekend = False
    selectedDate = request.GET.get("date")
    if selectedDate:
        try:
            date = datetime.strptime(selectedDate, "%Y-%m-%d").date()
           
            if date < startDate or date > endDate:
                return redirect(f"{request.path}?date={startDate}")

           
            if date.weekday() >= 5:  
                weekend = True
                available = [] 
            else:
                
                workTime = WorkTime.objects.filter(idMed_id=idMed, date=date).first()
                if workTime:
                    start = datetime.combine(date, workTime.startTime)
                    end = datetime.combine(date, workTime.endTime)
                    breakTime = datetime.combine(date, workTime.breakTime)

                    slots = []
                    while start < end:
                        slot = start + timedelta(minutes=30)
                        if slot <= end:
                            slots.append(start.time())
                        start = slot

                    booked = Intervention.objects.filter(idMed=idMed, date=date)
                    bookedSlots = []
                    for b in booked:
                        bookedStart = datetime.combine(date, b.time)
                        bookedEnd = bookedStart + timedelta(minutes=b.duration)
                        current = bookedStart
                        while current < bookedEnd:
                            bookedSlots.append(current.time())
                            current += timedelta(minutes=30)

                    available = [
                        s for s in slots
                        if s != breakTime.time() and s not in bookedSlots
                    ]


        except ValueError:

            return redirect(f"{request.path}?date={startDate}")

    doctor_obj = Med.objects.get(id=idMed)
    doctor_level = doctor_obj.level_spec
    all_interventions = AllInterventions.objects.filter(level__lte=doctor_level)
    comments = Rating.objects.filter(
        idMed=doctor_obj,
        comment__isnull=False
    ).exclude(comment="").order_by("-created_at")
    context = {
        'interventions': all_interventions,
        'idMed': idMed,
        'med': med,
        'myRate': myRate.star if myRate else None,
        'photo': 'photos/med_' + str(idMed) + '.png',
        'available': available,
        'message': message,
        'code': code,
        'startDate': startDate,
        'endDate': endDate,
        'comments' : comments,
        'idPat': idPat,
        'weekend': weekend,
    }

    return render(request, "med.html", context)


#Maja Miljuš 2022/0576
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
    date_str = request.GET.get('date')
    intervention_id = request.GET.get('intervention')  
    doctor_id = request.GET.get('doctor')

    if not date_str or not intervention_id or not doctor_id:
        return JsonResponse({'available': [], 'weekend': False})

    date = parse_date(date_str)
    doctor_id = int(doctor_id)

   
    if date.weekday() >= 5:
        return JsonResponse({'available': [], 'weekend': True})


    selected_intervention = AllInterventions.objects.get(id=intervention_id)
    duration = selected_intervention.duration

   
    work_time = WorkTime.objects.filter(idMed_id=doctor_id, date=date).first()
    if not work_time:
        return JsonResponse({'available': [], 'weekend': False})

  
    on_vacation = Vacation.objects.filter(
        idMed_id=doctor_id,
        startDate__lte=date,
        endDate__gte=date
    ).exists()
    if on_vacation:
        return JsonResponse({'available': [], 'weekend': False})

    work_start = datetime.combine(date, work_time.startTime)
    work_end   = datetime.combine(date, work_time.endTime)
    break_start = datetime.combine(date, work_time.breakTime)
    break_end   = break_start + timedelta(minutes=30)

    booked = Intervention.objects.filter(date=date, idMed=doctor_id)
    booked_intervals = []
    for appt in booked:
        b_start = datetime.combine(date, appt.time)
        b_end   = b_start + timedelta(minutes=appt.duration) + timedelta(minutes=5)
        booked_intervals.append((b_start, b_end))

    slots = []
    current_time = work_start
    while current_time + timedelta(minutes=duration) <= work_end:
        end_time = current_time + timedelta(minutes=duration)
        overlaps_break = not (end_time <= break_start or current_time >= break_end)
        overlaps_booked = any(not (end_time <= b_start or current_time >= b_end) for b_start, b_end in booked_intervals)

        if not overlaps_break and not overlaps_booked:
            slots.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=10)

    return JsonResponse({'available': slots, 'weekend': False})


#Maja Miljuš 2022/0576:
def myInterventions(request):
    """
    **Opis:**  
    Prikazuje listu intervencija za trenutno ulogovanog pacijenta. Omogucava
    filtriranje po danu, mesecu, godini i statusu, kao i sortiranje po datumu
    i vremenu.

    **Kontekst:**  
        ``pat:``  
        Instanca :model:`patients.Pat` koja predstavlja trenutno ulogovanog pacijenta.

        ``interventions:``  
        Instance iz :model:`patients.Intervention` koje sadrze sve intervencije pacijenta.

        ``arr:``  
        Lista sa detaljima svake intervencije.

        ``years:``  
        Lista godina u kojima pacijent ima intervencije, koristi se za filter.

        **Template:**  
        :template:`myInterventionsPatient.html`
    """
    pat = request.user.pat_profile

    day = request.GET.get('day')
    month = request.GET.get('month')
    year = request.GET.get('year')
    sortOrder = request.GET.get('sort', 'asc')
    status = request.GET.get('status')

    interventions = (
        Intervention.objects
        .filter(idPat=pat)  
        .select_related("idMed", "idPat")
    )

    if year:
        interventions = interventions.filter(date__year=year)
    if month:
        interventions = interventions.filter(date__month=month)
    if day:
        interventions = interventions.filter(date__day=day)
    if status:
        interventions = interventions.filter(status=status)

    
    if sortOrder == 'asc':
        interventions = interventions.order_by('date', 'time')
    else:
        interventions = interventions.order_by('-date', '-time')

   

    arr = []
    for inter in interventions:
        start_dt = datetime.combine(inter.date, inter.time)
        end_dt = start_dt + timedelta(minutes=inter.duration)
        med = inter.idMed
        
        can_rate = Intervention.objects.filter(
        idPat=pat,
        idMed=med,
        status='Završen'
        ).exists()

        myRate = Rating.objects.filter(idMed=med, idPat=pat).first()  
        arr.append({
            "id": inter.id,
            "med_id": med.id,
            "doctor": f"{med.name} {med.surname}",
            "email": med.email,
            "telephone": med.telephone,
            "interventionName": inter.description,
            "date": inter.date,
            "start": start_dt.strftime("%H:%M"),
            "end": end_dt.strftime("%H:%M"),
            "status": inter.status,
            "patient_star": myRate.star if myRate else None,
            "patient_comment": myRate.comment if myRate else None,
            "rating_id": myRate.id if myRate else None,
            "rating_choices": range(1, 6),
            "can_rate": can_rate, 
        })

    years = sorted(
        Intervention.objects.filter(idPat=pat).values_list("date__year", flat=True).distinct(),
        reverse=True
    )

    context = {
        "myInterventions": arr,
        "days": [(i, str(i)) for i in range(1, 32)],
        "months": [(1, "Januar"), (2, "Februar"), (3, "Mart"), (4, "April"), (5, "Maj"), (6, "Jun"),
                   (7, "Jul"), (8, "Avgust"), (9, "Septembar"), (10, "Oktobar"), (11, "Novembar"), (12, "Decembar")],
        "years": years,
        "selectedDay": day or "",
        "selectedMonth": month or "",
        "selectedYear": year or "",
        "sortOrder": sortOrder,
        "today": timezone.now().date(),
    }
    return render(request, "myInterventionsPatient.html", context)


#Maja Miljuš 2022/0576:
def deleteIntervention(request, idInt):
    """
    **Opis:**
    Brise intervenciju sa zadatim ID-jem za trenutno ulogovanog pacijenta i
    preusmerava korisnika nazad na listu njegovih intervencija.

    Nakon brisanja, korisnik se preusmerava na :template:`myInterventionsPatient.html`.

    """
    intervention = Intervention.objects.filter(pk = idInt)
    intervention.delete()
    return redirect("patients:myInterventions")


#Maja Miljuš 2022/0576:
@login_required
def profile(request):
    """
    Opis:
        Prikazuje profil trenutno ulogovanog pacijenta.

    Kontekst:
        patient
            Instanca :model:`patients.Pat` koja predstavlja trenutno ulogovanog pacijenta.
        image
            URL slike pacijenta.

        **Template:**
        :template:`patientProfile.html`.
    """
    patient = request.user.pat_profile
  

    context = {
        "patient": patient,
        "image": patient.image.url
    }
    return render(request, "patientProfile.html", context)


#Minja Krivokapić 2022/0615:
def editProfile(request):
    """
    Omogucava pacijentu da izmeni svoj profil.
    **Template:**
    :template:`patientEditProfile.html`.

    """
    patient = request.user.pat_profile

    if request.method == "POST":
        if "cancel" in request.POST:
            return redirect("patients:profile")

        patient.name = request.POST.get("name")
        patient.surname = request.POST.get("surname")
        patient.email = request.POST.get("email")
        patient.telephone = request.POST.get("telephone")
        uploaded_file = request.FILES.get("image")
        if uploaded_file:
            patient.image = uploaded_file
        patient.save()

        return redirect("patients:profile")

    context = {
        "patient": patient,
    }
    return render(request, "patientEditProfile.html", context)


#Irina Majstorović 2022/0518:
def karton(request):
    """
    Prikazuje karton pacijenta sa zavrsenim intervencijama.

    **Kontekst:**

    - patient: 
        instanca :model:`patients.Pat` koja predstavlja trenutno ulogovanog korisnika.

    - intervencije: 
        lista zavrsenih intervencija za ulogovanog korisnika iz :model:`patients.Intervention`.

    **Template:** 
    :template:`patientKarton.html`
    """
    patient = request.user.pat_profile

    interventions = Intervention.objects.filter(idPat=patient, status='Završen').order_by('-date', '-time')

    data = []
    for inter in interventions:
        med = inter.idMed
        start_dt = datetime.combine(inter.date, inter.time)
        end_dt = start_dt + timedelta(minutes=inter.duration)

        data.append({
            "date": inter.date.strftime("%d.%m.%Y."),
            "intervencija": inter.description,
            "stomatolog": f"dr {med.name} {med.surname}",
            "vreme": f"{start_dt.strftime('%H:%M')}h - {end_dt.strftime('%H:%M')}h",
            "status": inter.status
        })

    context = {
        "patient": patient,
        "intervencije": data
    }

    return render(request, "patientKarton.html", context)
  

#Minja Krivokapić 2022/0615
def cancel_intervention(request, id):
    """
    Omogućava pacijentu da otkaže svoju intervenciju.
    """
    if request.method == "POST":
        intervention = get_object_or_404(Intervention, id=id)
        if intervention.idPat != request.user.pat_profile:
            messages.error(request, "Ne možete otkazati ovu intervenciju.")
            return redirect('patients:myInterventions')

        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        if intervention.date == tomorrow:
            messages.error(request, "Ne možete otkazati dan pre termina.")
            return redirect('patients:myInterventions')

        if intervention.date == today:
            messages.error(request, "Ne možete otkazati na dan intervencije.")
            return redirect('patients:myInterventions')

        intervention.status = "Otkazan"
        intervention.save()

        messages.success(request, "Uspešno ste otkazali intervenciju.")
        return redirect('patients:myInterventions')

    return redirect('patients:myInterventions')

