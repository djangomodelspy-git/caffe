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