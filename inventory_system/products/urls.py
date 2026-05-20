from django.urls import path
from .views import product_list, HomePageView, register, user_login, user_logout, dashboard, AddItemView,EditItemView, DeleteItemView, sales_page, sales_history,  inventory_pdf, inventory_pdf_preview

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('products/', product_list, name='product_list'),
    path("register/", register, name="register"),
    path("login/", user_login, name="user_login"),
    path("logout/", user_logout, name="user_logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("add-item/", AddItemView.as_view(), name="add_item"),
    path("edit/<int:pk>/", EditItemView.as_view(), name="edit_item"),
    path("delete/<int:pk>/", DeleteItemView.as_view(), name="delete_item"),
    path("sales/", sales_page, name="sales_page"),
    path("sales/history/", sales_history, name="sales_history"),
    path("reports/pdf/", inventory_pdf, name="inventory_pdf"),
    path("reports/preview/", inventory_pdf_preview, name="inventory_pdf_preview"),

]