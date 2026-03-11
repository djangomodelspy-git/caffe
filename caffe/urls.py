from django.urls import path
from . import views

urlpatterns = [
    # ── AUTH ──
    path('login/',                        views.caffe_login,         name='caffe_login'),
    path('logout/',                       views.caffe_logout,        name='caffe_logout'),

    # ── MAIN ──
    path('',                              views.order_screen,        name='order_screen'),
    path('bill/generate/',                views.generate_bill,       name='generate_bill'),
    path('bill/history/',                 views.bill_history,        name='bill_history'),
    path('bill/<int:bill_id>/',           views.bill_view,           name='bill_view'),
    path('bill/<int:bill_id>/payment/',   views.set_payment,         name='set_payment'),

    # ── MENU ──
    path('menu/',                         views.menu_manager,        name='menu_manager'),
    path('menu/add/',                     views.add_item,            name='add_item'),
    path('menu/edit/<int:item_id>/',      views.edit_item,           name='edit_item'),
    path('menu/delete/<int:item_id>/',    views.delete_item,         name='delete_item'),
    path('menu/category/add/',            views.add_category,        name='add_category'),

    # ── PURCHASES ──
    path('purchases/',                               views.purchase_list,        name='purchase_list'),
    path('purchases/save/',                          views.save_purchases,       name='save_purchases'),
    path('purchases/item/add/',                      views.add_purchase_item,    name='add_purchase_item'),
    path('purchases/item/delete/<int:item_id>/',     views.delete_purchase_item, name='delete_purchase_item'),
    path('purchases/delete/<int:purchase_id>/',      views.delete_purchase,      name='delete_purchase'),

    # ── REPORTS ──
    path('sales/',                        views.sales_report,        name='sales_report'),

    # ── PROFILE / DASHBOARD ──
    path('profile/',                      views.profile_dashboard,   name='profile_dashboard'),
]