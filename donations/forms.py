from django import forms
from django.utils import timezone
from .models import FoodDonation


class FoodDonationForm(forms.ModelForm):
    preparation_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        label="Preparation / Cooking Time"
    )
    expiry_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        label="Expiry / Best Before Time"
    )

    class Meta:
        model = FoodDonation
        fields = [
            'food_name',
            'category',
            'food_type',
            'quantity',
            'unit',
            'storage_requirements',
            'description',
            'preparation_datetime',
            'expiry_datetime',
            'pickup_location',
            'pickup_time',
            'image',
            'contact_person',
            'contact_phone',
        ]
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 40 Packets Vegetable Pulao & Dal'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'food_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1', 'placeholder': 'Quantity'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'storage_requirements': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List ingredients, packing details, allergen warnings...'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pickup address, area, or establishment landmark'}),
            'pickup_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Today 2:00 PM – 5:30 PM'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of person at pickup location'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if hasattr(image, 'size') and image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file size cannot exceed 5MB.")
            if hasattr(image, 'name'):
                ext = image.name.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    raise forms.ValidationError("Unsupported image format. Allowed formats: JPG, JPEG, PNG, WEBP, GIF.")
        return image

    def clean(self):
        cleaned_data = super().clean()
        prep = cleaned_data.get('preparation_datetime')
        exp = cleaned_data.get('expiry_datetime')
        
        if prep and exp:
            if exp <= prep:
                self.add_error('expiry_datetime', "Expiry date/time must be strictly after the preparation time.")
            if exp < timezone.now():
                self.add_error('expiry_datetime', "Expiry date/time cannot be in the past.")
        return cleaned_data
