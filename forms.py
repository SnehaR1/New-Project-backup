from django import forms 
from userauth.models import CustomUser
from adminapp.models import Product,Category,Brand,ProductVariant,ProductImages,Color,Quantity,OrderItem,Coupon,Offers,Blogs,BlogAdditionalImage
from multiupload.fields import MultiFileField
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


class UserEditForm(forms.ModelForm):
    user_id_to_block = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    is_active = forms.ChoiceField(
        choices=[(True, 'Unblock'), (False, 'Block')],
        widget=forms.RadioSelect,
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ['is_active']

class AddProduct(forms.ModelForm):
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        to_field_name='title',  
        empty_label=None,  
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        to_field_name='title',  
        empty_label=None,  
    )
    class Meta:
        model=Product
        fields=['title','category','brand','description','specifications']

class ProductVariantForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        to_field_name='title',  
        empty_label=None,  
    )
    color = forms.ModelChoiceField(
        queryset=Color.objects.all(),
        to_field_name='name',
        required=False,
    )
    new_color = forms.CharField(max_length=50, required=False)

    quantity = forms.ModelChoiceField(
        queryset=Quantity.objects.all(),
        to_field_name='name',
        required=False,
    )
    new_quantity = forms.CharField(max_length=50, required=False)
    class Meta:
        model=ProductVariant
        fields=['product','color','quantity','image','price','old_price','stock']
    

class ProductImagesForm(forms.ModelForm):
    class Meta:
        model = ProductImages
        fields = ['images']
  
       
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['status']

    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        initial_status = self.instance.status if self.instance else None
        self.fields['status'].initial = initial_status

class CouponForm(forms.ModelForm):
    class Meta:
        model=Coupon
        fields=['hashed_code','discount_percentage','valid_from','valid_to','active']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM '}),
            'valid_to': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM '}),
        }
        input_formats = {
            'valid_from': ['%Y-%m-%d %H:%M %p'],  
            'valid_to': ['%Y-%m-%d %H:%M %p'],
        }

class OffersForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'select2'}),
        to_field_name='title', 
        required=False,
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'select2'}),
        to_field_name='title',
        required=False,
    )

    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        widget=forms.Select(attrs={'class': 'select2'}),
        to_field_name='title',
        required=False,
    )
    widgets = {
            'valid_from': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM '}),
            'valid_to': forms.DateTimeInput(attrs={'placeholder': 'YYYY-MM-DD HH:MM '}),
        }
    input_formats = {
            'valid_from': ['%Y-%m-%d %H:%M %p'],  
            'valid_to': ['%Y-%m-%d %H:%M %p'],
        }

    class Meta:
        model = Offers
        fields = ['name', 'discount_percentage', 'product', 'category', 'brand','valid_from','valid_to','active']

class BlogForm(forms.ModelForm):
    class Meta:
        model=Blogs
        fields=['title','content','author','image']
    
       

class BlogImagesForm(forms.ModelForm):
    class Meta:
        model =BlogAdditionalImage
        fields = ['add_images']
    
       

  



