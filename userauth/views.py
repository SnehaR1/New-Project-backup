from pyotp import TOTP
import paypalrestsdk
from userauth.models import CustomUser, Userprofile
from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from userauth.forms import UserRegisterForm,LoginForm,OTPForm,ForgotPassword,UserAccount,PasswordChange,AddressForm,CheckoutForm,ProductReviewForm,ContactUsForm
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse,HttpResponse
from adminapp.models import Product,Category,ProductImages,Brand,ProductVariant,CartOrder,CartOrderItems,Address,Order,OrderItem,Coupon,Transaction,Wallet,Wishlist,Offers,Referral,Blogs,ProductReview,BlogAdditionalImage
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, fields
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm 
from django.db.models import Q
from django.db import transaction
import razorpay
from django.views.decorators.csrf import csrf_exempt
import secrets
import base64
from django.urls import reverse
from django.shortcuts import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
import random
import uuid
from django.db.models import Case, When, F, DecimalField




paypalrestsdk.configure({
    "mode": "sandbox",  
    "client_id": "AUBlmfAZUuaAzqsla8EKv764JTkJCciGvfexs1-wEgtsdrD1iSYuOdPOy-KQb3yPJLUoQqecAgRlBOjr",
    "client_secret": "EFoS8LslWs0qzPg5M_ka3ya4tmnlo8WyMrYAPMoG9gWNgZ02IhDvqYsRGX8hrn_2hif0cs9fs5GeSkni",
})

def signup_view(request):
    disc_applied=False
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
          
            new_user=request.user
            referral_code=form.cleaned_data['referral_code']
            referral=Referral.objects.get(referral_code=referral_code)
            if referral:
                # disc_applied=apply_ref_discount(referral_code,new_user)
                request.session['referral_code'] = referral_code

            else:
                form = UserRegisterForm(instance=new_user)

                context = {'form': form}
                messages.error("Referral Code is Invalid!!!")
                return render(request, "signup.html", context)
            user_data = form.cleaned_data
            request.session['user_data'] = user_data

            otp = generate_otp() 
            request.session['otp'] = otp
            if otp is None:
                messages.error(request, 'There was an error generating the OTP. Please try again.')
                return render(request, "signup.html", {'form': form})
            
            send_mail(
                'OTP Verification Code',
                f'Verify Your Mail By The OTP: \n {otp}',
                settings.EMAIL_HOST_USER,
                [user_data['email']],
                fail_silently=True,
            )

            request.session['flow'] = 'signup'
            return redirect('email_otp')
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, "signup.html", context)

def apply_ref_discount(referral_code,new_user):
    if referral_code:
        ref_info_q=Referral.objects.filter(referral_code=referral_code)
        if ref_info_q.exists():
            ref_info=ref_info_q.first()
            if ref_info.referrer:
                return False
            else:
                referrer=new_user
                ref_info.referrer=referrer
                ref_info.save()
            
            # referral,created=Referral.objects.update_or_create(referral_code=referral_code,referred_user=referred_by,discount_amount=ref_info.discount_amount,referrer=referrer)
                wallet=Wallet.objects.create(user=new_user,balance=ref_info.discount_amount)
                wallet_info=Wallet.objects.get(user=ref_info.referred_user)
                wallet_info.balance+=ref_info.discount_amount
                wallet_info.save()
                return True
        else:
            return False
        
        


def email_otp(request):
    user_data = request.session.get('user_data')
    referral_code = request.session.get('referral_code')
    if not user_data:
        messages.error(request, 'Session data is missing.')
        return redirect('signup_view')  

    user_email = user_data['email']
    otp_in_session = request.session.get('otp')
    flow = request.session.get('flow')
    disc_applied=request.session.get('disc_applied')
    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data.get('otp')
            if entered_otp == otp_in_session:  
                if flow == 'signup':
                    password = user_data.pop('password1')
                    user_data.pop('password2', None)
                    user = CustomUser.objects.create(email=user_email, password=password)
                    user.set_password(password)

            
                    user.first_name = user_data['first_name']
                    user.last_name = user_data['last_name']
                    user.phone_number = user_data['phone_number']
                    user.save()

                    user_profile, created = Userprofile.objects.get_or_create(user=user)
                    if not created:
                        user_profile.is_verified = True
                        user_profile.phone_number = user_data['phone_number']
                        user_profile.save()

                    messages.success(request, 'Account created and verified.')
                    if referral_code:
                        disc_applied=apply_ref_discount(referral_code,user)
                        if disc_applied:
                            messages.success(request,'Referral Code Applied Successfully!You have credited Rs 100 in your Wallet!')
                    login(request, user)  
                    return redirect('login_view')

                elif flow == 'login':
                    user = CustomUser.objects.get(email=user_email)
                    login(request, user)
                    messages.success(request, 'Login successful.')
                    return redirect('home')
            else:
                messages.error(request, 'Invalid or expired OTP.')
        else:
            messages.error(request, 'Invalid OTP format.')

    else:
        form = OTPForm()

    context = {'form': form}
    return render(request, 'email.html', context)


def login_view(request):
    form = LoginForm(request.POST or None)
    email = None

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if "otp_login" in request.POST:
            if not email:
                messages.error(request, "Please enter your email.")
                return render(request, 'login.html', {'form': form})

            user = CustomUser.objects.filter(email=email).first()
            if user:
                otp = generate_otp(user)
                request.session['otp'] = otp
                request.session['user_data'] = {'email': email}
                send_mail(
                    'OTP Verification Code',
                    f'Verify Your Mail By The OTP: \n {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=True,
                )
                request.session['flow'] = 'login'
                return redirect('email_otp')
            else:
                messages.error(request, 'User with the given email does not exist.')
        else:
            if password:
                user = authenticate(request, email=email, password=password)
                if user:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, "Incorrect email or password.")
            else:
                messages.error(request, "Please enter your password.")

    context = {'form': form}
    return render(request, 'login.html', context)



def generate_otp(user=None):
    if user:
        user_profile, created = Userprofile.objects.get_or_create(user=user)
    else:
        user_profile = None 


    otp_secret = user_profile.otp_secret if user_profile and user_profile.otp_secret else base64.b32encode(secrets.token_bytes(16)).decode()

    totp = TOTP(otp_secret,interval=30)
    otp = totp.now()

    if user_profile:
        user_profile.otp = otp
        user_profile.otp_timestamp = timezone.now()
        user_profile.save()

    return otp

@login_required(login_url='/login/')
def home(request):
    products=Product.objects.all()
    return render(request,"core/home.html",{"products":products})

@login_required(login_url='/login/')
def shop(request, category_title=None, brand_title=None):
    product_variants = ProductVariant.objects.filter(is_listed=True)
    products = Product.objects.filter(product_variants__in=product_variants).distinct()
    categories = Category.objects.filter(is_listed=True)
    brands = Brand.objects.filter(is_listed=True)
    active_offers = Offers.objects.filter(active=True)
    
    discounted_price=0
    for offers in active_offers:
       
        discounted_price = offers.new_price()
       
            
        

        

    if category_title:
        category = get_object_or_404(Category, title=category_title)
        products = products.filter(category=category)
    if brand_title:
        brand = get_object_or_404(Brand, title=brand_title)
        products = products.filter(brand=brand)

    query = request.GET.get('search', '')

    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(brand__title__icontains=query) |
            Q(category__title__icontains=query) 
        ) 
    
    sort_by = request.GET.get('sort_by', 'default')  
    
    if sort_by == 'price_low':
    
        products = products.annotate(
            effective_price=Case(
                When(offers__isnull=False, then=F('product_variants__price')),
                default=F('product_variants__old_price'),
                output_field=DecimalField(),
            )
        ).order_by('effective_price')
    elif sort_by == 'price_high':
       
        products = products.annotate(
            effective_price=Case(
                When(offers__isnull=False, then=F('product_variants__price')),
                default=F('product_variants__old_price'),
                output_field=DecimalField(),
            )
        ).order_by('-effective_price')
    elif sort_by == 'discount_high':
        products = products.order_by('-offers__discount_percentage')
    elif sort_by == 'discount_low':
        products = products.order_by('offers__discount_percentage')

        
    context = {
        "products": products,
        "categories": categories,
        "brands": brands,
        "product_variants": product_variants,
        "query": query,
        "active_offers":active_offers,
        "discounted_price":discounted_price,
    }

    return render(request, "core/shop.html", context)



def product_details(request, pv_id):
    try:
        product = get_object_or_404(ProductVariant, pk=pv_id)
        additional_images = product.productimages_set.all()
        categories = Category.objects.all()
        main_p = Product.objects.all()
        reviews=ProductReview.objects.filter(product_variant_id=pv_id)
        form = ProductReviewForm()
        if request.method == "POST":
            review = request.POST.get('review')
            rating = request.POST.get('rating')
            review_form = ProductReview.objects.create(
            review=review,
            rating=rating,
            product_variant=product,
            user=request.user 
        )
            return redirect('product_details', pv_id=product.id)
        else:
            form = ProductReviewForm()
        

        

        context = {
            "product": product,
            "categories": categories,
            "additional_images": additional_images,
            "form":form,
            "reviews":reviews
        
        }

        return render(request, "core/product_details.html", context)

    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)



    
    
    
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = CustomUser.objects.filter(email=email).first()

        if user:
            otp = generate_otp(user)
            send_mail(
                'OTP Verification Code',
                f'Verify Your Mail By The OTP: \n {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=True,
            )
            
     
            request.session['reset_otp'] = otp
            request.session['reset_email'] = user.email

            return redirect('new_password')
        else:
            messages.error(request, 'User with the given email does not exist.')
            return render(request, "forgot_password.html")
    
    return render(request, 'forgot_password.html')

def new_password(request):

    otp = request.session.get('reset_otp')
    email = request.session.get('reset_email')

    if not (otp and email):
        messages.error(request, "Invalid session. Please request a new OTP.")
        return redirect("forgot_password")

    user = CustomUser.objects.get(email=email)

    form = ForgotPassword(request.POST or None)
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        if otp_entered == otp and form.is_valid():
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            messages.success(request, "Password changed successfully.")
            return redirect("login_view")
        else:
            messages.error(request, "Invalid OTP or form error.")

    return render(request, "new_password.html", {'form': form})


def user_dashboard(request):
    return render(request,'core/user_dashboard.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login_view')



@login_required
def add_to_cart(request, pv_id):
    user = request.user
    product_variant = ProductVariant.objects.get(pk=pv_id)
    cart_order, created = CartOrder.objects.get_or_create(user=user)

   
    if product_variant.stock > 0:
        if product_variant:
            cart_item, item_created = CartOrderItems.objects.get_or_create(order=cart_order, price=product_variant)
       


   
        if not item_created:

            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, "Item added to cart successfully!!!")
        else:

            cart_item.quantity = 1
            cart_item.save()
            messages.success(request, "Item added to cart successfully!!!")
    else:

        messages.error(request, "This product is out of stock!!!")

    referer = request.META.get('HTTP_REFERER', None)

    if referer and 'product_details' in referer:
        return redirect('product_details', pv_id=pv_id)
    elif referer and 'wishlist' in referer:
        return redirect('wishlist')
    else:
        return redirect('shop')



@login_required
def view_cart(request):
    user = request.user
    cart_order, created = CartOrder.objects.get_or_create(user=user)
    overall_total = sum(item.calculate_total() for item in cart_order.cartorderitems_set.all())
    context = {'cart_order': cart_order, 'overall_total': overall_total}
    return render(request, 'core/cart.html', context)

@login_required
def dlt_cart(request,item_id):
    cart_item=get_object_or_404(CartOrderItems, id=item_id)
    cart_item.delete()
    return redirect('view_cart')

@login_required
def user_dashboard(request):
    user = request.user
    wallet=Wallet.objects.filter(user=user)
    form = UserAccount(instance=user)
    password_form = PasswordChangeForm(user=user)
    error_message = None

    if request.method == 'POST':
        if "profile_form" in request.POST:
            form = UserAccount(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated.')
                return redirect('user_dashboard')
        elif "password_form" in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Your Password has been reset successfully.")
                return redirect('login_view')
            elif 'new_password1'!='new_password2':
                messages.error(request, "The two passwords don't match.")
                return redirect('user_dashboard')

            else:
                messages.error(request, "Invalid password change request. Please check your old password.")
                return redirect('user_dashboard')

    return render(request, 'core/user_dashboard.html', {'form': form, "password_form": password_form, 'error_message': error_message,"wallet":wallet})


def address(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    return render(request,"core/address.html",{"addresses":addresses})

@login_required
def add_address(request):
    user = request.user

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user 
            address.save()
            messages.success(request, "Your address has been successfully added.")
            return redirect('address')
    else:
        form = AddressForm(initial={'phone_number': ''})

    return render(request, "core/add_address.html", {"form": form})


def increase_quantity(request, item_id):
    cart_item = get_object_or_404(CartOrderItems, pk=item_id)
    if cart_item.quantity < cart_item.price.stock:
        cart_item.quantity += 1
        cart_item.save()


    return redirect('view_cart')

def decrease_quantity(request, item_id):
    cart_item = get_object_or_404(CartOrderItems, pk=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()

    return redirect('view_cart')


def checkout(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    cart_order = get_object_or_404(CartOrder, user=user)
    overall_total = sum(item.calculate_total() for item in cart_order.cartorderitems_set.all())
    discounted_price = overall_total 
    wallet,created = Wallet.objects.get_or_create(user=user)
    payment_done = request.session.get('payment_done', False)
    print(f"PaymentDoneInput value: {request.POST.get('paymentDoneInput')}")

    if request.method == 'POST':
        if 'coupon_code' in request.POST:
            coupon_code_value = request.POST['coupon_code']
            print(f"Coupon Code entered: {coupon_code_value}") 
            try:
                coupon = Coupon.objects.get(hashed_code=coupon_code_value)
                if coupon.is_active() and not coupon.is_expired():
                    discount_amount = (coupon.discount_percentage / Decimal(100)) * Decimal(overall_total)
                    rounded_discount_amount = round(discount_amount, 2)
                    overall_total= overall_total - rounded_discount_amount
                    messages.success(request, f"Coupon successfully applied! Discount: ₹{discount_amount:.2f}")
                else:
                    messages.error(request, "Coupon is not active or has expired.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code. Please try again.")
            
        
            form = CheckoutForm(request.POST)
            overall_total_paisa=overall_total*100
            return render(request, "core/checkout.html", {"addresses": addresses, "overall_total": overall_total,"overall_total_paisa":overall_total_paisa,"form": form})

        else:
          
            form = CheckoutForm(request.POST)
        
        if form.is_valid():
            address = form.cleaned_data['address']
            payment_method = form.cleaned_data['payment_method']
            

            if not address:
                default_address = addresses.filter(is_default=True).first()
                form.initial['address'] = default_address
            
    
                
            if payment_method == "razorpay":
                if payment_done:
                    order = Order.objects.create(
                        user=user,
                        shipping_address=address,
                        payment_method=payment_method,
                        total_price=overall_total,
                        payment_done=True
                    )


               
                 
                    order.save() 
                    cart_order.delete()
                    return redirect('order_confirmation')
                else:
                    messages.error(request, "Payment not done")
                    return redirect("checkout")
            elif payment_method == 'wallet':
             
                if wallet.balance >= overall_total:
                 
                    wallet.balance -= overall_total
                    wallet.save()
                    order = Order.objects.create(
                    user=user,
                    shipping_address=address,
                    payment_method=payment_method,
                    total_price=overall_total,
                    payment_done=True
                    
                )

                    for item in cart_order.cartorderitems_set.all():
                        OrderItem.objects.create(
                            order=order,
                            product=item.price.product,
                            quantity=item.quantity,
                            price=item.price
                        )
            
                    cart_order.delete()
                    return redirect('order_confirmation')
                else:
                    messages.error(request,"Not enough balance!!!")
               
                    return redirect("checkout")
                 
            elif payment_method=='cash_on_delivery':
                order = Order.objects.create(
                    user=user,
                    shipping_address=address,
                    payment_method=payment_method,
                    total_price=overall_total,
                    payment_done=False
                    
                )

                for item in cart_order.cartorderitems_set.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.price.product,
                        quantity=item.quantity,
                        price=item.price
                    )
            
                cart_order.delete()
                return redirect('order_confirmation')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CheckoutForm()
    form.fields['payment_method'].initial = request.POST.get('payment_method', form.fields['payment_method'].initial)
    form.fields['address'].initial = request.POST.get('address', form.fields['address'].initial)

    form.fields['payment_method'].choices = form.payment_method_choices
    overall_total_paisa=overall_total*100
    return render(request, "core/checkout.html", {"addresses": addresses,'overall_total_paisa':overall_total_paisa, "overall_total": overall_total,"discounted_price": discounted_price, "form": form,"wallet":wallet})




def order_confirmation(request):
 
    latest_order = Order.objects.latest('created_at')
    orderitems = OrderItem.objects.filter(order=latest_order)
    for order_item in orderitems:
        product_variant = order_item.price
        product_variant.stock -= order_item.quantity
        product_variant.save()

    return render(request,'core/order_confirmation.html', { "latest_order":latest_order, "orderitems": orderitems})

def orders_view(request):
    orders = Order.objects.all()
    orderitems = OrderItem.objects.select_related('product', 'product__product_variants').all() 
    return render(request, 'core/orders.html', {"orders": orders, "orderitems": orderitems})

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "POST" and "cancel_order" in request.POST:
        order.status = "Cancelled"
        order.save()
        total_refund_amount = sum(item.price.price for item in order.orderitem_set.all())
        user_wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
        user_wallet.balance += total_refund_amount
        user_wallet.save()
        refund_transaction = Transaction.objects.create(
            user=request.user,
            amount=-total_refund_amount, 
        )
        for item in order.orderitem_set.all():
            item.status = "Cancelled"
            item.save()

            product = item.product
            product_variants = product.product_variants.all()  
            for product_variant in product_variants:
                product_variant.stock += item.quantity
                product_variant.save()

        print(f"Order status updated successfully")
        return redirect("orders")
    elif request.method == "POST" and "return_order" in request.POST:
        order.status = "Returned"
        order.save()
        total_refund_amount = sum(item.price.price for item in order.orderitem_set.all())
        user_wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
        user_wallet.balance += total_refund_amount
        user_wallet.save()
        refund_transaction = Transaction.objects.create(
            user=request.user,
            amount=-total_refund_amount, 
        )
        for item in order.orderitem_set.all():
            item.status = "Returned"
            item.save()

            product = item.product
            product_variants = product.product_variants.all()  
            for product_variant in product_variants:
                product_variant.stock += item.quantity
                product_variant.save()

        print(f"Order status updated successfully")
        return redirect("orders")
    return redirect("orders") 





def add_wishlist(request, pv_id):
    user = request.user
    product_variant = ProductVariant.objects.get(pk=pv_id)
    wishlist, created = Wishlist.objects.get_or_create(user=user, product_variant=product_variant)
    messages.success(request, "Item added to wishlist successfully!!!")
    referer = request.META.get('HTTP_REFERER', None)
    if referer and 'product_details' in referer:
        return redirect('product_details', pv_id=pv_id)
    else:
        return redirect('shop')
    
def wishlist(request):
    user = request.user
    wishlist = Wishlist.objects.filter(user=user)


    return render(request,'core/wishlist.html',{"wishlist":wishlist}) 

def del_wishlist(request,pv_id):
    wishlist=get_object_or_404(Wishlist,product_variant__id=pv_id)
    wishlist.delete()
    return redirect('wishlist')



def razorpay_done(request):
    request.session['payment_done'] = True
    messages.success(request, "Payment done successfully")
    return redirect("checkout")
    
def generateinvoice(request,order_id):
    order = get_object_or_404(Order,id=order_id)
    template=get_template('core/invoice.html')
    context={'order':order}
    html_content=template.render(context)
    if request.GET.get('preview'):
        return HttpResponse(html_content)
    elif request.GET.get('download'):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        pdf_data = pisa.CreatePDF(html_content, dest=response)
        if pdf_data.err:
            return HttpResponse('We had some errors <pre>' + html_content + '</pre>')
        return response

def generate_ref_code(request):
    user = request.user
    if request.method == "POST":
        try:
            ref = Referral.objects.get(referred_user=user)
            if ref and ref.referrer:
                referral_code = ref_code()
                referral = Referral.objects.create(referral_code=referral_code, referred_user=user, discount_amount=200)
                return render(request, "core/user_dashboard.html", {"referral_code": referral_code})

        except Referral.DoesNotExist:
            referral_code = ref_code()
            referral = Referral.objects.create(referral_code=referral_code, referred_user=user, discount_amount=200)
            return render(request, "core/user_dashboard.html", {"referral_code": referral_code})

        referral_code = ref.referral_code
    else:
        referral_code = None

    return render(request, "core/user_dashboard.html", {"referral_code": referral_code})




def ref_code():
    code=str(uuid.uuid4()).replace("-","")[:12]
    return code
    

def about_us(request):
    return render(request,"core/about_us.html")

def blog(request):
    blogs=Blogs.objects.all()
    return render(request,"core/blog.html",{"blogs":blogs})

def blog_page(request,blog_id):
    blog=get_object_or_404(Blogs,id=blog_id)
    blog_images=blog.additional_images.all()
    return render(request,"core/blog_page.html",{"blog":blog,"blog_images":blog_images})

def contact_us(request):
    if request.method=="POST":
        form=ContactUsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your message has been received! Thank you for reaching out")
            return redirect("contact_us")
        else:
            messages.error(request,"Something went wrong!!!")
            redirect("contact_us")
    else:
        form=ContactUsForm()
    return render(request,"core/contact_us.html",{"form":form})