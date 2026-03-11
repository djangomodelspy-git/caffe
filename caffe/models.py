from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category     = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name         = models.CharField(max_length=100)
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('cash',    'Cash'),
        ('qr',      'QR / PhonePe'),
    ]
    bill_no        = models.CharField(max_length=20, unique=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    subtotal       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='pending')

    def __str__(self):
        return self.bill_no


class OrderItem(models.Model):
    order     = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    name      = models.CharField(max_length=100)
    price     = models.DecimalField(max_digits=8, decimal_places=2)
    quantity  = models.PositiveIntegerField(default=1)

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.name} x{self.quantity}"


# ── PURCHASE ITEMS (grocery list master) ─────────────────

class PurchaseItem(models.Model):
    """Master list of purchasable items (like Sugar, Milk etc)"""
    name       = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ── PURCHASE ENTRY (daily purchase log) ──────────────────

class Purchase(models.Model):
    """One purchase entry = one item bought on one day"""
    item       = models.ForeignKey(PurchaseItem, on_delete=models.CASCADE, related_name='purchases')
    shop_name  = models.CharField(max_length=100)
    quantity   = models.DecimalField(max_digits=8, decimal_places=2)
    price      = models.DecimalField(max_digits=10, decimal_places=2)
    total      = models.DecimalField(max_digits=10, decimal_places=2)
    date       = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.item.name} - {self.date}"