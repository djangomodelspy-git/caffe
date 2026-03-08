from django.urls import path
from . import views

urlpatterns = [
    # ── AUTH ──
    path('login/',                        views.caffe_login,   name='caffe_login'),
    path('logout/',                       views.caffe_logout,  name='caffe_logout'),

    # ── MAIN ──
    path('',                              views.order_screen,  name='order_screen'),
    path('bill/history/',                 views.bill_history,  name='bill_history'),
    path('bill/generate/',                views.generate_bill, name='generate_bill'),
    path('bill/<int:bill_id>/',           views.bill_view,     name='bill_view'),

    # ── MENU ──
    path('menu/',                         views.menu_manager,  name='menu_manager'),
    path('menu/add/',                     views.add_item,      name='add_item'),
    path('menu/edit/<int:item_id>/',      views.edit_item,     name='edit_item'),
    path('menu/delete/<int:item_id>/',    views.delete_item,   name='delete_item'),
    path('menu/category/add/',            views.add_category,  name='add_category'),

    # ── REPORTS ──
    path('sales/',                        views.sales_report,  name='sales_report'),
]