from django.db import models
from pgvector.django import VectorField

# Create your models here.
class Image(models.Model):
	image_id = models.UUIDField(primary_key=True)
	prompt = models.CharField(max_length=4000)
	size = models.CharField(max_length=20, default="")
	created_at = models.DateTimeField(auto_now=True)
	embedding = VectorField(dimensions=1536, null=True)

	def __str__(self):
			return f'{self.image_id} - "{self.prompt}"'
