from django.db import models

# Create your models here.
class Image(models.Model):
	image_id = models.UUIDField(primary_key=True)
	prompt = models.CharField(max_length=4000)
	created_at = models.DateTimeField(auto_now=True)
