from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProductModelForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'category', 'price', 'description', 'alert_quantity',]