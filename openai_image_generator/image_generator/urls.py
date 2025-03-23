from django.urls import path

from . import views

urlpatterns = [
	path("", views.formPage),
	path("gallery", views.gallery),
	path("image_preview/<str:id>", views.image_preview, name="image_preview")
]