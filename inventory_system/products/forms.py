from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Sale, SaleItem, Category


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class ProductModelForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label="Or type a new category",
        widget=forms.TextInput(attrs={'placeholder': 'Type new category name...'})
    )

    class Meta:
        model = Product
        fields = ['name', 'quantity', 'price', 'category', 'description', 'alert_quantity', 'image', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def save(self, commit=True):
        new_cat = self.cleaned_data.get("new_category")
        if new_cat:
            category, _ = Category.objects.get_or_create(name=new_cat)
            self.instance.category = category
        return super().save(commit=commit)

class SaleItemForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none()
    )
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(user=user)
