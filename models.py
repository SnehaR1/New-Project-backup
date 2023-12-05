from django.db import models
from shortuuid.django_fields import ShortUUIDField
from userauth.models import CustomUser
from django.utils.html import mark_safe
from django.utils.crypto import get_random_string
from django.db.models import Count 
from django.utils import timezone
import hashlib
from decimal import Decimal
from userauth.utils import generate_ref_code
import logging

# Create your models here.
STATUS_CHOICE=[
    ("processing","Processing"),
    ("shipped","Shipped"),
    ("delivered","Delivered"),
    ('cancelled', 'Cancelled'),
]

STATUS=[
    ("draft","Processing"),
    ("disabled","Disabled"),
    ("rejected","Rejected"),
    ("in review","In Review"),
     ("published","Published"),
]

RATING=[
    (0,"☆☆☆☆☆"),
    (1,"★☆☆☆☆"),
    (2,"★★☆☆☆"),
    (3,"★★★☆☆"),
    (4,"★★★★☆"),
    (5,"★★★★★"),
]

def user_directory_path(instance, filename):
    if instance.user:
        return 'user_{0}/{1}'.format(instance.user.id, filename)
    else:
        # Handle the case when user is None or not set
        return 'user_unknown/{0}'.format(filename)

class Category(models.Model):
    cid=ShortUUIDField(unique=True,length=10,max_length=20,prefix="cat",alphabet="abcdefgh12345")
    title=models.CharField(max_length=100)
    is_listed = models.BooleanField(default=True)
    class Meta:
        verbose_name_plural="Categories"
    def product_count(self):
        return self.product_set.count() 
    def __str__(self):
        return self.title
    
class Brand(models.Model):
    bid=ShortUUIDField(unique=True,length=10,max_length=20,prefix="br",alphabet="abcdefgh12345")
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True)
    title=models.CharField(max_length=100)
    is_listed = models.BooleanField(default=True)
    class Meta:
        verbose_name_plural="Brands"
    def product_count(self):
        return self.product_set.count() 
    def __str__(self):
        return self.title
        

class Product(models.Model):
    
    pid=ShortUUIDField(unique=True,length=10,max_length=20,prefix="pr",alphabet="abcdefgh12345")
    is_listed = models.BooleanField(default=True)
    user=models.ForeignKey(CustomUser,on_delete=models.SET_NULL,null=True)
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,related_name='product_set')
    brand=models.ForeignKey(Brand,on_delete=models.SET_NULL,null=True,related_name='product_set')
    title=models.CharField(max_length=100)
    description=models.TextField(null=True,blank=True)
    specifications=models.TextField(null=True,blank=True)
    status=models.BooleanField(default=True)
    date=models.DateField(auto_now_add=True)
    class Meta:
        verbose_name_plural="Products"
    
   

    def __str__(self):
        return self.title
    
class Color(models.Model):
    name=models.CharField(max_length=50)
    class Meta:
        verbose_name_plural="Colors"
    def __str__(self):
        return self.name

class Quantity(models.Model):
   
    name=models.CharField(max_length=50)
    class Meta:
        verbose_name_plural="Quantities"
    def __str__(self):
        return self.name
    
class ProductVariant(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.SET_NULL,null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_variants')
    image=models.ImageField(upload_to=user_directory_path ,default="images\backgrounds\Face.jpeg")
    color=models.ForeignKey(Color,on_delete=models.CASCADE,default=1)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE, default=1)
    price=models.DecimalField(max_digits=10,decimal_places=2,default="50.00",null=True,blank=True)
    old_price=models.DecimalField(max_digits=10,decimal_places=2,default="50.00")
    stock = models.PositiveIntegerField(default=0)
    is_listed = models.BooleanField(default=True)
    objects=models.Manager()
    
    def product_images(self):
        return mark_safe('<img src="%s" width="50" height="50"/>' % (self.image.url))
    class Meta:
        verbose_name_plural="Product Variants"

    def get_percentage(self):
        discount = (1 - (self.price / self.old_price)) * 100
        return round(discount, 2)

    def __str__(self):
        return self.product.title


class ProductImages(models.Model):
    images = models.ImageField(upload_to="product-images", default="product.jpg")
    productvariant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Images"


class CartOrder(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)

    class Meta:
        verbose_name_plural = "Cart Orders"
    

class CartOrderItems(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total(self):
        if self.quantity is not None:
            if self.price.price is not None:
                return self.quantity * self.price.price
            elif  self.price.old_price is not None:
                return self.quantity * self.price.old_price
        return 0 

    class Meta:
        unique_together = ['order', 'price'] 



class ProductReview(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True,related_name="reviews")
    review=models.TextField()
    rating=models.IntegerField(choices=RATING,default=None)
    date=models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural="Product Review"
    
    def __str__(self):
        return self.product.title
    
    def get_rating(self):
        return self.rating
    
class Wishlist(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True)
    product_variant=models.ForeignKey(ProductVariant,on_delete=models.SET_NULL,null=True)
    date=models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural="Wishlists"
    
    def __str__(self):
        return self.product.title

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,default="")
    address_line1 = models.CharField(max_length=100, verbose_name='Address Line 1',default="")
    address_line2 = models.CharField(max_length=100, verbose_name='Address Line 2', blank=True, null=True)
    city = models.CharField(max_length=50, verbose_name='City',default="")
    state = models.CharField(max_length=50, verbose_name='State',default="")
    zip_code = models.CharField(max_length=10, verbose_name='ZIP Code',default="")
    is_default = models.BooleanField(default=False, verbose_name='Default Address')
    phone_number = models.CharField(max_length=15, unique=False, blank=False, null=False,default="6238648528")  
  

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default']  

    def __str__(self):
        return self.address_line1
    
    def to_dict(self):
        return {
            'id': self.id,
            'state': self.state,
            'city': self.city,
            'zip_code': self.zip_code,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'phone_number': self.phone_number,
            'name': self.name,
            'is_default':self.is_default
        }
  
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_done=models.BooleanField(null=True,blank=True)
  


class OrderItem(models.Model):
    oid=ShortUUIDField(unique=True,length=10,max_length=20,prefix="or",alphabet="abcdefgh12345")
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  
    quantity = models.PositiveIntegerField()
    price = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICE, default="processing")
    delivery_date=models.DateTimeField(null=True,blank=True)
    def is_returnable(self):
        if self.status=="delivered":
        
            time_difference = timezone.now() - self.delivery_date  
            if 0 <= time_difference.days <= 7:
                    return True
            else:
                return False
  


class Coupon(models.Model):
    code= ShortUUIDField(unique=True,length=10,max_length=20,prefix="co",alphabet="abcdefgh12345")
    hashed_code = models.CharField(max_length=64)  
    discount_percentage = models.PositiveIntegerField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

   
    def is_active(self):
        return self.valid_from <= timezone.now() <= self.valid_to
        
    def is_expired(self):
        return timezone.now() > self.valid_to

    def validate_coupon_code(self, entered_code):
        entered_code_hashed = self._hash_coupon_code(entered_code)
        return entered_code_hashed == self.hashed_code and not self.is_expired()

class Wallet(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    balance=models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Transaction(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

class Referral(models.Model):
    referral_code=models.CharField(max_length=12,unique=True)
    referrer=models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name='referred_to',null=True,blank=True)
    referred_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referred_by')
    discount_amount = models.PositiveIntegerField()
    # variants=models.ForeignKey(ProductVariant,on_delete=models.CASCADE,related_name='ref_variants')
    updated=models.DateTimeField(auto_now=True)
    created=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.referral_code} |{self.referrer}"
    


class Offers(models.Model):
    name = models.CharField(max_length=255)
    discount_percentage = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    Brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)
   
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    def offer_active(self):
        return self.valid_from <= timezone.now() <= self.valid_to
    
    def apply_discount(self, product_variant):
        discount_percentage = Decimal(self.discount_percentage)
        discounted_price = product_variant.old_price - ((discount_percentage / 100) * product_variant.old_price)
        product_variant.price = discounted_price
        product_variant.save()
        return discounted_price

    def new_price(self):
        if not self.offer_active() or not self.active:
            return None
        
        if self.product:
            product_variants= self.product.product_variants.all()
        elif self.Brand:
            product_variants = self.Brand.product_set.first().product_variants.all()
        elif self.category:
            product_variants = self.category.product_set.first().product_variants.all()
        else:
            return None

        if product_variants:
            for product_variant in product_variants:
                return self.apply_discount(product_variant)
        return None
    
class Blogs(models.Model):
    title=models.CharField(max_length=100,unique=True)
    content=models.TextField(null=True,blank=True)
    author=models.CharField(max_length=100)
    image=models.ImageField(upload_to="product-images" ,blank=True,null=True)
    date=models.DateField(auto_now=True)

class BlogAdditionalImage(models.Model):
    blog = models.ForeignKey(Blogs, on_delete=models.CASCADE, related_name='additional_images')
    add_images = models.ImageField(upload_to="product-images",  blank=True,null=True)

