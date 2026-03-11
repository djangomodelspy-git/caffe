from django.core.management.base import BaseCommand
from caffe.models import Category, MenuItem


MENU_DATA = {
    "Hot Drinks": [
        ("Tea", 15),
        ("Ginger Tea", 20),
        ("Masala Tea", 25),
        ("Coffee", 20),
        ("Filter Coffee", 30),
        ("Cappuccino", 60),
        ("Latte", 65),
        ("Hot Chocolate", 70),
    ],
    "Cold Drinks": [
        ("Cold Coffee", 60),
        ("Iced Latte", 70),
        ("Iced Tea", 50),
        ("Chocolate Milkshake", 80),
        ("Vanilla Milkshake", 75),
        ("Strawberry Milkshake", 80),
        ("Mango Milkshake", 75),
    ],
    "Tea": [
        ("Lemon Tea", 25),
        ("Green Tea", 30),
        ("Black Tea", 20),
        ("Cardamom Tea", 25),
        ("Honey Lemon Tea", 35),
    ],
    "Juices": [
        ("Orange Juice", 50),
        ("Apple Juice", 55),
        ("Pineapple Juice", 50),
        ("Watermelon Juice", 40),
        ("Mango Juice", 55),
        ("Mixed Fruit Juice", 60),
    ],
    "Snacks": [
        ("Veg Sandwich", 50),
        ("Cheese Sandwich", 60),
        ("Grilled Sandwich", 65),
        ("Veg Puff", 20),
        ("Samosa", 15),
        ("French Fries", 60),
        ("Garlic Bread", 55),
    ],
    "Bakery": [
        ("Chocolate Cake", 60),
        ("Black Forest Cake", 70),
        ("Cup Cake", 40),
        ("Brownie", 50),
        ("Donut", 35),
        ("Muffin", 40),
    ],
    "Meals": [
        ("Veg Burger", 70),
        ("Chicken Burger", 90),
        ("Veg Wrap", 65),
        ("Chicken Wrap", 85),
        ("Veg Noodles", 70),
        ("Fried Rice", 80),
    ],
    "Desserts": [
        ("Ice Cream (Vanilla)", 40),
        ("Ice Cream (Chocolate)", 40),
        ("Ice Cream (Strawberry)", 40),
        ("Sundae", 70),
        ("Fruit Salad with Ice Cream", 80),
    ],
}


class Command(BaseCommand):
    help = 'Seeds cafe categories and menu items with realistic prices'

    def handle(self, *args, **options):
        self.stdout.write('\n☕  Seeding cafe menu...\n')

        total_cats  = 0
        total_items = 0

        for cat_name, items in MENU_DATA.items():
            cat, cat_created = Category.objects.get_or_create(name=cat_name)
            if cat_created:
                total_cats += 1
                self.stdout.write(self.style.SUCCESS(f'  + Category: {cat_name}'))
            else:
                self.stdout.write(f'  - Category exists: {cat_name}')

            for item_name, price in items:
                item, item_created = MenuItem.objects.get_or_create(
                    name=item_name,
                    defaults={
                        'price': price,
                        'category': cat,
                        'is_available': True,
                    }
                )
                if item_created:
                    total_items += 1
                    self.stdout.write(f'       + {item_name:<35} Rs.{price}')
                else:
                    self.stdout.write(f'       . {item_name} already exists, skipped')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! {total_cats} categories and {total_items} items added.'
        ))
        self.stdout.write('   Owner can edit prices anytime from /menu/\n')

        # ── Create superuser ──
        from django.contrib.auth.models import User
        if not User.objects.filter(username='Sai').exists():
            User.objects.create_superuser('Sai', '', 'cafe@2026')
            self.stdout.write(self.style.SUCCESS('✅ Superuser created → username: admin  password: Sai'))
        else:
            self.stdout.write('   Superuser already exists, skipped.')

from django.core.management.base import BaseCommand
from caffe.models import Category, MenuItem, PurchaseItem


MENU = {
    'Coffee': [
        ('Espresso', 60), ('Americano', 80), ('Cappuccino', 90),
        ('Latte', 100), ('Mocha', 110), ('Cold Coffee', 120),
        ('Filter Coffee', 50), ('Instant Coffee', 40),
    ],
    'Tea': [
        ('Masala Chai', 30), ('Ginger Tea', 35), ('Green Tea', 60),
        ('Lemon Tea', 50), ('Iced Tea', 70), ('Tulsi Tea', 45),
    ],
    'Snacks': [
        ('Samosa', 20), ('Bread Butter', 30), ('Veg Sandwich', 60),
        ('Cheese Sandwich', 80), ('Egg Sandwich', 70), ('Puff', 25),
        ('Biscuits', 20), ('Banana Bread', 50),
    ],
    'Breakfast': [
        ('Idli (2 pcs)', 40), ('Vada (2 pcs)', 40), ('Dosa', 60),
        ('Upma', 50), ('Poha', 45), ('Paratha', 55), ('Omelette', 60),
    ],
    'Juices': [
        ('Orange Juice', 80), ('Watermelon Juice', 60), ('Mango Juice', 90),
        ('Mixed Fruit Juice', 100), ('Sugarcane Juice', 40),
    ],
    'Shakes': [
        ('Mango Shake', 110), ('Strawberry Shake', 120), ('Chocolate Shake', 130),
        ('Vanilla Shake', 110), ('Banana Shake', 100),
    ],
    'Meals': [
        ('Veg Thali', 120), ('Egg Thali', 150), ('Chicken Thali', 180),
        ('Rice + Dal', 80), ('Curd Rice', 70),
    ],
    'Beverages': [
        ('Water Bottle', 20), ('Soda', 30), ('Lassi', 60),
        ('Buttermilk', 30), ('Badam Milk', 80),
    ],
}

PURCHASE_ITEMS = [
    ('Sugar',          1),
    ('Coffee Powder',  2),
    ('Milk',           3),
    ('Tea Powder',     4),
    ('Oil',            5),
]


class Command(BaseCommand):
    help = 'Seed menu items and purchase list for Narasimha Cafe'

    def handle(self, *args, **kwargs):
        # ── Menu ──
        for cat_name, items in MENU.items():
            cat, _ = Category.objects.get_or_create(name=cat_name)
            for item_name, price in items:
                MenuItem.objects.get_or_create(
                    name=item_name,
                    defaults={'price': price, 'category': cat, 'is_available': True},
                )
        self.stdout.write(self.style.SUCCESS('✅ Menu seeded'))

        # ── Purchase Items ──
        for name, order in PURCHASE_ITEMS:
            PurchaseItem.objects.get_or_create(
                name=name,
                defaults={'sort_order': order},
            )
        self.stdout.write(self.style.SUCCESS('✅ Purchase items seeded'))

        # ── Superuser ──
        from django.contrib.auth.models import User
        if not User.objects.filter(username='Sai').exists():
            User.objects.create_superuser('Sai', '', 'cafe@2026')
            self.stdout.write(self.style.SUCCESS('✅ Superuser created'))
        else:
            self.stdout.write('ℹ️  Superuser already exists')           