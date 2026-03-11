import json
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator

from .models import Category, MenuItem, Order, OrderItem, Purchase, PurchaseItem


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


# ── HELPERS ──────────────────────────────────────────────

def get_gst():
    return Decimal(str(getattr(settings, 'GST_PERCENT', 0)))

def generate_bill_no():
    today  = date.today()
    prefix = f"INV-{today.strftime('%Y%m%d')}"
    last   = Order.objects.filter(bill_no__startswith=prefix).count()
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


# ── PAYMENT METHOD ────────────────────────────────────────

@require_POST
def set_payment(request, bill_id):
    order  = get_object_or_404(Order, id=bill_id)
    method = request.POST.get('method', 'cash')
    if method in ('cash', 'qr'):
        order.payment_method = method
        order.save()
    return JsonResponse({'status': 'ok', 'method': method})


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


# ── PURCHASES ─────────────────────────────────────────────

@login_required(login_url='caffe_login')
def purchase_list(request):
    purchase_items = PurchaseItem.objects.all()
    today_str      = date.today().strftime('%Y-%m-%d')

    # monthly filter for history
    filter_month = request.GET.get('month', '')

    # group purchases by date for history
    all_purchases = Purchase.objects.select_related('item').all()
    if filter_month:
        try:
            year, month = filter_month.split('-')
            all_purchases = all_purchases.filter(date__year=year, date__month=month)
        except ValueError:
            filter_month = ''

    # group by date
    from itertools import groupby
    dates_purchases = {}
    for p in all_purchases:
        d = str(p.date)
        if d not in dates_purchases:
            dates_purchases[d] = []
        dates_purchases[d].append(p)

    # monthly summary
    monthly_summary = (
        Purchase.objects
        .values('date__year', 'date__month')
        .annotate(total_spent=Sum('total'))
        .order_by('-date__year', '-date__month')[:6]
    )

    return render(request, 'caffe/purchases.html', {
        'purchase_items':  purchase_items,
        'today':           today_str,
        'dates_purchases': dates_purchases,
        'monthly_summary': monthly_summary,
        'filter_month':    filter_month,
        'current_month':   date.today().strftime('%Y-%m'),
    })


@login_required(login_url='caffe_login')
@require_POST
def save_purchases(request):
    """Save all purchase entries at once"""
    shop_name  = request.POST.get('shop_name', '').strip()
    entry_date = request.POST.get('date', str(date.today()))

    if not shop_name:
        return redirect('purchase_list')

    saved = 0
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            item_id = key.replace('qty_', '')
            qty_str   = value.strip()
            price_str = request.POST.get(f'price_{item_id}', '').strip()

            if qty_str and price_str:
                try:
                    qty   = Decimal(qty_str)
                    price = Decimal(price_str)
                    if qty > 0 and price > 0:
                        item = PurchaseItem.objects.get(id=item_id)
                        Purchase.objects.create(
                            item=item,
                            shop_name=shop_name,
                            quantity=qty,
                            price=price,
                            total=qty * price,
                            date=entry_date,
                        )
                        saved += 1
                except (InvalidOperation, PurchaseItem.DoesNotExist):
                    pass

    return redirect('purchase_list')


@login_required(login_url='caffe_login')
@require_POST
def add_purchase_item(request):
    """Add new item to the grocery list"""
    name = request.POST.get('name', '').strip()
    if name:
        PurchaseItem.objects.get_or_create(name=name)
    return redirect('purchase_list')


@login_required(login_url='caffe_login')
@require_POST
def delete_purchase_item(request, item_id):
    """Remove item from grocery list"""
    get_object_or_404(PurchaseItem, id=item_id).delete()
    return redirect('purchase_list')


@login_required(login_url='caffe_login')
@require_POST
def delete_purchase(request, purchase_id):
    get_object_or_404(Purchase, id=purchase_id).delete()
    return redirect('purchase_list')


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
        .annotate(total_qty=Sum('quantity'))
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

    paginator = Paginator(orders, 20)
    page_num  = request.GET.get('page', 1)
    orders    = paginator.get_page(page_num)

    return render(request, 'caffe/bill_history.html', {
        'orders':        orders,
        'total_revenue': total_revenue,
        'bill_count':    bill_count,
        'avg_bill':      avg_bill,
        'filter_date':   filter_date,
        'search_query':  search_query,
    })


# ── PROFILE / DASHBOARD ───────────────────────────────────

@login_required(login_url='caffe_login')
def profile_dashboard(request):
    today = date.today()
    week_start  = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # ── Today stats ──
    today_orders = Order.objects.filter(created_at__date=today)
    today_revenue = today_orders.aggregate(t=Sum('grand_total'))['t'] or Decimal('0')
    today_bills   = today_orders.count()
    today_items   = OrderItem.objects.filter(order__created_at__date=today).aggregate(t=Sum('quantity'))['t'] or 0
    today_pending = today_orders.filter(payment_method='pending').count()
    today_cash    = today_orders.filter(payment_method='cash').aggregate(t=Sum('grand_total'))['t'] or Decimal('0')
    today_qr      = today_orders.filter(payment_method='qr').aggregate(t=Sum('grand_total'))['t'] or Decimal('0')

    # ── This week ──
    week_revenue = Order.objects.filter(created_at__date__gte=week_start).aggregate(t=Sum('grand_total'))['t'] or Decimal('0')
    week_bills   = Order.objects.filter(created_at__date__gte=week_start).count()

    # ── This month ──
    month_revenue = Order.objects.filter(created_at__date__gte=month_start).aggregate(t=Sum('grand_total'))['t'] or Decimal('0')
    month_bills   = Order.objects.filter(created_at__date__gte=month_start).count()

    # ── All time ──
    total_bills   = Order.objects.count()
    total_revenue = Order.objects.aggregate(t=Sum('grand_total'))['t'] or Decimal('0')

    # ── Menu stats ──
    total_menu_items = MenuItem.objects.filter(is_available=True).count()
    total_categories = Category.objects.count()

    # ── Today top 5 items ──
    top_items_today = (
        OrderItem.objects
        .filter(order__created_at__date=today)
        .values('name')
        .annotate(qty=Sum('quantity'), revenue=Sum('price'))
        .order_by('-qty')[:5]
    )

    # ── Purchases this month ──
    month_purchases = Purchase.objects.filter(date__gte=month_start).aggregate(t=Sum('total'))['t'] or Decimal('0')
    last_purchase   = Purchase.objects.order_by('-date', '-created_at').first()

    # ── Revenue last 7 days (for mini chart) ──
    daily_revenue = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = Order.objects.filter(created_at__date=d).aggregate(t=Sum('grand_total'))['t'] or 0
        daily_revenue.append({'date': d.strftime('%a'), 'amount': float(rev)})

    # ── Payment breakdown today ──
    pay_total = float(today_cash + today_qr)
    cash_pct  = round((float(today_cash) / pay_total * 100)) if pay_total > 0 else 0
    qr_pct    = 100 - cash_pct if pay_total > 0 else 0

    # ── Change password ──
    pw_error = pw_success = None
    if request.method == 'POST' and 'change_password' in request.POST:
        old_pw  = request.POST.get('old_password', '')
        new_pw  = request.POST.get('new_password1', '')
        conf_pw = request.POST.get('new_password2', '')
        if not request.user.check_password(old_pw):
            pw_error = 'Current password is incorrect.'
        elif new_pw != conf_pw:
            pw_error = 'New passwords do not match.'
        elif len(new_pw) < 6:
            pw_error = 'Password must be at least 6 characters.'
        else:
            request.user.set_password(new_pw)
            request.user.save()
            update_session_auth_hash(request, request.user)
            pw_success = 'Password changed successfully!'

    return render(request, 'caffe/profile.html', {
        # today
        'today_revenue': today_revenue,
        'today_bills':   today_bills,
        'today_items':   today_items,
        'today_pending': today_pending,
        'today_cash':    today_cash,
        'today_qr':      today_qr,
        'cash_pct':      cash_pct,
        'qr_pct':        qr_pct,
        # week
        'week_revenue':  week_revenue,
        'week_bills':    week_bills,
        # month
        'month_revenue': month_revenue,
        'month_bills':   month_bills,
        # all time
        'total_bills':   total_bills,
        'total_revenue': total_revenue,
        # menu
        'total_menu_items': total_menu_items,
        'total_categories': total_categories,
        # top items
        'top_items_today': top_items_today,
        # purchases
        'month_purchases': month_purchases,
        'last_purchase':   last_purchase,
        # chart
        'daily_revenue':   daily_revenue,
        # misc
        'today':           today,
        'user':            request.user,
        'gst_percent':     getattr(settings, 'GST_PERCENT', 0),
        'pw_error':        pw_error,
        'pw_success':      pw_success,
    })