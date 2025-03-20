from django.shortcuts import render
from django.http import HttpResponse
from openai import OpenAI
from django.shortcuts import redirect
from io import BytesIO
from .forms import ImageForm
import requests
import uuid
import boto3
import os
from  image_generator.models import Image

def formPage(request):
	if request.method == "POST":

		form = ImageForm(request.POST)

		if form.is_valid():
			prompt = form.cleaned_data["prompt"]
			image_size = form.cleaned_data["image_size"]

			generated_image_url = generateImage(prompt, image_size)
			s3_data = sendImageToS3(generated_image_url)

			Image.objects.create(image_id=s3_data["uuid"], prompt=prompt)

			return render(
				request,
				"image_generator/image_preview.html",
				{"prompt": prompt, "img_size": image_size, "link": s3_data["s3_image_url"]},
			)

	else:
		form = ImageForm()

	return render(request, "image_generator/form.html", {"form": form})


def generateImage(prompt, image_size="1024x1024"):
	client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

	response = client.images.generate(
		model="dall-e-3",
		prompt=prompt,
		size=image_size,
		quality="standard",
		n=1,
	)

	return response.data[0].url


def sendImageToS3(image_url):
	image_response = requests.get(image_url)
	image_data = BytesIO(image_response.content)

	s3 = boto3.client(
		"s3",
		aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
		aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
	)

	image_uuid = str(uuid.uuid4())

	s3_filename = f"generated_images/{image_uuid}.png"

	s3.upload_fileobj(
		image_data,
		os.getenv("AWS_STORAGE_BUCKET_NAME"),
		s3_filename,
		ExtraArgs={"ContentType": "image/png"},
	)

	s3_image_url = (
		f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/{s3_filename}"
	)
	
	return {
			"s3_image_url": s3_image_url,
			"uuid": image_uuid
		}

