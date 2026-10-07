"""
ASGI config for projekat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.projekat.com/en/5.2/howto/deployment/asgi/
"""

#Minja Krivokapic 0615/2022
#ASGI ulazna tačka (async deployment). Izlaže application za ASGI server (uvodi DJANGO_SETTINGS_MODULE i poziva get_asgi_application()).
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projekat.settings')

application = get_asgi_application()
