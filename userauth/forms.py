from django import forms 
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm
from userauth.models import CustomUser,ContactUs
from adminapp.models import Address,ProductReview
from django.contrib.auth.password_validation import validate_password

class UserRegisterForm(UserCreationForm):
    referral_code = forms.CharField(max_length=12, required=False)
    class Meta:
        model=CustomUser
        fields=['first_name','last_name','email','phone_number','password1','password2',"referral_code"]

class LoginForm(AuthenticationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder': 'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'Password'}),required=False)
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        otp_login = self.data.get('otp_login')


        if not password and not otp_login:
            raise forms.ValidationError("Password is required unless using OTP.")

        return cleaned_data
    class Meta:
        model=CustomUser
        fields=['email','password1']

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter your OTP'}))
    class Meta:
        fields=['otp']
        
class FP_Email:
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder': 'Email'}))
    class Meta:
        fields=['email']

class ForgotPassword(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': 'Enter your OTP'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control', 'placeholder': 'Confirm Password'}))
    
    

    class Meta:
        fields=['otp','password1','password2']


class UserAccount(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name','phone_number']

    def __init__(self, *args, **kwargs):
        super(UserAccount, self).__init__(*args, **kwargs)
        self.fields['email'].disabled = True

class PasswordChange(PasswordChangeForm):
    class Meta:
        model=CustomUser
        fields=['old_password','new_password1','new_password2']

class AddressForm(forms.ModelForm):
    class Meta:
        model=Address
        fields=['name','address_line1','address_line2','city','state','zip_code','is_default','phone_number']

class CheckoutForm(forms.Form):
    def __init__(self, *args, validate_coupon=True, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        
        # Set queryset for address field
        self.fields['address'].queryset = Address.objects.all()

        # Set choices for payment_method field
        self.fields['payment_method'].choices = self.payment_method_choices

        if not validate_coupon:
            # Exclude coupon-related fields from validation
            for key in ['coupon_code']:  # Add other coupon-related fields if needed
                self.fields[key].validators = []

    address = forms.ModelChoiceField(queryset=Address.objects.none(), empty_label=None, widget=forms.RadioSelect)
    payment_method_choices = [('cash_on_delivery', 'Cash on Delivery'), ('razorpay', 'Razorpay'), ('wallet', 'Wallet')]
    payment_method = forms.ChoiceField(choices=payment_method_choices, widget=forms.RadioSelect)
    coupon_code = forms.CharField(max_length=100, required=False)  #


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['review', 'rating','product_variant']

class ContactUsForm(forms.ModelForm):
    class Meta:
        model=ContactUs
        fields=['mail','subject','message']