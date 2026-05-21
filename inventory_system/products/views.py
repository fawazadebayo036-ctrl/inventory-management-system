from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView 
from .models import Product, SaleItem, Sale, ChatMessage
from .forms import SignUpForm, ProductModelForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from .forms import SaleItemForm
import json
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime, date, timedelta











from django.views.decorators.http import require_POST
from django.conf import settings

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
    search = request.GET.get("search")
    items = Product.objects.filter(
        user=request.user.id
    ).order_by("id")
    if search:
        items = items.filter(name__icontains=search)

    total_products = items.count()

    low_stock = items.filter(
        quantity__lte=F('alert_quantity')
    ).count()

    inventory_value = sum(
        item.quantity * item.price for item in items
    )

    return render(
        request,
        "products/dashboard.html",
        {
            "items": items,
            "total_products": total_products,
            "low_stock": low_stock,
            "inventory_value": inventory_value,
            "search": search
        }
    )


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
    


@login_required(login_url="user_login")
def sales_page(request):
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        cart = json.loads(request.POST.get("cart", "[]"))

        if not cart:
            return redirect("sales_page")

        sale = Sale.objects.create(
            user=request.user,
            payment_method=payment_method
        )

        for entry in cart:
            product = Product.objects.get(id=entry["id"], user=request.user)
            qty = int(entry["quantity"])

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                price=product.price
            )

            # reduce stock
            product.quantity -= qty
            product.save()

        return redirect("sales_history")

    products = Product.objects.filter(user=request.user)
    return render(request, "products/sales_page.html", {"products": products})

@login_required(login_url="user_login")
def sales_history(request):
    sales = Sale.objects.filter(user=request.user).order_by("-created_at")

    # bar chart — sales per day
    from django.db.models import Count
    from django.db.models.functions import TruncDate

    daily_sales = (
        Sale.objects.filter(user=request.user)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    sale_labels = [str(s["date"]) for s in daily_sales]
    sale_data = [s["count"] for s in daily_sales]

    # pie chart — cash vs transfer
    cash_count = sales.filter(payment_method="cash").count()
    transfer_count = sales.filter(payment_method="transfer").count()

    return render(request, "products/sales_history.html", {
        "sales": sales,
        "sale_labels": json.dumps(sale_labels),
        "sale_data": json.dumps(sale_data),
        "cash_count": cash_count,
        "transfer_count": transfer_count,
    })


@login_required(login_url="user_login")
def inventory_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="inventory_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Inventory Report", styles["Title"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}",
        styles["Normal"]
    ))
    elements.append(Paragraph(
        f"User: {request.user.username}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 0.5 * cm))

    # Summary
    items = Product.objects.filter(user=request.user).order_by("id")
    total_products = items.count()
    low_stock = items.filter(quantity__lte=F("alert_quantity")).count()
    inventory_value = sum(item.quantity * item.price for item in items)

    summary_data = [
        ["Total Products", "Low Stock Items", "Inventory Value"],
        [str(total_products), str(low_stock), f"${inventory_value:,.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Products table
    elements.append(Paragraph("Product List", styles["Heading2"]))
    elements.append(Spacer(1, 0.3 * cm))

    table_data = [["ID", "Name", "Category", "Qty", "Price", "Status"]]

    for item in items:
        status = "Low Stock" if item.quantity <= item.alert_quantity else "OK"
        table_data.append([
            str(item.id),
            item.name,
            item.category.name if item.category else "Uncategorized",
            str(item.quantity),
            f"${item.price:,.2f}",
            status,
        ])

    product_table = Table(table_data, colWidths=[1.5*cm, 5*cm, 4*cm, 2*cm, 3*cm, 2.5*cm])
    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("PADDING", (0, 0), (-1, -1), 6),
        # red text for low stock
        *[
            ("TEXTCOLOR", (5, i + 1), (5, i + 1), colors.red)
            for i, item in enumerate(items)
            if item.quantity <= item.alert_quantity
        ],
    ]))

    elements.append(product_table)
    doc.build(elements)

    return response

@login_required(login_url="user_login")
def inventory_pdf_preview(request):
    items = Product.objects.filter(user=request.user).order_by("id")
    total_products = items.count()
    low_stock = items.filter(quantity__lte=F("alert_quantity")).count()
    inventory_value = sum(item.quantity * item.price for item in items)

    return render(request, "products/pdf_preview.html", {
        "items": items,
        "total_products": total_products,
        "low_stock": low_stock,
        "inventory_value": inventory_value,
        "now": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    })
@login_required(login_url="user_login")
def dashboard(request):
    search = request.GET.get("search")
    items = Product.objects.filter(
        user=request.user.id
    ).order_by("id")
    if search:
        items = items.filter(name__icontains=search)

    total_products = items.count()

    low_stock = items.filter(
        quantity__lte=F('alert_quantity')
    ).count()

    inventory_value = sum(
        item.quantity * item.price for item in items
    )

    # expiry warning — products expiring within 7 days
    today = date.today()
    week_ahead = today + timedelta(days=7)
    expiring_soon = items.filter(
        expiry_date__isnull=False,
        expiry_date__lte=week_ahead,
        expiry_date__gte=today
    )

    # chart data
    stock_labels = [item.name for item in items]
    stock_data = [item.quantity for item in items]

    
    category_counts = {}
    for item in items:
        cat = item.category.name if item.category else "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    category_labels = list(category_counts.keys())
    category_data = list(category_counts.values())

    return render(
        request,
        "products/dashboard.html",
        {
            "items": items,
            "total_products": total_products,
            "low_stock": low_stock,
            "inventory_value": inventory_value,
            "search": search,
            "stock_labels": json.dumps(stock_labels),
            "stock_data": json.dumps(stock_data),
            "category_labels": json.dumps(category_labels),
            "category_data": json.dumps(category_data),
            "expiring_soon": expiring_soon,
        }
    )
@login_required(login_url="user_login")
def chat_page(request):
    history = ChatMessage.objects.filter(user=request.user).order_by("created_at")

    if request.method == "POST":
        user_message = request.POST.get("message", "").strip().lower()
        if not user_message:
            return redirect("chat_page")

        ChatMessage.objects.create(user=request.user, role="user", content=request.POST.get("message", "").strip())

        # fetch data
        today = date.today()
        week_ahead = today + timedelta(days=7)
        items = Product.objects.filter(user=request.user)
        sales = Sale.objects.filter(user=request.user)

        # --- rule-based replies ---

        if any(w in user_message for w in ["low stock", "low", "running out", "restock"]):
            low = items.filter(quantity__lte=F("alert_quantity"))
            if low.exists():
                lines = "\n".join(f"• {p.name} — {p.quantity} left (alert: {p.alert_quantity})" for p in low)
                reply = f"These products are low on stock:\n{lines}"
            else:
                reply = "All products are sufficiently stocked."

        elif any(w in user_message for w in ["expir", "expire", "expiry"]):
            expiring = items.filter(expiry_date__isnull=False, expiry_date__lte=week_ahead, expiry_date__gte=today)
            if expiring.exists():
                lines = "\n".join(f"• {p.name} — expires {p.expiry_date}" for p in expiring)
                reply = f"Products expiring within 7 days:\n{lines}"
            else:
                reply = "No products are expiring within the next 7 days."

        elif any(w in user_message for w in ["total product", "how many product", "number of product", "product count"]):
            reply = f"You have {items.count()} products in your inventory."

        elif any(w in user_message for w in ["inventory value", "worth", "total value", "value"]):
            value = sum(p.quantity * p.price for p in items)
            reply = f"Your total inventory value is ${value:,.2f}."

        elif any(w in user_message for w in ["sale", "sales", "revenue", "sold"]):
            total_sales = sales.count()
            cash = sales.filter(payment_method="cash").count()
            transfer = sales.filter(payment_method="transfer").count()
            today_sales = sales.filter(created_at__date=today).count()
            reply = (
                f"Sales summary:\n"
                f"• Total sales: {total_sales}\n"
                f"• Today: {today_sales}\n"
                f"• Cash: {cash}\n"
                f"• Transfer: {transfer}"
            )

        elif any(w in user_message for w in ["most stock", "highest stock", "most quantity"]):
            top = items.order_by("-quantity").first()
            reply = f"'{top.name}' has the most stock with {top.quantity} units." if top else "No products found."

        elif any(w in user_message for w in ["least stock", "lowest stock", "least quantity"]):
            bottom = items.order_by("quantity").first()
            reply = f"'{bottom.name}' has the least stock with {bottom.quantity} units." if bottom else "No products found."

        elif any(w in user_message for w in ["category", "categories"]):
            from collections import Counter
            cats = Counter(p.category.name if p.category else "Uncategorized" for p in items)
            lines = "\n".join(f"• {cat}: {count} product(s)" for cat, count in cats.items())
            reply = f"Products by category:\n{lines}" if lines else "No categories found."

        elif any(w in user_message for w in ["hello", "hi", "hey"]):
            reply = f"Hello! Ask me about your inventory, stock levels, sales, or expiry dates."

        elif any(w in user_message for w in ["help", "what can you do", "what do you know"]):
            reply = (
                "I can answer questions like:\n"
                "• Which products are low on stock?\n"
                "• What is my inventory value?\n"
                "• Any products expiring soon?\n"
                "• How many sales today?\n"
                "• Which product has the most/least stock?\n"
                "• Show products by category"
            )

        else:
            reply = "I didn't understand that. Type 'help' to see what I can answer."

        ChatMessage.objects.create(user=request.user, role="assistant", content=reply)
        return redirect("chat_page")

    return render(request, "products/chat_page.html", {"history": history})

@login_required(login_url="user_login")
def clear_chat(request):
    ChatMessage.objects.filter(user=request.user).delete()
    return redirect("chat_page")