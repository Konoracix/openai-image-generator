from django import forms

class ImageForm(forms.Form):
    prompt = forms.CharField(label="prompt", max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    image_size = forms.ChoiceField(
      label="Size",
			choices=[("1024x1024", "1024x1024"), ("1792x1024", "1792x1024"), ("1024x1792", "1024x1792")],
      widget=forms.Select(attrs={'class': 'form-select'})
    )