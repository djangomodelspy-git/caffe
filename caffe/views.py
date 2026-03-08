import json
from decimal import Decimal
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Avg
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


from .models import Category, MenuItem, Order, OrderItem


# ── AUTH ─────────────────────────────────────────────────

def caffe_login(request):
    if request.user.is_authenticated:
        return redirect('order_screen')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('order_screen')
        error = 'Wrong username or password'
    return render(request, 'caffe/login.html', {'error': error})


def caffe_logout(request):
    logout(request)
    return redirect('caffe_login')


# ── helpers ──────────────────────────────────────────────

def get_gst():
    return Decimal(str(getattr(settings, 'GST_PERCENT', 0)))

def generate_bill_no():
    today = date.today()
    prefix = f"INV-{today.strftime('%Y%m%d')}"
    last = Order.objects.filter(bill_no__startswith=prefix).count()
    return f"{prefix}-{str(last + 1).zfill(3)}"


# ── ORDER SCREEN ─────────────────────────────────────────

@login_required(login_url='caffe_login')
def order_screen(request):
    categories = Category.objects.prefetch_related('menuitem_set').all()
    data = []
    for cat in categories:
        items = cat.menuitem_set.filter(is_available=True)
        if items.exists():
            data.append({'category': cat, 'items': items})

    no_cat = MenuItem.objects.filter(category=None, is_available=True)
    if no_cat.exists():
        data.append({'category': None, 'items': no_cat})

    return render(request, 'caffe/order.html', {'data': data})


# ── GENERATE BILL ─────────────────────────────────────────

@require_POST
def generate_bill(request):
    try:
        body  = json.loads(request.body)
        items = body.get('items', [])
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    if not items:
        return JsonResponse({'error': 'No items'}, status=400)

    order    = Order.objects.create(bill_no=generate_bill_no())
    subtotal = Decimal('0')

    for entry in items:
        menu_item = get_object_or_404(MenuItem, id=entry['id'])
        qty       = int(entry['qty'])
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            name=menu_item.name,
            price=menu_item.price,
            quantity=qty,
        )
        subtotal += menu_item.price * qty

    gst_percent = get_gst()
    tax         = (subtotal * gst_percent / 100).quantize(Decimal('0.01'))
    grand_total = subtotal + tax

    order.subtotal    = subtotal
    order.tax         = tax
    order.grand_total = grand_total
    order.save()

    return JsonResponse({'bill_id': order.id})


# ── BILL PREVIEW ──────────────────────────────────────────

@login_required(login_url='caffe_login')
def bill_view(request, bill_id):
    order = get_object_or_404(Order, id=bill_id)
    return render(request, 'caffe/receipt.html', {
        'order':       order,
        'gst_percent': get_gst(),
    })


# ── MENU MANAGER ──────────────────────────────────────────

@login_required(login_url='caffe_login')
def menu_manager(request):
    categories = Category.objects.all()
    items      = MenuItem.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'caffe/menu_manager.html', {
        'categories': categories,
        'items':      items,
    })


@require_POST
def add_item(request):
    name   = request.POST.get('name', '').strip()
    price  = request.POST.get('price', '0')
    cat_id = request.POST.get('category', '')

    if not name:
        return redirect('menu_manager')

    category = Category.objects.filter(id=cat_id).first() if cat_id else None
    MenuItem.objects.create(name=name, price=Decimal(price), category=category)
    return redirect('menu_manager')


@require_POST
def edit_item(request, item_id):
    item          = get_object_or_404(MenuItem, id=item_id)
    item.name     = request.POST.get('name', item.name).strip()
    item.price    = Decimal(request.POST.get('price', item.price))
    cat_id        = request.POST.get('category', '')
    item.category = Category.objects.filter(id=cat_id).first() if cat_id else None
    item.is_available = request.POST.get('is_available') == 'on'
    item.save()
    return redirect('menu_manager')


@require_POST
def delete_item(request, item_id):
    get_object_or_404(MenuItem, id=item_id).delete()
    return redirect('menu_manager')


@require_POST
def add_category(request):
    name = request.POST.get('name', '').strip()
    if name:
        Category.objects.get_or_create(name=name)
    return redirect('menu_manager')


# ── SALES REPORT ──────────────────────────────────────────

@login_required(login_url='caffe_login')
def sales_report(request):
    filter_date = request.GET.get('date', str(date.today()))
    try:
        report_date = date.fromisoformat(filter_date)
    except ValueError:
        report_date = date.today()

    orders = Order.objects.filter(
        created_at__date=report_date
    ).prefetch_related('items').order_by('-created_at')

    total_revenue = orders.aggregate(t=Sum('grand_total'))['t'] or 0
    bill_count    = orders.count()

    top_items = (
        OrderItem.objects
        .filter(order__created_at__date=report_date)
        .values('name')
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price'))
        .order_by('-total_qty')[:5]
    )

    return render(request, 'caffe/sales_report.html', {
        'orders':        orders,
        'total_revenue': total_revenue,
        'bill_count':    bill_count,
        'top_items':     top_items,
        'report_date':   report_date,
    })


# ── BILL HISTORY ──────────────────────────────────────────

@login_required(login_url='caffe_login')
def bill_history(request):
    filter_date  = request.GET.get('date', '')
    search_query = request.GET.get('q', '').strip()

    orders = Order.objects.prefetch_related('items').order_by('-created_at')

    if filter_date:
        try:
            d = date.fromisoformat(filter_date)
            orders = orders.filter(created_at__date=d)
        except ValueError:
            filter_date = ''

    if search_query:
        orders = orders.filter(bill_no__icontains=search_query)

    total_revenue = orders.aggregate(t=Sum('grand_total'))['t'] or 0
    bill_count    = orders.count()
    avg_bill      = round(total_revenue / bill_count, 2) if bill_count else 0

    paginator  = Paginator(orders, 20)
    page_num   = request.GET.get('page', 1)
    orders     = paginator.get_page(page_num)

    return render(request, 'caffe/bill_history.html', {
        'orders':       orders,
        'total_revenue': total_revenue,
        'bill_count':   bill_count,
        'avg_bill':     avg_bill,
        'filter_date':  filter_date,
        'search_query': search_query,
    })