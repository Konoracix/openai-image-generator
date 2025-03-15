from django.shortcuts import render
from django.http import HttpResponse
from openai import OpenAI
from django.shortcuts import redirect
import os
from .forms import ImageForm

def formPage(request):
	if request.method == "POST":

		form = ImageForm(request.POST)

		if form.is_valid():
			prompt = form.cleaned_data["prompt"]
			image_size = form.cleaned_data["image_size"]
      
			return render(request, "image_generator/image_preview.html", {
				"prompt": prompt,
				"img_size": image_size,
				"link": generateImage(prompt, image_size)
			})

	else:
		form = ImageForm()
		
	return render(request, "image_generator/form.html", {"form": form})


def generateImage(prompt, image_size = "1024x1024"):
	client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

	response = client.images.generate(
  	model="dall-e-3",
  	prompt=prompt,
  	size=image_size,
    quality="standard",
    n=1,
	)

	return response.data[0].url