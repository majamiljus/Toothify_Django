from django.shortcuts import render
# Maja Miljuš 576/22
def guest(request):
    """
    **Opis:**
    Prikaz index strane gosta (neulogovanog korisnika).

    **Template:**

    :template:`indexGuest.html`
    """
    return render(request, "indexGuest.html")