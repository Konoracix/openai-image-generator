from django.urls import path

from . import views

urlpatterns = [
	path("", views.formPage, name="create_image_form"),
	path("gallery", views.gallery, name="gallery"),
	path("image_preview/<str:id>", views.image_preview, name="image_preview")
]