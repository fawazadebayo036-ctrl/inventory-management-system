from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView 
from .models import Product
from .forms import SignUpForm, ProductModelForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin



# Home Page
class HomePageView(TemplateView):
    template_name = 'products/home.html'


# Register User
def register(request):

    if request.method == 'POST':

        form = SignUpForm(request.POST)

        if form.is_valid():

            user = form.save()

            # Login automatically after register
            login(request, user)

            # Redirect to dashboard
            return redirect('dashboard')

    else:
        form = SignUpForm()

    return render(request, 'products/register.html', {'form': form})


# Login User
def user_login(request):

    if request.method == 'POST':

        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            # Redirect to dashboard after login
            return redirect('dashboard')

    else:
        form = AuthenticationForm()

    return render(request, 'products/login.html', {'form': form})


# Logout User
def user_logout(request):

    logout(request)

    return render(request, "products/logout.html")


# Dashboard
@login_required(login_url="user_login")
def dashboard(request):

    items = Product.objects.filter(
        user=request.user.id
    ).order_by("id")

    return render(
        request,
        "products/dashboard.html",
        {"items": items}
    )


# Product List
def product_list(request):

    products = Product.objects.all()

    return render(
        request,
        'products/product_list.html',
        {'products': products}
    )
# class AddItemView(CreateView):
#     model = Product
#     fields = "__all__"
#     template_name = "products/add_item.html"
#     success_url = reverse_lazy("dashboard")


class AddItemView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductModelForm
    template_name = "products/add_item.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class EditItemView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductModelForm
    template_name = "products/edit_item.html"
    success_url = reverse_lazy("dashboard")

    def get_queryset(self):
        # ensures user can ONLY edit their own products
        return Product.objects.filter(user=self.request.user)    



class DeleteItemView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = "products/delete_item.html"
    success_url = reverse_lazy("dashboard")

    def get_queryset(self):
        # only allow user to delete their own products
        return Product.objects.filter(user=self.request.user)

