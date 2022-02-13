from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('B', 'Blik'),
    ('BT', 'Bank Transfer'),

)

class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
        'class':'custom-select d-block w-100'
    }))
    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100'
        }))
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    set_default_shipping = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    use_default_shipping = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    set_default_billing = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    use_default_billing = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES
    )


class PaymentForm(forms.Form):
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label' : "Recipient's username",
        'aria-describedby' : "basic-addon2",
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3
    }))
    email = forms.EmailField()