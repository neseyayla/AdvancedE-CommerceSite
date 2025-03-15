from django.core.management.base import BaseCommand
import requests
from commerceApp.models import Product, Category
from django.core.files.base import ContentFile
from django.utils.text import slugify
import os
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import jewelry products from Etsy API'

    def add_arguments(self, parser):
        parser.add_argument('--api_key', type=str, required=True, help='Etsy API Key')

    def handle(self, *args, **kwargs):
        api_key = kwargs['api_key']
        
        # Takı kategorisini oluştur
        jewelry_category, created = Category.objects.get_or_create(
            name='Takı',
            defaults={
                'slug': 'taki',
                'description': 'Şık ve modern takı koleksiyonu'
            }
        )

        # Etsy API endpoint
        url = "https://openapi.etsy.com/v3/application/listings/active"
        
        # API parametreleri
        params = {
            "taxonomy_id": "1179", # Takı kategorisi ID'si
            "limit": 100,
            "includes": "Images,Shop",
        }
        
        # API headers
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  # Hata kontrolü
            
            products_data = response.json()
            
            for item in products_data.get('results', []):
                # Ürün adından slug oluştur
                slug = slugify(item['title'][:50])  # İlk 50 karakter
                
                # Fiyatı TL'ye çevir (yaklaşık bir kur kullanıyoruz)
                price_usd = Decimal(str(item.get('price', {}).get('amount', 0)))
                price_try = price_usd * Decimal('30.0')  # Örnek kur
                
                # Ürün verilerini hazırla
                product_data = {
                    'name': item['title'][:100],  # İlk 100 karakter
                    'description': item.get('description', '')[:500],  # İlk 500 karakter
                    'price': price_try,
                    'category': jewelry_category,
                    'is_active': True,
                    'stock': item.get('quantity', 1)
                }

                # Ürünü oluştur veya güncelle
                product, created = Product.objects.get_or_create(
                    slug=slug,
                    defaults=product_data
                )

                # Eğer ürün yeni oluşturulduysa ve resmi varsa
                if created and item.get('images') and len(item['images']) > 0:
                    try:
                        image_url = item['images'][0]['url_fullxfull']
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

                status = 'Created' if created else 'Already exists'
                self.stdout.write(
                    self.style.SUCCESS(f'{status}: {product.name}')
                )

            self.stdout.write(
                self.style.SUCCESS('Successfully imported Etsy products')
            )
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'API request failed: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred: {str(e)}')
            ) 