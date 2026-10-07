#Irina Majstorović 2022/0518
#Maja Miljuš 2022/0576
#Minja Krivokapic 0615/2022 
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db.models import Q
from patients.models import Intervention, Pat
from .models import Vacation, WorkTime
from .models import Med
from index.models import Rating
from django.utils import timezone
from django.db.models import Case, When, IntegerField
from index.models import AllInterventions 
from django.utils.dateparse import parse_date
from users.models import Notification
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from patients.notifications import (
    send_intervention_scheduled_email,
    send_intervention_canceled_email,
)
from .models import SpecializationUpgradeRequest
from django.contrib import messages
from datetime import date, time
from .models import WorkTime
from django.contrib import messages


#Irina Majstorović 2022/0518:
def _next_monday(d: date) -> date:
    """
    Vraca datum sledeceg ponedeljka nakon datog datuma.
    Ako je prosledjeni datum ponedeljak, vraca ponedeljak naredne nedelje.

    Povratna vrednost:
        Objekat tipa `date` koji predstavlja sledeci ponedeljak
    """
    # Monday = 0 ... Sunday = 6
    days_ahead = (0 - d.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7 
    return d + timedelta(days=days_ahead)


#Irina Majstorović 2022/0518:
def _shift_to_times(shift_code: str):
    """
    Pretvara kod smene u odgovarajuće vreme pocetka, kraja i pauze.

    Smene:
        'FIRST'  -> 08:00-16:00
        'SECOND' -> 12:00-20:00

    Pauza se automatski postavlja na sredinu smene (start + 4h).
    
    Povratna vrednost:
        Tuple(start_time, end_time, break_time) kao objekti tipa `time`
    """
    if shift_code == "SECOND":
        start_t = time(12, 0)
        end_t = time(20, 0)
    else:
        start_t = time(8, 0)
        end_t = time(16, 0)

    # pauza na sredini
    break_t = (datetime.combine(date.today(), start_t) + timedelta(hours=4)).time()
    return start_t, end_t, break_t


#Minja Krivokapic 0615/2022: 
#Irina Majstorović 2022/0518:
@login_required
def setWorkTimeTwoWeeks(request):
    """
    Omogucava doktoru da postavi radno vreme za naredne dve nedelje.

    **Template:**

    :template:`setWorkTimeTwoWeeks.html`
    """

    med = Med.objects.get(user=request.user)

    today = timezone.localdate()
    start_date = _next_monday(today)     
    end_date = start_date + timedelta(days=13) 

    all_days = [start_date + timedelta(days=i) for i in range(14)]
    weekdays = [d for d in all_days if d.weekday() < 5] 

    if request.method == "POST":
        week1_shift = request.POST.get("week1_shift", "FIRST")  
        week2_shift = request.POST.get("week2_shift", "FIRST")
        
        WorkTime.objects.filter(
            idMed=med,
            date__gte=start_date,
            date__lte=end_date
        ).delete()

        objs = []
        for d in weekdays:
            shift = week1_shift if d < (start_date + timedelta(days=7)) else week2_shift
            start_t, end_t, break_t = _shift_to_times(shift)

            objs.append(WorkTime(
                idMed=med,
                date=d,
                startTime=start_t,
                endTime=end_t,
                breakTime=break_t
            ))

        WorkTime.objects.bulk_create(objs)
        return redirect("meds:myWorkTimeTwoWeeks")


    existing = WorkTime.objects.filter(
        idMed=med,
        date__gte=start_date,
        date__lte=end_date
    ).order_by("date")

    existing_map = {e.date: e for e in existing}

    return render(request, "setWorkTimeTwoWeeks.html", {
        "start_date": start_date,
        "end_date": end_date,
        "weekdays": weekdays,
        "existing_map": existing_map,
    })


#Minja Krivokapic 0615/2022: 
#Irina Majstorović 2022/0518:
@login_required
def myWorkTimeTwoWeeks(request):
    """
    Prikazuje radno vreme ulogovanog doktora za naredne dve nedelje.

    **Kontekst:**

    ``start_date``
        Datum sledećeg ponedeljka (početak perioda).

    ``end_date``
        Datum koji predstavlja kraj dvonedeljnog perioda.

    ``work_times``
        zapis radnog vremena za doktora,
        sortirani po datumu rastuće.

    **Template:**

    :template:`myWorkTimeTwoWeeks.html`
    """

    med = Med.objects.get(user=request.user)

    today = timezone.localdate()
    start_date = _next_monday(today)
    end_date = start_date + timedelta(days=13)

    work_times = WorkTime.objects.filter(
        idMed=med,
        date__gte=start_date,
        date__lte=end_date
    ).order_by("date")

    return render(request, "myWorkTimeTwoWeeks.html", {
        "start_date": start_date,
        "end_date": end_date,
        "work_times": work_times
    })


#Minja Krivokapic 0615/2022: 
@login_required
def myVacations(request):
    """
    Prikazuje godisnje odmore ulogovanog doktora.

    **Kontekst:**

    ``myVacations``
         zahtev za godišnji odmor (po potrebi filtriran).

    ``months``
        Lista meseci za prikaz u filteru.

    ``years``
        Lista godina koje postoje u zapisima odmora.

    ``selectedMonth``
        Trenutno izabrani mesec (ako postoji filter).

    ``selectedYear``
        Trenutno izabrana godina (ako postoji filter).

    ``vac_total``
        Ukupan broj dana godisnjeg odmora doktora.

    ``vac_remaining``
        Preostali broj dana godisnjeg odmora.

    ``vac_year``
        Godina na koju se odnosi evidencija odmora.

    **Template:**

    :template:`myVacations.html`
    """

    try:
        med = Med.objects.get(user=request.user)
        _reset_vacation_days_if_needed(med)

    except Med.DoesNotExist:
        return redirect('index:index')

    vacations_qs = Vacation.objects.filter(idMed=med).order_by('startDate')

    months = [
        (1, "Januar"), (2, "Februar"), (3, "Mart"), (4, "April"),
        (5, "Maj"), (6, "Jun"), (7, "Jul"), (8, "Avgust"),
        (9, "Septembar"), (10, "Oktobar"), (11, "Novembar"), (12, "Decembar"),
    ]

    years = sorted(
        {v.startDate.year for v in vacations_qs}
        | {v.endDate.year for v in vacations_qs}
    )

    month = request.GET.get("month", "")
    year = request.GET.get("year", "")

    vacations = vacations_qs
    if month:
        vacations = vacations.filter(startDate__month=month)
    if year:
        vacations = vacations.filter(startDate__year=year)

    context = {
        "myVacations": vacations,
        "months": months,
        "years": years,
        "selectedMonth": month,
        "selectedYear": year,
        "vac_total": med.vacation_days_total,
        "vac_remaining": med.vacation_days_remaining,
        "vac_year": med.vacation_days_year,
    }
    return render(request, "myVacations.html", context)


#Minja Krivokapic 0615/2022: 
@login_required
def deleteVacation(request, idVacation):
    """
    Briše zahtev za godišnji odmor doktora.
    """
    vac = Vacation.objects.filter(pk=idVacation).first()
    if not vac:
        return redirect("meds:myVacations")


    if vac.status in (0, 1):

        med = vac.idMed
        _reset_vacation_days_if_needed(med)

        days = _count_vacation_days(vac.startDate, vac.endDate)
        med.vacation_days_remaining += days
        if med.vacation_days_remaining > med.vacation_days_total:
            med.vacation_days_remaining = med.vacation_days_total
        med.save(update_fields=["vacation_days_remaining"])

        vac.delete()

    return redirect("meds:myVacations")


#Minja Krivokapic 0615/2022:
@login_required
def vacation(request):
    """
    Omogućava doktoru podnosenje zahteva za godisnji odmor.

    **Kontekst:**

    ``vac_total`` – ukupan broj dana godisnjeg odmora  

    ``vac_remaining`` – preostali broj dana  
    
    ``vac_year`` – godina na koju se odnosi evidencija odmora  

    **Template:**

    :template:`vacation.html`
    """

    try:
        med = Med.objects.get(user=request.user)
        _reset_vacation_days_if_needed(med)

    except Med.DoesNotExist:
        # nije doktor
        return redirect('index:index')

    if request.method == "POST":
        start_str = request.POST.get("startDate")
        end_str = request.POST.get("endDate")

        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        if end_date < start_date:
            messages.error(request, "Datum kraja ne može biti pre datuma početka.")
            return redirect("meds:vacation")

        requested_days = _count_vacation_days(start_date, end_date)

        if requested_days > med.vacation_days_remaining:
            messages.error(
                request,
                f"Nemaš dovoljno dana godišnjeg. Tražiš {requested_days}, a preostalo je {med.vacation_days_remaining}."
            )
            return redirect("meds:vacation")

        overlap = Vacation.objects.filter(
            idMed=med,
            status__in=[0, 1],
        ).filter(
            Q(startDate__lte=end_date, endDate__gte=start_date)
        )

        if overlap.exists():
            messages.error(request, "Već imaš odmor koji se preklapa sa izabranim periodom.")
            return redirect("meds:vacation")

        Vacation.objects.create(
            idMed=med,
            startDate=start_date,
            endDate=end_date,
            status=0
        )

        med.vacation_days_remaining -= requested_days
        med.save(update_fields=["vacation_days_remaining"])

        return redirect("meds:myVacations")

    
    return render(request, "vacation.html", {
        "vac_total": med.vacation_days_total,
        "vac_remaining": med.vacation_days_remaining,
        "vac_year": med.vacation_days_year,
    })


#Minja Krivokapic 0615/2022:
def get_available_times(doctor_id, date_str, intervention_id):
    """
    Vraća listu dostupnih termina za zakazivanje intervencije
    kod izabranog doktora za određeni datum.
    """
    if not date_str or not intervention_id or not doctor_id:
        return []

    date = parse_date(date_str)
    doctor_id = int(doctor_id)

    selected_intervention = AllInterventions.objects.get(id=intervention_id)
    duration = selected_intervention.duration

    work_override = WorkTime.objects.filter(idMed_id=doctor_id, date=date).first()
    if not work_override:
        return []  

    start_time = work_override.startTime
    end_time = work_override.endTime
    break_time = work_override.breakTime

    if Vacation.objects.filter(
            idMed_id=doctor_id,
            status__in=[0, 1],
            startDate__lte=date,
            endDate__gte=date
    ).exists():
        return []



    #work_start = datetime.combine(date, work_time.startTime)
    #work_end   = datetime.combine(date, work_time.endTime)
    work_start = datetime.combine(date, start_time)
    work_end   = datetime.combine(date, end_time)
    last_start = work_end - timedelta(minutes=duration  )


    break_start = datetime.combine(date, break_time)
    break_end   = break_start + timedelta(minutes=30)

    booked = Intervention.objects.filter(date=date, idMed_id=doctor_id, status="Zakazan")
    booked_intervals = [
        (
            datetime.combine(date, b.time),
            datetime.combine(date, b.time) + timedelta(minutes=b.duration + 5)
        )
        for b in booked
    ]

    slots = []
    current = work_start
    step = 10

    while current <= last_start:
        end_time = current + timedelta(minutes=duration)

        if end_time <= break_start or current >= break_end:
            overlaps = False
            for b_start, b_end in booked_intervals:
                if not (end_time <= b_start or current >= b_end):
                    overlaps = True
                    break

            if not overlaps:
                slots.append(current.time())

        current += timedelta(minutes=step)

    return slots


#Minja Krivokapic 0615/2022: 
def myInterventions(request):
    """
    Prikazuje intervencije ulogovanog doktora.

    **Kontekst:**

    ``myInterventions`` – lista obradjenih intervencija

    ``days`` – lista dana (1–31) za filter  

    ``months`` – lista meseci za filter  

    ``years`` – dostupne godine intervencija  

    ``selectedDay`` – trenutno izabrani dan  

    ``selectedMonth`` – trenutno izabrani mesec  

    ``selectedYear`` – trenutno izabrana godina  

    ``selectedStatus`` – trenutno izabrani status  

    **Template:**

    :template:`myInterventionsMeds.html`
    """

    idMed = Med.objects.get(user=request.user)

    day = request.GET.get("day")
    month = request.GET.get("month")
    year = request.GET.get("year")
    status = request.GET.get("status")  

    qs = Intervention.objects.filter(idMed=idMed)
    qs = qs.order_by(
        Case(
            When(status='Zakazan', then=0),
            When(status='Završen', then=1),
            When(status='Otkazan', then=2),
            default=3,
            output_field=IntegerField()
        ),
        'date',  
        'time'   
    )
    if day:
        qs = qs.filter(date__day=day)
    if month:
        qs = qs.filter(date__month=month)
    if year:
        qs = qs.filter(date__year=year)
    if status:           
        qs = qs.filter(status=status)

    
    arr = []
    for inter in qs:
        patient = inter.idPat
        start_dt = datetime.combine(inter.date, inter.time)
        end_dt = start_dt + timedelta(minutes=inter.duration)

        arr.append({
            "id": inter.id,
            "idPat": patient.id,
            "patient": f"{patient.name} {patient.surname}",
            "telephone": patient.telephone,
            "email": patient.email,
            "interventionName": inter.description,
            "date": inter.date.strftime("%d.%m.%Y."),
            "start": start_dt.strftime("%H:%M"),
            "end": end_dt.strftime("%H:%M"),
            "status": inter.status
        })

    days = [(i, i) for i in range(1, 32)]
    months = [
        (1, "Januar"), (2, "Februar"), (3, "Mart"), (4, "April"),
        (5, "Maj"), (6, "Jun"), (7, "Jul"), (8, "Avgust"),
        (9, "Septembar"), (10, "Oktobar"), (11, "Novembar"), (12, "Decembar"),
    ]
    years = sorted({i.date.year for i in Intervention.objects.filter(idMed=idMed)}, reverse=True)

    return render(request, "myInterventionsMeds.html", {
        "myInterventions": arr,
        "days": days,
        "months": months,
        "years": years,
        "selectedDay": day or "",
        "selectedMonth": month or "",
        "selectedYear": year or "",
        "selectedStatus": status or ""    
    })


#Minja Krivokapic 0615/2022:
def confirmIntervention(request, idInter):
    """
    Potvrdjuje intervenciju ulogovanog doktora.
    """
    if request.method == "POST":
        inter = Intervention.objects.get(id=idInter)

        if inter.status not in ["Završen", "Nije došao"]:
            inter.status = "Završen"
            inter.save()

    return redirect("meds:myInterventionsMeds")


#Minja Krivokapic 0615/2022:
def deleteIntervention(request, idInter):
    """
     Briše jednu intervenciju ulogovanog doktora.
    """
    Intervention.objects.filter(pk=idInter).delete()
    return redirect("meds:myInterventions")


#Maja Miljuš 2022/0576:
@login_required
def profile(request):
    """
    **Opis:**  
    Prikaz profila ulogovanog lekara sa komentarima pacijenata.

    **Kontekst:**

    ``med``
        Instanca :model:`meds.Med` koja predstavlja trenutno ulogovanog lekara.

    ``comments``
        Instance iz :model:`index.Rating` gde postoji komentar, 
        sortirani tako da najnoviji komentari budu prvi.

        **Template:**
        :template:`profile.html`
    """
    med = request.user.med
    comments = Rating.objects.filter(
            idMed=med,
            comment__isnull=False
        ).exclude(comment="").order_by("-created_at")

    context = {
        "med": med,
        "comments": comments
    }

    return render(request, "profile.html", context)


#Minja Krivokapic 0615/2022:
#Maja Miljuš 2022/0576:
def editProfile(request):
    """
    **Opis:**  
    Stomatolog menja svoj profil.

    **Kontekst:**

    ``med``
        Instanca :model:`meds.Med` koja predstavlja trenutno ulogovanog lekara.

    **Template:**

    :template:`editProfile.html`
    """
    med = request.user.med

    if request.method == "POST":
        if "cancel" in request.POST:
            return redirect("meds:profile")

        med.name = request.POST.get("name")
        med.surname = request.POST.get("surname")
        med.email = request.POST.get("email")
        med.telephone = request.POST.get("telephone")
        med.description = request.POST.get("description")

        if request.FILES.get("image"):
            med.image = request.FILES["image"]

        med.save()
        return redirect("meds:profile")

    return render(request, "editProfile.html", {"med": med})


#Minja Krivokapic 0615/2022:
def addIntervention(request):
    """
    Dodaje novu intervenciju za pacijenta.
    """
    idMed = request.user.med
    message = ""
    code = 0

    interventions = AllInterventions.objects.all()  # sve moguće intervencije
    patients = Pat.objects.select_related("user").order_by("name", "surname")

    selected_date = request.GET.get("date") or request.POST.get("date")
    selected_patient = request.GET.get("idPat") or request.POST.get("idPat")
    selected_intervention = request.GET.get("idInt") or request.POST.get("idInt")
    pat_obj = None
    if selected_patient:
        pat_obj = get_object_or_404(Pat.objects.select_related("user"), pk=int(selected_patient))

    today = timezone.localdate()
    startDate = _next_monday(today)
    endDate = startDate + timedelta(days=13)

    available = []
    weekend = False

    if selected_date and selected_patient and selected_intervention:
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

        if date_obj.weekday() >= 5:  
            weekend = True
            available = []  
        else:
            weekend = False
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            if date_obj < startDate or date_obj > endDate:
                return redirect(f"{request.path}?date={startDate}")

            available_times = get_available_times(
                doctor_id=idMed.id,
                date_str=selected_date,
                intervention_id=selected_intervention
            )
            available = [t.strftime("%H:%M") for t in available_times]
    else:
        weekend = False
        available = []

    if request.method == "POST":
        idPat = request.POST.get("idPat")
        idInt = request.POST.get("idInt")
        date = request.POST.get("date")
        time = request.POST.get("time")

        if not all([idPat, idInt, date, time]):
            return render(request, "patient.html", {
                "message": "Morate popuniti sva polja.",
                "code": 1,
                "patients": patients,
                "interventions": interventions,
                "available": available,
                "startDate": startDate,
                "endDate": endDate,
                "selectedDateValue": selected_date,
                "selected_patient": selected_patient,
                "selected_intervention": selected_intervention
            })


        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(time, "%H:%M").time()

      
        int_obj = AllInterventions.objects.get(id=idInt)
        desc = int_obj.description
        duration = int_obj.duration

        pat_selected = get_object_or_404(Pat.objects.select_related("user"), pk=int(idPat))

        Intervention.objects.create(
            idMed=idMed,
            idPat=pat_selected,
            description=desc,
            duration=duration,
            date=date_obj,
            time=time_obj,
            status="Zakazan"
        )

        return redirect("meds:myInterventionsMeds")

    return render(request, "patient.html", {
        "patients": patients,
        "selected_patient": selected_patient,
        "interventions": interventions,
        "selected_intervention": selected_intervention,
        "available": available,
        "startDate": startDate,
        "endDate": endDate,
        "selectedDateValue": selected_date,
        "message": message,
        "code": code,
        "weekend": weekend,
    })


#Minja Krivokapic 0615/2022:
def karton(request, idPat):
    """
    Prikazuje medicinski karton pacijenta.
    """
    patient = Pat.objects.get(id=idPat)
    all_interventions = Intervention.objects.filter(idPat=idPat).order_by("-date", "-time")

    data = []
    for inter in all_interventions:
        med = inter.idMed
        data.append({
            "date": inter.date.strftime("%d.%m.%Y."),
            "intervencija": inter.description,
            "stomatolog": f"dr {med.name} {med.surname}",
            "napomena": inter.description or "-"
        })

    return render(request, "kartonMedspat.html", {
        "patient": patient,
        "intervencije": data
    })


#Minja Krivokapic 0615/2022:
def editKarton(request, idPat):
    """
    Omogućava stomatologu da izmeni karton pacijenta.

    **Kontekst:**

    ``med``
        Instanca :model:`meds.Med` koja predstavlja trenutno ulogovanog lekara.

    **Template:**

    :template:`editKarton.html`
    """
    patient = Pat.objects.get(id=idPat)
    from_page = request.GET.get("from", "karton")

    if request.method == "POST":
        if "cancel" in request.POST:
            if from_page == "myInterventionsMeds":
                return redirect("meds:myInterventionsMeds")

            return redirect("meds:karton", idPat=idPat)

        new_description = request.POST.get("description")
        doctor_description = request.POST.get("Doctordescription")
        patient.description = new_description
        patient.secretNotes = doctor_description
        patient.save()

        if from_page == "myInterventionsMeds":
            return redirect("meds:myInterventionsMeds")

        return redirect("meds:karton", idPat=idPat)

    return render(request, "editKarton.html", {"patient": patient})


#Minja Krivokapic 0615/2022:
def cancelIntervention(request, id):
    """
    Otkazuje intervenciju i obavestava pacijenta.
    """
    intervention = Intervention.objects.filter(id=id).first()

    if not intervention:
        return redirect("meds:myInterventionsMeds")

    intervention.status = "Otkazan"
    intervention.save()

    send_intervention_canceled_email(intervention)

    return redirect("meds:myInterventionsMeds")


#Irina Majstorović 2022/0518:
def notificationMeds(request):
    """
    **Opis:**  
    Prikaz  stranice sa obavestenjima za lekara.

    **Template:**

    :template:`doctorNotifications.html`
    """
    return render(request, "doctorNotifications.html")


#Irina Majstorović 2022/0518:
def indexDoctor(request):
    """
    **Opis:**  
    Prikaz pocetne stranice lekara.

    **Template:**

    :template:`indexDoctor.html`
    """
    return render(request, "indexDoctor.html")


#Irina Majstorović 2022/0518:
def notificationsMeds(request):
    """
    Sluzi za kreiranje novih obavestenja i pregled postojecih.

    Funkcionalnosti:

    - POST zahtev:
        - kreiranje obavestenja sa naslovom i tekstom
        - obavestenje moze biti i za pacijente
    - GET zahtev:
        - prikazuje listu svih obavestenja, sortiranu po datumu kreiranja (najnovije prvo)

    **Template:**

    :template:`notificationsMeds.html`
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        for_patients = bool(request.POST.get("for_patients"))

        if title and text:
            Notification.objects.create(
                author=request.user,
                title=title,
                text=text,
                for_patients=for_patients,
            )

    notifications = Notification.objects.order_by('-created_at')
    return render(request, "notificationsMeds.html", {"notifications": notifications})


#Irina Majstorović 2022/0518:
@login_required
def addNotificationMeds(request):
    """
    Omogucava lekaru kreiranje novog obavestenja.

    Funkcionalnosti:

    - POST zahtev:
        - kreira novo obavestenje 
        - nakon uspesnog kreiranja, korisnik se preusmerava na listu obavestenja
    - GET zahtev:
        - prikazuje formu za kreiranje obavestenja

    **Template - GET:** 
    :template:`addNotificationMeds.html`

    **Redirect - POST:** 
    :view:`meds.views.notificationsMeds`.
       
    """
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        for_patients = bool(request.POST.get("for_patients"))

        if title and text:
            Notification.objects.create(
                author=request.user,
                title=title,
                text=text,
                for_patients=for_patients,
            )
            return redirect("meds:notificationsMeds")

    return render(request, "addNotificationMeds.html")

#Maja Miljuš 2022/0576:
@login_required
def request_specialization_upgrade(request):
    """
    **Opis:**  
    Lekar salje zahtev za vecu specijalizaciju.  
    Ako postoji vec zahtev, moze se azurirati; u suprotnom, kreira se novi zahtev.

    **Kontekst:**

    ``med``
        Instanca :model:`meds.Med` koja predstavlja trenutno ulogovanog lekara.

    ``pending``
        Instanca :model:`meds.SpecializationUpgradeRequest` sa statusom PENDING, ako vec postoji.

    **Template:**
    
    :template:`requestSpecializationUpgrade.html`
    """
    try:
        med = Med.objects.get(user=request.user)
    except Med.DoesNotExist:
        return redirect("index:index")

    pending = SpecializationUpgradeRequest.objects.filter(
        med=med, status=SpecializationUpgradeRequest.STATUS_PENDING
    ).first()

    if request.method == "POST":
        requested_level = int(request.POST.get("requested_level", med.level_spec))

        if requested_level <= med.level_spec:
            messages.error(request, "Morate izabrati nivo veći od trenutnog nivoa.")
            return redirect("meds:request_specialization_upgrade")

        if pending:
            pending.requested_level = requested_level
            pending.save()
        else:
            SpecializationUpgradeRequest.objects.create(
                med=med,
                requested_level=requested_level,
                status=SpecializationUpgradeRequest.STATUS_PENDING
            )

        messages.success(request, "Zahtev je poslat administratoru na odobrenje.")
        return redirect("meds:request_specialization_upgrade")

    context = {
        "med": med,
        "pending": pending,
    }
    return render(request, "requestSpecializationUpgrade.html", context)


#Irina Majstorović 2022/0518:
def _reset_vacation_days_if_needed(med: Med):
    """
    **Opis:**
    - Proverava da li se promenila godina za lekara i po potrebi resetuje broj dana godisnjeg odmora.
    - Ako je trenutna godina razlicita od godine u kojoj su sacuvani  godisnji odmori, azurira se  maksimalni broj dana odmora 
    - Ako je godina ista, ne radi nista.
    - Instanca lekara iz :model:`meds.Med` za koga se proverava
   
    """
    current_year = timezone.now().year
    if med.vacation_days_year != current_year:
        med.vacation_days_year = current_year
        med.vacation_days_remaining = med.vacation_days_total
        med.save(update_fields=["vacation_days_year", "vacation_days_remaining"])


#Irina Majstorović 2022/0518:
def _count_vacation_days(start_date, end_date) -> int:
    """
    Racuna broj dana izmedju dva datuma ukljucujuci oba datuma.

    """
    return (end_date - start_date).days + 1

