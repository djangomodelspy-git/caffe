from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ('id', 'name', 'category', 'price', 'is_available')
    list_filter   = ('category', 'is_available')
    search_fields = ('name',)
    list_editable = ('price', 'is_available')


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0
    fields = ('name', 'quantity', 'price')
    readonly_fields = ('name', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ('bill_no', 'created_at', 'subtotal', 'tax', 'grand_total')
    list_filter    = ('created_at',)
    search_fields  = ('bill_no',)
    readonly_fields = ('bill_no', 'subtotal', 'tax', 'grand_total', 'created_at')
    inlines        = [OrderItemInline]
    ordering       = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ('id', 'order', 'name', 'quantity', 'price')
    search_fields = ('name', 'order__bill_no')