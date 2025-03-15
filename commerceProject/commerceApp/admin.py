from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem
from .forms import CustomerForm

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    list_editable = ('price', 'stock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'lastname', 'telephone', 'city', 'country')
    search_fields = ('name', 'lastname', 'telephone', 'city')
    list_filter = ('city', 'country')
    form = CustomerForm

    def save_model(self, request, obj, form, change):
        user = form.save(commit=False)
        user.save()
        obj.user = user
        obj.save()