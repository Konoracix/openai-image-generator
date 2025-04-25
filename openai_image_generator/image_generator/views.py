from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from openai import OpenAI
from django.shortcuts import redirect
from io import BytesIO
from .forms import ImageForm
import requests
import uuid
import boto3
import os
import numpy as np
from  image_generator.models import Image
from itertools import chain
import json
from sklearn.metrics.pairwise import cosine_similarity

def formPage(request):
	if request.method == "POST":

		form = ImageForm(request.POST)

		if form.is_valid():
			prompt = form.cleaned_data["prompt"]
			image_size = form.cleaned_data["image_size"]

			generated_image_url = generateImage(prompt, image_size)
			s3_data = sendImageToS3(generated_image_url)

			Image.objects.create(image_id=s3_data["uuid"], prompt=prompt, size=image_size, embedding=create_embedding(prompt))

			return render(
				request,
				"image_generator/image_preview.html",
				{"prompt": prompt, "img_size": image_size, "link": s3_data["s3_image_url"], "id": s3_data["uuid"]},
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
	
	return render(request, "image_generator/gallery.html", {"images": images, "Title": "Gallery"})

def image_preview(request, id):
	image = Image.objects.get(image_id=id)
	return render(
				request,
				"image_generator/image_preview.html",
				{"prompt": image.prompt, "img_size": image.size, "link": generateS3ImageLink(id), "id":	id},
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


def delete_image(request, id):
	s3 = boto3.client(
		"s3",
		aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
		aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
	)

	s3.delete_object(
		Bucket=os.getenv("AWS_STORAGE_BUCKET_NAME"),
		Key=f"generated_images/{id}.png",
	)

	Image.objects.get(image_id=id).delete()

	return gallery(request)

def generate_embeddings(request):
	images = Image.objects.all();
	
	for image in images:
		image.embedding = create_embedding(image.prompt)
		image.save()
	return JsonResponse({"message": "Embeddings genereted"})

def create_embedding(data):
	client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
	embedding = client.embeddings.create(
    input=data,
    model="text-embedding-ada-002"
  ) 
	return embedding.data[0].embedding

def search_images(images, search_prompt):
	search_prompt_embedding = create_embedding(search_prompt)
	searched_images = []
	for image in images:
		if compare_embeddings(image.embedding, search_prompt_embedding) > 0.84:
			searched_images.append({"image_id": image.image_id,
				"prompt": image.prompt,
				"size": image.size,
				"created_at": image.created_at,
				"link": generateS3ImageLink(image.image_id)
			})
	return searched_images
	

def test(request):
	images = Image.objects.all()
	search_prompt = "Kostka rubika"
	return render(request, "image_generator/gallery.html", {"images": search_images(images, search_prompt), "Title": ("Search: "+search_prompt)})
	# return JsonResponse({"images": search_images(images, "butelka")})

def compare_embeddings(emb1, emb2):
	return cosine_similarity(np.array(emb1).reshape(1, -1), np.array(emb2).reshape(1, -1))[0][0]

