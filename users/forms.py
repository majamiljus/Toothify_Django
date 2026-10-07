#Irina Majstorovič 2022/0518
#Aleksandar Pavlovic 0093/2022

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from patients.models import Pat
from meds.models import Med
from django.core.exceptions import ValidationError

#Aleksandar Pavlovic 0093/2022
class CustomAuthenticationForm(AuthenticationForm):
    """
    Forma za prijavu korisnika sa srpskim label-ama i placeholder-ima.
    """
    username = forms.CharField(
        label=_("Email"),
        widget=forms.TextInput(attrs={'placeholder': _('Unesite Vaš email')})
    )
    password = forms.CharField(
        label=_("Lozinka"),
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': _('Unesite lozinku')})
    )

class CustomUserCreationForm(UserCreationForm):
    """
    **Opis:**
        Proširena forma za registraciju korisnika.
        Pored standardnih polja (username/lozinka) podržava dodatne podatke
        koje aplikacija čuva uz korisnika (npr. telefon, slika profila).

    **Napomena:**
        Logika čuvanja (save) može kreirati ili povezati dodatne entitete
        (npr. Pacijent) u zavisnosti od potrebnog toka registracije.
    """
    # USER fields
    username = forms.CharField(
        label=_("Email"),
        widget=forms.TextInput(attrs={'placeholder': _('Unesite Vaš email')})
    )
    password1 = forms.CharField(
        label=_("Lozinka"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Unesite lozinku')})
    )
    password2 = forms.CharField(
        label=_("Potvrda lozinke"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Ponovo unesite lozinku')})
    )

    # PAT fields
    name = forms.CharField(
        label=_("Ime"),
        widget=forms.TextInput(attrs={'placeholder': _('Unesite ime')})
    )
    surname = forms.CharField(
        label=_("Prezime"),
        widget=forms.TextInput(attrs={'placeholder': _('Unesite prezime')})
    )
    description = forms.CharField(
        label=_("Opis"),
        widget=forms.TextInput(attrs={'placeholder': _('Kratak opis / napomena')})
    )

    telephone = forms.CharField(required=True)
    def clean_telephone(self):
        """
        **Opis:**
            Validira format broja telefona unetog u formu.

        **Povratna vrednost:**
            Vraća očišćen (validiran) broj telefona.

        **Izuzeci:**
            Podize ValidationError ukoliko telefon nije u dozvoljenom formatu.
        """
        tel = self.cleaned_data['telephone']
        if not tel.isdigit():
            raise ValidationError("Telefon mora sadržati samo cifre")
        if len(tel) < 9:
            raise ValidationError("Telefon mora imati najmanje 9 cifara")
        if len(tel) > 11:
            raise ValidationError("Telefon može imati najviše 11 cifara")
        return tel
    
    image = forms.ImageField(
        label=_("Slika"),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2'] 
        # fields = ['username', 'password1', 'password2',
        #           'name', 'surname', 'description', 'telephone', 'image']

    def save(self, commit=True):
        """
        **Opis:**
            Kreira korisnika na osnovu podataka iz forme i upisuje dodatna polja
            (npr. telefon, slika profila). Po potrebi kreira i povezane modele
            u zavisnosti od toka registracije.

        **Parametri:**
            ``commit``
                Ako je True, snima korisnika u bazu.

        **Povratna vrednost:**
            Kreirani User objekat.
        """
        user = super().save(commit=False)  
        user.email = self.cleaned_data['username']
        user.first_name = self.cleaned_data['name']    # 
        user.last_name = self.cleaned_data['surname']  # 
        user.save()
        image = self.cleaned_data.get('image')
        if not image:
            image = 'images/defaultP.jpg'
      
        Pat.objects.create(
            user=user,
            name=self.cleaned_data['name'],
            surname=self.cleaned_data['surname'],
            description=self.cleaned_data['description'],
            email=self.cleaned_data['username'],
            telephone=self.cleaned_data['telephone'],
            image=image
        )

        return user


#Irina Majstorovič 2022/0518 
class DoctorCreationForm(UserCreationForm):
    """
    Forma za kreiranje novog doktora sa korisnickim nalogom.
    Model:
    - Koristi  :model:`auth.User` model za korisnicki nalog
    - Kreira instancu :model:`meds.Med` za doktora sa dodatnim informacijama
    """
    username = forms.CharField(
        label="Email doktora",
        widget=forms.TextInput(attrs={'placeholder': 'Unesite email doktora'}),
        help_text=""
    )
    password1 = forms.CharField(
        label="Lozinka",
        widget=forms.PasswordInput(attrs={'placeholder': 'Unesite lozinku'}),
        help_text=""
    )
    password2 = forms.CharField(
        label="Potvrda lozinke",
        widget=forms.PasswordInput(attrs={'placeholder': 'Ponovo unesite lozinku'}),
        help_text=""
    )

    name = forms.CharField(label="Ime doktora", max_length=30)
    surname = forms.CharField(label="Prezime doktora", max_length=30)
    description = forms.CharField(
        label="Opis",
        widget=forms.Textarea(attrs={'placeholder': 'Unesite kratak opis doktora'}),
        max_length=200
    )
    telephone = forms.CharField(label="Telefon", max_length=30)
    level_spec = forms.IntegerField(label="Nivo specijalizacije", min_value=1, initial=1)
    image = forms.ImageField(label="Slika", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        # username=email doktora
        fields = ("username", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

            image = self.cleaned_data.get("image")
            if not image:
                image = "images/default.jpg"

            Med.objects.create(
                user=user,
                name=self.cleaned_data["name"],
                surname=self.cleaned_data["surname"],
                description=self.cleaned_data["description"],
                email=self.cleaned_data["username"],
                telephone=self.cleaned_data["telephone"],
                level_spec=self.cleaned_data["level_spec"],
                image=image,
            )

        return user
