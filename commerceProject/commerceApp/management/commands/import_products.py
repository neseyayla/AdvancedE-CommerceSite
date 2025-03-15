from django.core.management.base import BaseCommand
import requests
from commerceApp.models import Product, Category
from django.core.files.base import ContentFile
from django.utils.text import slugify
import os

class Command(BaseCommand):
    help = 'Import products from DummyJSON API and categorize them automatically'

    def handle(self, *args, **kwargs):
        # Önce mevcut ürünleri ve kategorileri temizle
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        # DummyJSON API'den ürünleri çek
        response = requests.get('https://dummyjson.com/products')
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            # Benzersiz kategorileri topla
            categories = {}
            
            # Önce kategorileri oluştur
            for product in products:
                category_name = product.get('category', '').title()
                if category_name not in categories:
                    category = Category.objects.create(
                        name=category_name,
                        slug=slugify(category_name),
                        description=f'En güzel {category_name} ürünleri'
                    )
                    categories[category_name] = category
                    self.stdout.write(
                        self.style.SUCCESS(f'Created category: {category.name}')
                    )

            # Sonra ürünleri ekle
            for product_data in products:
                category_name = product_data.get('category', '').title()
                category = categories[category_name]
                
                # Her ürün için slug oluştur
                slug = slugify(product_data['title'])
                
                # Fiyatı TL'ye çevir (örnek kur: 1 USD = 30 TL)
                price_tl = float(product_data['price']) * 30
                
                # Ürünü oluştur
                product = Product.objects.create(
                    name=product_data['title'],
                    slug=slug,
                    description=product_data['description'],
                    price=price_tl,
                    category=category,
                    is_active=True,
                    is_new=True,
                    stock=product_data.get('stock', 0)
                )

                # Ürün resmini indir ve kaydet
                try:
                    # Birden fazla resim varsa ilkini al
                    image_url = product_data['images'][0] if product_data['images'] else None
                    if image_url:
                        image_response = requests.get(image_url)
                        if image_response.status_code == 200:
                            image_name = f"{slug}.jpg"
                            product.image.save(
                                image_name,
                                ContentFile(image_response.content),
                                save=True
                            )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Image download failed for {product.name}: {str(e)}'
                        )
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created product: {product.name} in category: {category.name}'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS('Successfully imported all products')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to fetch products from API')
            ) 