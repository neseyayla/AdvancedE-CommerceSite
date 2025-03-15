from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.db.models import Min, Max
from . import models
from .forms import UserForm, CustomerForm, UserEditForm
from django.contrib.auth.decorators import login_required
from .models import Customer, Product, Category, Cart, CartItem
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.views.generic import ListView, DetailView
from django.contrib import messages

# Create your views here.
def index(request):
    featured_products = Product.objects.filter(is_active=True)[:4]
    categories = Category.objects.all()[:6]  # İlk 6 kategoriyi al
    return render(request, 'commerceApp/index.html', {
        'featured_products': featured_products,
        'categories': categories
    })

def register(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        customer_form = CustomerForm({
            'name': request.POST.get('name', ''),
            'lastname': request.POST.get('lastname', ''),
            'telephone': request.POST.get('telephone', ''),
            'address': request.POST.get('address', ''),
            'city': request.POST.get('city', ''),
            'country': request.POST.get('country', ''),
            'postal_code': request.POST.get('postal_code', '')
        })

        if user_form.is_valid() and customer_form.is_valid():
            try:
                # Önce user'ı kaydet
                user = user_form.save()
                
                # Sonra customer'ı kaydet
                customer = customer_form.save(commit=False)
                customer.user = user
                customer.save()

                # Newsletter aboneliği
                if request.POST.get('newsletter'):
                    # Newsletter işlemleri burada yapılabilir
                    pass

                messages.success(request, 'Kayıt işlemi başarılı! Lütfen giriş yapın.')
                return redirect('commerceApp:login')
            except Exception as e:
                # Hata durumunda user'ı sil
                if user:
                    user.delete()
                messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in customer_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    else:
        user_form = UserForm()
        customer_form = CustomerForm()

    return render(request, 'registration/register.html', {
        'user_form': user_form,
        'customer_form': customer_form,
        'hide_footer': True
    })

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            messages.success(request, 'Giriş başarılı!')
            return redirect("commerceApp:index")
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre!')
    
    return render(request, 'registration/login.html')

def user_logout(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'Sayın {username}, oturumunuz güvenli bir şekilde sonlandırıldı. İyi günler dileriz.')
    return redirect("commerceApp:login")

@login_required
def profile(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        customer = None
    return render(request, 'commerceApp/profile.html', {'customer': customer})

@login_required   
def product(request):
    return render(request,'product.html')

class ProductListView(ListView):
    model = Product
    template_name = 'commerceApp/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Kategori filtresi
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Fiyat aralığı filtresi
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
        
        # Sıralama
        sort_by = self.request.GET.get('sort', 'default')
        
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')  # Varsayılan sıralama
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = None
        
        # Mevcut filtreleri context'e ekle
        context['current_sort'] = self.request.GET.get('sort', 'default')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        
        # Fiyat aralığı için min ve max değerleri
        if Product.objects.exists():
            context['price_range'] = {
                'min': int(Product.objects.aggregate(Min('price'))['price__min']),
                'max': int(Product.objects.aggregate(Max('price'))['price__max'])
            }
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'commerceApp/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class CategoryListView(ListView):
    model = Category
    template_name = 'commerceApp/category_list.html'
    context_object_name = 'categories'

@login_required
def edit_profile(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        customer = Customer(user=request.user)

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=request.user)
        customer_form = CustomerForm(request.POST, instance=customer)

        if user_form.is_valid() and customer_form.is_valid():
            user = user_form.save()
            customer = customer_form.save(commit=False)
            customer.user = user
            customer.save()

            messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
            return redirect('commerceApp:profile')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in customer_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserEditForm(instance=request.user)
        customer_form = CustomerForm(instance=customer)

    return render(request, 'commerceApp/edit_profile.html', {
        'user_form': user_form,
        'customer_form': customer_form
    })

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'commerceApp/cart.html', {
        'cart': cart
    })

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        # Eğer ürün zaten sepette varsa miktarını güncelle
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'{product.name} sepetinize eklendi.')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'{product.name} sepetinize eklendi.',
                'cart_total': cart.get_total_items()
            })
            
        return redirect('commerceApp:view_cart')
    
    return redirect('commerceApp:product_list')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'{product_name} sepetinizden çıkarıldı.')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'{product_name} sepetinizden çıkarıldı.'
        })
        
    return redirect('commerceApp:view_cart')

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Sepetiniz güncellendi.')
        else:
            cart_item.delete()
            messages.success(request, f'{cart_item.product.name} sepetinizden çıkarıldı.')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Sepetiniz güncellendi.',
                'item_total': cart_item.get_cost(),
                'cart_total': cart_item.cart.get_total_price()
            })
            
    return redirect('commerceApp:view_cart')