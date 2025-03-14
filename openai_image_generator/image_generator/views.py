from django.shortcuts import render
from django.http import HttpResponse
from openai import OpenAI
import os

# Create your views here.

def index(request):
	prompt = "BMW e30"
	return render(request, "image_generator/index.html", {
		# "link": generateImage(prompt),
		"link": os.getenv("EXAMPLE_PHOTO"), # Ustawione statyczne zdjęcie żeby ciągle nie generować nowych fot (taniej i szybciej ;) )
		"prompt": prompt
	})

def generateImage(prompt):
	client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

	response = client.images.generate(
  	model="dall-e-3",
  	prompt=prompt,
  	size="1024x1024",
    quality="standard",
    n=1,
	)

	return response.data[0].url
