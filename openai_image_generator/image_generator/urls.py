from django.urls import path

from . import views

urlpatterns = [
	path("", views.formPage),
	path("gallery", views.gallery)
]