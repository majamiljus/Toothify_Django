#Irina Majstorović 2022/0518
from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """
    Model koji predstavlja obavestenje kreirano od strane :model:`auth.User`.

    Svako obaveštenje ima autora, datum kreiranja, naslov, tekst i oznaku
    da li je namenjeno pacijentima ili samo lekarima.

    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    text = models.TextField()

    for_patients = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.author.username})"





