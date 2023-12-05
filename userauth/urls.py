from django.contrib import admin
from django.urls import path,include
from .views import home,signup_view,login_view,email_otp,shop,product_details,forgot_password,new_password,user_dashboard,logout_view,add_to_cart,view_cart,address,add_address,increase_quantity,decrease_quantity,checkout,dlt_cart,order_confirmation,orders_view,cancel_order,add_wishlist,wishlist,del_wishlist,razorpay_done,generateinvoice,generate_ref_code,about_us,blog,blog_page,contact_us
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("",signup_view,name="signup_view"),
    path("otp/",email_otp,name="email_otp"),
    path("login/",login_view,name="login_view"),
    path("forgot_password",forgot_password,name="forgot_password"),
    path("new_password",new_password,name="new_password"),
    path("home/",home,name="home"),
    path("shop/", shop, name="shop"),
    path("shop/category/<str:category_title>/", shop, name="shop_category"),
    path("shop/brand/<str:brand_title>/", shop, name="shop_brand"),
    path("user_dashboard/",user_dashboard,name="user_dashboard"),
    path("logout/",logout_view,name="logout_view"),
    path("product_details/<int:pv_id>/",product_details,name="product_details"),
    path('add_to_cart/<int:pv_id>/', add_to_cart, name='add_to_cart'),
    path('view_cart/', view_cart, name='view_cart'),
    path('wishlist/', wishlist, name='wishlist'),
    path('add_wishlist/<int:pv_id>/', add_wishlist, name='add_wishlist'),
    path('del_wishlist/<int:pv_id>/', del_wishlist, name='del_wishlist'),
    path('user_dashboard/', user_dashboard, name='user_dashboard'),
    path('address/', address, name='address'),
    path('orders/', orders_view, name='orders'),
    path('cancel_order/<str:order_id>/', cancel_order, name='cancel_order'),
    # path('return_order/<str:order_id>/', return_order, name='return_order'),
    path('add_address/', add_address, name='add_address'),
    path('increase_quantity/<int:item_id>/', increase_quantity, name='increase_quantity'),
    path('decrease_quantity/<int:item_id>/', decrease_quantity, name='decrease_quantity'),
    path('checkout/',checkout, name='checkout'),
    path('order_confirmation/', order_confirmation, name='order_confirmation'),
    path('dlt_cart/<int:item_id>',dlt_cart, name='dlt_cart'),
    path('razorpay_done/',razorpay_done, name='razorpay_done'),
    path('generateinvoice/<int:order_id>',generateinvoice, name='generateinvoice'),
    path('generate_ref_code/',generate_ref_code, name='generate_ref_code'),
    # path('review/<int:pv_id>/',review, name='review'),
    path('about_us/',about_us, name='about_us'),
    path('blog/',blog, name='blog'),
    path('blog_page/<int:blog_id>',blog_page, name='blog_page'),
    # path('paypal/execute/', paypal_execute, name='paypal_execute'),
    path('contact_us/',contact_us, name='contact_us'),
    path('social-auth/',include('social_django.urls', namespace='social')),

    

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)