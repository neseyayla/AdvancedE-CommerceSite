from django.contrib import admin
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from commerceApp.models import Customer

# Kullanıcıyı değiştirecek formu oluşturuyoruz.
class UserForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre Tekrar'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# Profil düzenleme için özel form
class UserEditForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None  # Remove default help text

# Customer modelini düzenlemek için formu oluşturuyoruz.
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ('name', 'lastname', 'telephone', 'address', 'city', 'country', 'postal_code')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad'}),
            'lastname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyad'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Adres', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Şehir'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ülke'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Posta Kodu'}),
        }
