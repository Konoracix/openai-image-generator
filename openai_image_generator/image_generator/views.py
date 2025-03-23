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
from itertools import chain

def formPage(request):
	if request.method == "POST":

		form = ImageForm(request.POST)

		if form.is_valid():
			prompt = form.cleaned_data["prompt"]
			image_size = form.cleaned_data["image_size"]

			generated_image_url = generateImage(prompt, image_size)
			s3_data = sendImageToS3(generated_image_url)

			Image.objects.create(image_id=s3_data["uuid"], prompt=prompt, size=image_size)

			return render(
				request,
				"image_generator/image_preview.html",
				{"prompt": prompt, "img_size": image_size, "link": s3_data["s3_image_url"]},
			)

	else:
		form = ImageForm()

	return render(request, "image_generator/form.html", {"form": form})

def gallery(request):
	images_1024x1024 = Image.objects.filter(size="1024x1024").order_by("-created_at")
	images_1792x1024 = Image.objects.filter(size="1792x1024").order_by("-created_at")
	images_1024x1792 = Image.objects.filter(size="1024x1792").order_by("-created_at")

	images = list(chain(images_1024x1024, images_1792x1024, images_1024x1792))
	
	for image in images:
		image.link = generateS3ImageLink(image.image_id)
	
	return render(request, "image_generator/gallery.html", {"images": images})

def image_preview(request, id):
	image = Image.objects.get(image_id=id)
	return render(
				request,
				"image_generator/image_preview.html",
				{"prompt": image.prompt, "img_size": image.size, "link": generateS3ImageLink(id)},
			)

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

	s3_image_url = generateS3ImageLink(image_uuid)
	
	return {
			"s3_image_url": s3_image_url,
			"uuid": image_uuid
		}

def generateS3Link(file_name):
	return f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/{file_name}"

def generateS3ImageLink(image_id):

	return f"https://{os.getenv('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/generated_images/{image_id}.png"

