from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .models import Item, Order, OrderItem, Address, UserProfile, Payment, Coupon, Refund
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, PaymentForm, CouponForm, RefundForm

import random
import string

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def item_list(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "home.html", context)

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

class CheckoutView(View):
    def get(self, *args, **kwargs):
        #form
        form = CheckoutForm()
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True,
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'S',
                default=True,
            )

            if shipping_address_qs.exists():
                context.update({'default_shipping_address':shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'B',
                default=True,
            )

            if billing_address_qs.exists():
                context.update({'default_billing_address':billing_address_qs[0]})

            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You dont have active order")
            return redirect("shop_app:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    print("Using default shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True,
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('shop_app:checkout')
                else:
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type = 'S',
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(self.request, "Please enter correct shipping address")

                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                if same_billing_address:
                    billing_addres = shipping_address
                    billing_addres.pk = None
                    billing_addres.save()
                    billing_addres.address_type = "B"
                    billing_addres.save()
                    order.billing_address = billing_addres
                    order.save()

                elif use_default_billing:
                    print("Using default billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True,
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, "No default billing address available")
                        return redirect('shop_app:checkout')
                else:
                    print("user is entering new billing address")
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B',
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(self.request, "Please enter correct billing address")

            payment_option = form.cleaned_data.get('payment_option')

            if payment_option == 'B':
                return redirect('shop_app:payment', payment_option='blik')
            elif payment_option == 'BT':
                return redirect('shop_app:payment', payment_option='paypal')
            else:
                messages.warning(
                    self.request, "Invalid payment option selected")
                return redirect('shop_app:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request,"You do not have order")
            return redirect('shop_app:order_summary')

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
            }
            userprofile = self.request.user.userprofile
            #if userprofile.one_click_purchasing:
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("shop_app:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                userprofile.one_click_purchasing = True
                userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                payment = Payment()
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = "home.html"

    def get_queryset(self, *args, **kwargs):
        queryset = Item.objects.all()
        category = self.request.GET.get("category")
        if category:
            queryset = Item.objects.all().filter(category=category)
        return queryset

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request,"You do not have order")
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered = False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Item quantity succesful updated in cart")
            return redirect("shop_app:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Item succesful added to cart")
            return redirect("shop_app:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item succesful added to cart")
    return redirect("shop_app:product", slug=slug)

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user = request.user,
                ordered = False,
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Item succesful remove to cart")
            return redirect("shop_app:order-summary")
        else:
            messages.info(request, "Item is not in your to cart")
            return redirect("shop_app:product", slug=slug)
    else:
        messages.info(request, "You dont have active order")
        return redirect("shop_app:product", slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user = request.user,
                ordered = False,
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "Item quantity updated")
            return redirect("shop_app:order-summary")
        else:
            messages.info(request, "Item is not in your to cart")
            return redirect("shop_app:product", slug=slug)
    else:
        messages.info(request, "You dont have active order")
        return redirect("shop_app:product", slug=slug)

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon

    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("/")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code=code)
                order.save()
                messages.success(self.request, "This coupon is succesfully added")
                return redirect("shop_app:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You dont have active order")
                return redirect("shop_app:checkout")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form' : form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')

            # edit order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, 'Your request was recived')
                return redirect('shop_app:request-refund')

            except ObjectDoesNotExist:
                messages.info(self.request, 'Error, That orderd does not exist')
                return redirect('shop_app:request-refund')