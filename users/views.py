#Irina Majstorovic 0518/2022 
#Aleksandar Pavlovic 0093/2022
#Maja Miljuš 2022/0576
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login
from patients.models import Pat
from django.contrib.auth.models import User
from meds.models import SpecializationUpgradeRequest
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from meds.models import Med, Vacation
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from meds.models import Med, Vacation
from .forms import DoctorCreationForm
from .models import Notification
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta
from calendar import monthrange
from django.contrib import messages
from meds.models import WorkTime, Vacation, Med
from django.urls import reverse
from index.models import AllInterventions

#Aleksandar Pavlovic 0093/2022:
def index(request):
    """
    **Opis:**
        Prikazuje početnu (index) stranicu aplikacije.

    **Parametri:**
        ``request``
            Django HttpRequest objekat.

    **Povratna vrednost:**
        Renderovana HTML strana:
        :template:`index.html`.
    """
    return render(request, 'index.html')


def login_view(request):
    """
    **Opis:**
        Obrada prijave korisnika na sistem.
        Za POST zahteve validira formu za autentifikaciju i prijavljuje korisnika.
        Nakon uspešne prijave vrši preusmerenje u zavisnosti od uloge korisnika.

    **Parametri:**
        ``request``
            Django HttpRequest objekat (GET prikazuje formu, POST obrađuje prijavu).

    **Povratna vrednost:**
        - Renderuje :template:`login.html` sa formom za prijavu.
        - Redirect na :view:`users.views.admin_dashboard` ako je korisnik administrator.
        - Redirect na :view:`index.views.index_doctor` ako je korisnik lekar.
        - Redirect na :view:`index.views.index` za ostale korisnike.
    """
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            
            if user.is_staff:
                return redirect('users:admin_dashboard')

            if Med.objects.filter(user=user).exists():
                return redirect('index:doctor_home')

            return redirect('index:index')
    else:
        form = CustomAuthenticationForm()
    return render(request, "login.html", {"form": form})


def signup(request):
    """
    **Opis:**
        Registracija novog korisnika.
        Na POST zahtevu validira ``CustomUserCreationForm``, proverava da li korisnik već postoji
        i kreira novog korisnika. Nakon uspešne registracije korisnik se automatski prijavljuje.

    **Parametri:**
        ``request``
            Django HttpRequest objekat (GET prikazuje formu, POST obrađuje registraciju).

    **Povratna vrednost:**
        - Render :template:`signUp.html` sa formom (GET ili nevalidan POST)
        - Redirect na :view:`index.views.index` nakon uspešne registracije i prijave
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        
        if form.is_valid():
            username = form.cleaned_data.get('username') 
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Korisnik sa ovim emailom već postoji.')
            else:
                user = form.save()
                login(request, user)
                return redirect('index:index')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signUp.html', {'form': form})


@login_required
def deactivate_account(request):
    """
    **Opis:**
        Deaktivira nalog trenutno ulogovanog korisnika.
        Deaktivacija se izvršava samo na POST zahtev.
        Nakon deaktivacije korisnik se odjavljuje i dobija poruku upozorenja.

    **Parametri:**
        ``request``
            Django HttpRequest objekat.

    **Povratna vrednost:**
        - Na GET zahtevu renderuje :template:`deactivateConfirm.html`.
        - Na POST zahtevu deaktivira nalog, odjavljuje korisnika i radi redirect na :view:`guest.views.guest`.
    """
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        messages.warning(request, "Nalog je deaktiviran. Za reaktivaciju se obratite administratoru.")
        return redirect('guest:guest')
    return render(request, 'deactivateConfirm.html')


@login_required
def user_logout(request):
    """
    **Opis:**
        Odjavljuje trenutno ulogovanog korisnika iz sistema.

    **Parametri:**
        ``request``
            Django HttpRequest objekat.

    **Povratna vrednost:**
        Redirect na gostujuću početnu stranicu :view:`guest.views.guest`.
    """
    logout(request)
    return redirect('guest:guest') 



#Maja Miljuš 2022/0576:
@staff_member_required
def approve_spec_request(request, req_id):
    """
    **Opis:**  
        Odobravanje zahteva za vecom specijalizacijom lekara.
        Postavlja status zahteva na odobren,
        a zatim azurira nivo specijalizacije lekara.

    **Kontekst:**  
        ``req``  
            Instanca :model:`meds.SpecializationUpgradeRequest` koja se odobrava.  
        ``med``  
            Instanca :model:`meds.Med` ciji se nivo specijalizacije menja.

    **Povratna vrednost:**  
        :view:`users.views.admin_dashboard`.
    """
    req = get_object_or_404(SpecializationUpgradeRequest, pk=req_id)

    req.status = 1
    req.decided_at = timezone.now()
    req.decided_by = request.user
    req.save()

    med = req.med
    med.level_spec = req.requested_level
    med.save()

    return redirect("users:admin_dashboard")


@staff_member_required
def reject_spec_request(request, req_id):
    """
    **Opis:**  
        Odbijanje zahteva za vecu specijalizaciju lekara.
        Postavlja status zahteva na odbijen,
        a zatim preusmerava korisnika na administrativni panel.

    **Kontekst:**  
        ``req``  
            Instanca :model:`meds.SpecializationUpgradeRequest` koja se odbija.  
        ``admin_note``  
            Tekst koji administrator unese prilikom odbijanja zahteva.

    **Povratna vrednost:**  
       :view:`users.views.admin_dashboard`.
    """
    req = get_object_or_404(SpecializationUpgradeRequest, pk=req_id)

    req.status = -1
    req.decided_at = timezone.now()
    req.decided_by = request.user
    req.admin_note = request.POST.get("admin_note", "").strip()
    req.save()

    return redirect("users:admin_dashboard")



#Irina Majstorovic 0518/2022:
@staff_member_required
def admin_dashboard(request):
    """
    Prikazuje pocetnu stranu admina sa pregledom svih kljucnih informacija u sistemu.

    Funkcionalnosti:

    - Prikazuje odmor lekara prema statusu (na cekanju, odobren, odbijen)
    - Prikazuje obavestenja namenjena pacijentima i lekarima
    - Prikazuje zahteve za unapredjenje specijalizacije lekara
    - Omogucava pregled svih intervencija

    **Template :** 
    :template:`adminDashboard.html`

    """
    if not request.user.is_staff:
        return redirect('index')

    med_map = {m.id: m for m in Med.objects.all()}

    PENDING_STATUS = 0 #na cekanju
    APPROVED_STATUS = 1 #odobren
    REJECTED_STATUS = -1 #odbijen

    pending_qs = Vacation.objects.filter(status=PENDING_STATUS)
    approved_qs = Vacation.objects.filter(status=APPROVED_STATUS)
    rejected_qs = Vacation.objects.filter(status=REJECTED_STATUS)

    pending_vacations = [
        {
            "vac": v,
            "doctor": v.idMed,
        }
        for v in pending_qs.select_related("idMed")
    ]

    notifications_public = Notification.objects.filter(
        for_patients=True
    ).order_by('-created_at')

    notifications_staff = Notification.objects.filter(
        for_patients=False
    ).order_by('-created_at')

    pending_spec_requests = SpecializationUpgradeRequest.objects.filter(status=0).select_related("med").order_by("-created_at")

    context = {
        "pending_vacations": pending_vacations,
        "approved_vacations": approved_qs,
        "rejected_vacations": rejected_qs,
        "doctors": Med.objects.filter(is_active=True),
        "notifications_public": notifications_public,
        "notifications_staff": notifications_staff,
        "pending_spec_requests": pending_spec_requests,
        "interventions": AllInterventions.objects.all().order_by("level", "description"),

    }
    return render(request, "adminDashboard.html", context)


@staff_member_required
def approve_vacation(request, vac_id):
    """
    Odobrava zahtev za godisnji odmor lekara.

    Funkcionalnosti:

    - Menja status izabranog odmora na 'odobren' (status=1)
    - Brise svo radno vreme lekara koje se poklapa sa odobrenim odmorom


    **Redirect :** 
    :view:`users.views.admin_dashboard`
    """
    vac = get_object_or_404(Vacation, pk=vac_id)
    vac.status = 1
    vac.save()

    WorkTime.objects.filter(
        idMed=vac.idMed,
        date__range=(vac.startDate, vac.endDate)
    ).delete()

    return redirect('users:admin_dashboard')


@staff_member_required
def reject_vacation(request, vac_id):
    """
    Odbija zahtev za godisnji odmor lekara i vraca odgovarajuci broj dana odmora.

    Funkcionalnosti:

    - Proverava da li je status odmora "na cekanju" (status=0),ako jeste vraca broj dana koji je bio rezervisan ovim zahtevom
    - Postavlja status odmora na "odbijen" (status=-1)

    **Redirect :** 
    :view:`users.views.admin_dashboard`
    """
    vac = get_object_or_404(Vacation, pk=vac_id)

   
    if vac.status == 0:
        med = vac.idMed

       
        current_year = timezone.now().year
        if med.vacation_days_year != current_year:
            med.vacation_days_year = current_year
            med.vacation_days_remaining = med.vacation_days_total

        days = (vac.endDate - vac.startDate).days + 1
        med.vacation_days_remaining += days
        if med.vacation_days_remaining > med.vacation_days_total:
            med.vacation_days_remaining = med.vacation_days_total
        med.save(update_fields=["vacation_days_year", "vacation_days_remaining"])

    vac.status = -1
    vac.save()
    return redirect('users:admin_dashboard')


@staff_member_required
def create_doctor(request):
    """
    Omogucava adminu kreiranje novog doktora sa korisnickim nalogom.

    Funkcionalnosti:

    - GET zahtev:
        - Prikazuje formu za kreiranje novog doktora.
        - Template: :template:`createDoctor.html`
    
    - POST zahtev:
        - Validira podatke iz forme DoctorCreationForm
        - Ako su podaci ispravni:
            - Kreira korisnicki nalog :model:`auth.User`
            - Kreira instancu doktora :model:`meds.Med`
        - Ako podaci nisu ispravni:
            - Vraca formu sa greskama

 
    - Template (GET): :template:`createDoctor.html`
    - Redirect (POST, uspesno kreiranje): :view:`users.views.admin_dashboard`
    """
    if request.method == "POST":
        form = DoctorCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Doktor je uspešno dodat.")
            return redirect("users:admin_dashboard")
    else:
        form = DoctorCreationForm()

    return render(request, "createDoctor.html", {"form": form})


@staff_member_required
def deactivate_doctor(request, med_id):
    """
    Brisanje korisnickog naloga doktora od strane admina.

    **Redirect :** 
    :view:`users.views.admin_dashboard`

    """
    doctor = get_object_or_404(Med, pk=med_id)
    doctor.is_active = False
    doctor.save()

    if doctor.user:
        doctor.user.is_active = False
        doctor.user.save()

    messages.warning(request, f"Doktor {doctor.name} {doctor.surname} je deaktiviran.")
    return redirect("users:admin_dashboard")


@login_required
def notifications_view(request):
    """
    Kreiranje i pregled obavestenja za lekare i pacijente.

    **Funkcionalnosti:**

    - GET zahtev:
        - Prikazuje listu svih obavestenja
    - POST zahtev:
        - Kreira novo obavestenje sa naslovom i tekstom

    **Template:**
    - :template:`notifications.html`
    """
    if not (request.user.is_staff or is_doctor(request.user)):
        return redirect("index")

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
            return redirect("notifications")

    notifications = Notification.objects.all()

    context = {
        "notifications": notifications,
    }
    return render(request, "notifications.html", context)


@staff_member_required
def add_notification(request):
    """
    Admin kreira  novo obavestenje.

    **Funkcionalnosti:**

    - GET zahtev:
        - Prikazuje formu za kreiranje novog obavestenja
        - Template koristi: :template:`addNotification.html`

    - POST zahtev:
        - Kreira novo obavestenje sa naslovom i tekstom
        - Nakon uspesnog kreiranja :view:`users.views.admin_dashboard`.
        
    **Template:**
    - :template:`addNotification.html`
    """
    if not request.user.is_staff:
        return redirect('/')

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
            return redirect(f"{reverse('users:admin_dashboard')}#section-content")

    return render(request, "addNotification.html")


@staff_member_required
def delete_notification(request, notification_id):
    """
    Funkcija za brisanje postojeceg obavestenja od strane admina.
    **Redirect:**
    - Nakon brisanja: :view:`users.views.admin_dashboard`.
    """
    if not request.user.is_staff:
        return redirect('index')

    notification = get_object_or_404(Notification, id=notification_id)

    if request.method == "POST":
        notification.delete()

    return redirect(f"{reverse('users:admin_dashboard')}#section-content")


@staff_member_required
def add_intervention(request):
    """
    Funkcija za dodavanje nove intervencije u ordinaciju od strane admina.

    **Funkcionalnosti:**

    - POST zahtev:
        - Provera polja iz forme.
        - Kreira instancu :model:`index.AllInterventions`
        - Prikazuje success poruku

    - GET zahtev:
        - Prikazuje formu za dodavanje intervencije
        - Template: :template:`addIntervention.html`
        
    **Redirect:**
    -  :view:`users.views.admin_dashboard`
    """
    if request.method == "POST":
        description = request.POST.get("description", "").strip()
        duration_raw = request.POST.get("duration", "").strip()
        price_raw = request.POST.get("price", "").strip()
        level_raw = request.POST.get("level", "").strip()

        if not description:
            messages.error(request, "Naziv intervencije je obavezan.")
            return render(request, "addIntervention.html")

        try:
            duration = int(duration_raw)
        except ValueError:
            messages.error(request, "Trajanje mora biti broj (u minutima).")
            return render(request, "addIntervention.html")

        try:
            level = int(level_raw)
        except ValueError:
            messages.error(request, "Nivo mora biti broj.")
            return render(request, "addIntervention.html")

        try:
            price = Decimal(price_raw)
        except (InvalidOperation, ValueError):
            messages.error(request, "Cena mora biti broj.")
            return render(request, "addIntervention.html")

        AllInterventions.objects.create(
            description=description,
            duration=duration,
            price=price,
            level=level
        )
        messages.success(request, "Intervencija je dodata.")
        return redirect("users:admin_dashboard")

    return render(request, "addIntervention.html")


@staff_member_required
def delete_intervention(request, intervention_id):
    """
    Brisanje postojece intervencije iz ordinacije od strane admina.
    **Redirect:**  :view:`users.views.admin_dashboard`
    """
    intervention = get_object_or_404(AllInterventions, id=intervention_id)
    if request.method == "POST":
        intervention.delete()
        messages.success(request, "Intervencija je obrisana.")
    return redirect("users:admin_dashboard")


@staff_member_required
def admin_worktime(request):
    """
    Prikazuje pregled radnog vremena lekara za izabrani mesec.
    Admin ima pregled koji lekari sve rade, ko je na odmoru i ko nema radno vreme.

    **Template:**
    - :template:`adminWorktime.html`

    **Kontekst:**

    - year: godina prikazanog meseca

    - month: mesec (broj)

    - month_str: string u formatu "YYYY-MM"

    - days: lista dana sa statusom lekara

    - doctors: lista aktivnih lekara

  
    """
    month_str = request.GET.get("month")
    if month_str:
        year, month = map(int, month_str.split("-"))
    else:
        today = date.today()
        year, month = today.year, today.month

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    doctors = Med.objects.filter(is_active=True).order_by("surname", "name")

   
    wt_qs = WorkTime.objects.filter(date__range=(first_day, last_day))
    wt_map = {(w.idMed_id, w.date): w for w in wt_qs}

  
    vac_qs = Vacation.objects.filter(
        status=1,
        startDate__lte=last_day,
        endDate__gte=first_day
    )
 
    vac_days = set()
    for v in vac_qs:
        d = max(v.startDate, first_day)
        end = min(v.endDate, last_day)
        while d <= end:
            vac_days.add((v.idMed_id, d))
            d += timedelta(days=1)

    days = []
    d = first_day
    while d <= last_day:
        rows = []
        for doc in doctors:
            if (doc.id, d) in vac_days:
                rows.append({
                    "doc": doc,
                    "status": "vacation",
                    "text": "NA ODMORU"
                })
            else:
                w = wt_map.get((doc.id, d))
                if w:
                    rows.append({
                        "doc": doc,
                        "status": "work",
                        "text": f"{w.startTime.strftime('%H:%M')}–{w.endTime.strftime('%H:%M')}"
                    })
                else:
                    rows.append({
                        "doc": doc,
                        "status": "off",
                        "text": "Ne radi"
                    })
        days.append({"date": d, "rows": rows})
        d += timedelta(days=1)

    context = {
        "year": year,
        "month": month,
        "month_str": f"{year:04d}-{month:02d}",
        "days": days,
        "doctors": doctors,
    }
    return render(request, "adminWorktime.html", context)


@staff_member_required
def worktime_plan(request):
    """
    Administrator pravi radno vreme lekara ili ga menja.

    **Funkcionalnosti:**
    
    - GET zahtev:
        - Prikazuje listu svih aktivnih lekara.
        - Prikazuje moguce smene koje mogu da se odaberu:
            - "08:00–16:00" (Prva smena)
            - "12:00–20:00" (Druga smena)
            - "14:00–22:00" (Treca smena)
            - "Ne radi" (OFF)
    
    - POST zahtev:
        - Proverava da li je lekar na  odmoru  taj dan. Ako jeste, ne dozvoljava dodavanje radnog vremena.
        - Ako je izabrano "OFF", brise postojece radno vreme za taj dan.
        - Za smene dodaje ili azurira radno vreme.

    **Template:**
    - :template:`workTime.html`

    **Kontekst:**

    - doctors : lista svih aktivnih lekara

    - shift_choices : lista svih dostupnih smena
    """
    doctors = Med.objects.filter(is_active=True).order_by("surname", "name")

    SHIFT_CHOICES = [
        ("08-16", "08:00–16:00"),
        ("12-20", "12:00–20:00"),
        ("14-22", "14:00–22:00"),
        ("OFF", "Ne radi"),
    ]

    if request.method == "POST":
        doc_id = int(request.POST.get("doctor_id"))
        date_str = request.POST.get("date")
        shift = request.POST.get("shift")

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            messages.error(request, "Neispravan datum.")
            return redirect("users:worktime_plan")

        # Ako je odobren odmor -> zabrani
        on_vacation = Vacation.objects.filter(
            idMed_id=doc_id,
            status=1,
            startDate__lte=selected_date,
            endDate__gte=selected_date
        ).exists()
        if on_vacation:
            messages.error(request, "Ne možeš da dodaš radno vreme: doktor je na odobrenom odmoru.")
            return redirect("users:worktime_plan")

        if shift == "OFF":
            WorkTime.objects.filter(idMed_id=doc_id, date=selected_date).delete()
            messages.success(request, "Sačuvano: doktor ne radi taj dan.")
            return redirect("users:admin_worktime")

        shift_map = {
            "08-16": ("08:00", "16:00", "Prva smena"),
            "12-20": ("12:00", "20:00", "Druga smena"),
            "14-22": ("14:00", "22:00", "Treća smena"),
        }
        start_s, end_s, shift_name = shift_map[shift]
        start_t = datetime.strptime(start_s, "%H:%M").time()
        end_t = datetime.strptime(end_s, "%H:%M").time()

        wt, _ = WorkTime.objects.get_or_create(idMed_id=doc_id, date=selected_date)
        wt.startTime = start_t
        wt.endTime = end_t
        wt.shiftName = shift_name
        # pauza (npr 30 min)
        break_dt = datetime.combine(selected_date, start_t) + timedelta(hours=4)
        wt.breakTime = break_dt.time()
        wt.save()

        messages.success(request, "Radno vreme sačuvano.")
        return redirect("users:admin_worktime")

    return render(request, "workTime.html", {"doctors": doctors, "shift_choices": SHIFT_CHOICES})







