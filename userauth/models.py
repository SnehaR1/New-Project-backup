from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.translation import gettext as _



# Create your models here.
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)  
    username = models.CharField(max_length=255, blank=True, null=True, unique=False)
    phone_number = models.CharField(max_length=15, unique=True, blank=False, null=False)  
    first_name = models.CharField(max_length=30, blank=False) 
    last_name=models.CharField(max_length=30,blank=False) 

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name="customuser_groups",
        related_query_name="customuser",
        verbose_name=_('groups')
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name="customuser_user_permissions",
        related_query_name="customuser",
        verbose_name=_('user permissions')
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', 'first_name','last_name','phone_number']
    
    def __str__(self):
        return self.email or ''
    
class Userprofile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_secret = models.CharField(max_length=32, blank=True, null=True) 
    otp_timestamp = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)  


class ContactUs(models.Model):
    mail=models.EmailField(blank=False,null=False)
    subject=models.CharField(max_length=255,null=False,blank=False)
    message=models.TextField(null=False,blank=False)