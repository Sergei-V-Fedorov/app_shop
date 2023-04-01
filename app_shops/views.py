import logging
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import generic
from app_shops.models import Shop, Item, File, Cart, OrderedItem, Order
from django.urls import reverse_lazy, reverse
from app_shops.forms import ItemForm, UploadFile, TimeInterval
from csv import reader
from django.db import transaction, IntegrityError, connection, reset_queries
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _
from app_users.models import Profile
from django.conf import settings


logger = logging.getLogger(__name__)


class HomePageView(generic.ListView):
    model = Item
    template_name = 'app_shops/home_page_2.html'
    context_object_name = 'item_list'
    paginate_by = 10

    def get_queryset(self):
        #reset_queries()
        queryset = Item.objects.select_related('shop').only('name', 'shop__name').order_by('name')
        """print(queryset)
        print(connection.queries)
        print(len(connection.queries))"""
        return queryset


class AllShopListView(generic.ListView):
    """Show list of the shops in marketplace."""
    model = Shop
    template_name = 'app_shops/home_page.html'
    context_object_name = 'shop_list'
    paginate_by = 10


class CreateShopView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    """Create a new shop in marketplace."""
    model = Shop
    template_name = 'app_shops/create_shop.html'
    fields = ['name', 'tags', 'logo']
    success_url = reverse_lazy('shops_home')
    permission_required = 'app_shops.add_shop'

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class ShopListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    """Show shop list for its owners."""
    model = Shop
    template_name = 'app_shops/view_shoplist.html'
    context_object_name = 'shop_list'
    permission_required = 'app_shops.view_shop'

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = self.model.objects.filter(seller_id=user_id)
        return queryset


class ShopEditView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    """Edit shop's name, tag and logo."""
    model = Shop
    fields = ['name', 'tags', 'logo']
    template_name = 'app_shops/edit_shop.html'
    success_url = reverse_lazy('my_shop_list')
    permission_required = 'app_shops.change_shop'


class ShopDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    """Show shop detail."""
    model = Item
    template_name = 'app_shops/detail_shop.html'
    context_object_name = 'item_list'
    permission_required = ['app_shops.change_shop', 'app_shops.change_item']
    paginate_by = 10

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        queryset = Item.objects.filter(shop_id=pk).only('name', 'price', 'amount')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        shop = Shop.objects.get(id=pk)
        context['shop'] = shop
        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    """Add a new item to shop."""
    model = Item
    form_class = ItemForm
    template_name = 'app_shops/create_item.html'
    permission_required = ['app_shops.change_shop', 'app_shops.change_item']

    def get_success_url(self):
        return reverse('detail_shop', args=[self.kwargs.get('pk')])

    def form_valid(self, form):
        shop_id = self.kwargs.get('pk')
        shop = Shop.objects.get(id=shop_id)
        form.instance.shop = shop
        item = form.save()
        files = self.request.FILES.getlist('file')
        for file in files:
            file_model = File(item=item, file=file)
            file_model.save()
        return super().form_valid(form)


def item_detail_view(request, pk):
    """Show item detail and add it to cart."""
    item = Item.objects.get(id=pk)
    description = item.description.split('\\n')
    files = item.files.all()
    amount = None
    if request.user.has_perm('app_shops.change_item'):
        amount = item.amount

    if request.method == 'POST':
        if request.user.is_authenticated:
            item_id = request.POST.get('add')
            obj, created = Cart.objects.get_or_create(user_id=request.user.id, item_id=item_id)
        else:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
    return render(request, 'app_shops/detail_item.html',
                  {'item': item, 'description': description,
                   'files': files, 'amount': amount})


class ItemEditView(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    """Edit item."""
    model = Item
    template_name = 'app_shops/edit_item.html'
    form_class = ItemForm
    permission_required = ['app_shops.change_shop', 'app_shops.change_item']

    def get_success_url(self):
        return reverse_lazy('detail_item', args=[self.object.pk])

    def form_valid(self, form):
        item = self.object
        files = self.request.FILES.getlist('file')
        for file in files:
            file_model = File(item=item, file=file)
            file_model.save()
        return super().form_valid(form)


@login_required
@permission_required('app_shops.change_shop', 'app_shops.change_item', raise_exception=True)
def upload_item_from_file(request, pk):
    """Add new item in shop or renew existed items."""
    if request.method == 'POST':
        form = UploadFile(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file').read()
            file = file.decode('utf-8').split('\n')
            csv_reader = reader(file, quotechar='"')
            try:
                # code, name, price, description, amount
                for row in csv_reader:
                    if row:  # if not empty line
                        # check if item's code does not already exist
                        item, created = Item.objects.update_or_create(
                            code=row[0],
                            defaults={"shop_id": pk, "name": row[1],
                                      "price": row[2], "description": row[3],
                                      "amount": row[4]})
                return redirect(reverse('detail_shop', args=[pk]))
            except IntegrityError:
                transaction.rollback()
                return HttpResponse(content='Товары не обновлены из-за ошибок в файле')
            except Exception as e:
                return HttpResponse(content=f'Товары не обновлены из-за неправильного '
                                            f'формата данных в файле.\n{e}')
    else:
        form = UploadFile()
    return render(request, 'app_shops/upload_file.html',
                  {'form': form})


def items_in_shop(request,  pk):
    """Show a list of items in shops and add them to cart."""
    #item_list = Item.objects.filter(shop_id=pk).only('id', 'name', 'price')
    file_list = File.objects.select_related('item').filter(item__shop_id=pk).\
        only('file', 'item_id', 'item__name', 'item__price')

    # Select only first image for each item
    unique_files = dict()
    for file in file_list:
        item_id = file.item_id
        if unique_files.get(item_id) is None:
            unique_files[item_id] = {'item_name': file.item.name,
                                     'file': file.file,
                                     'item_price': file.item.price,
                                     'item_id': item_id
                                     }
    unique_files = list(unique_files.values())
    paginator = Paginator(unique_files, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        if request.user.is_authenticated:
            item_id = request.POST.get('add')
            obj, created = Cart.objects.get_or_create(user_id=request.user.id, item_id=item_id)
        else:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
    return render(request, 'app_shops/view_items_in_shop.html',
                  {'page_obj': page_obj})


@login_required
def view_cart(request):
    """View a list of items in cart and place them to order."""
    cart_list = Cart.objects.select_related('item').filter(user=request.user.id).only('quantity', 'item__name',
                                                                                      'item__price',
                                                                                      'item__amount')
    total_cost = sum([order.item.price * order.quantity
                      for order in cart_list])
    # list of item_id
    item_ids = [order.item_id for order in cart_list]

    if request.method == 'POST':
        # dict {item_ind: quantity}
        item_qty = dict(zip(item_ids,
                            request.POST.getlist('num')))
        action = request.POST.get('button')

        if action == 'clean':  # clear the cart
            cart_list.delete()
            total_cost = 0
        with transaction.atomic():
            if action == 'order':  # form the order
                # selected items to be placed in the order
                selected_items = request.POST.getlist('item')
                # Create a new order
                created = tz.now()
                created_string = created.strftime('%Y%m%dT%H%M%S')
                code = f'{request.user.id:08d}_{created_string}'
                order = Order.objects.create(user=request.user, code=code, created=created)
                # add selected items in the order and delete it from the cart
                ordered_items = []
                for index in selected_items:
                    ind = int(index)
                    item = Item.objects.get(id=ind)
                    cost = item.price * int(item_qty[ind])
                    ordered_item = OrderedItem(order=order, item=item, quantity=int(item_qty[ind]),
                                               user=request.user, total_cost=cost)
                    ordered_items.append(ordered_item)
                    deleted_item = Cart.objects.get(item=item, user=request.user)
                    deleted_item.delete()
                OrderedItem.objects.bulk_create(ordered_items)
                log_msg = f'Заказ #{order.id} сформирован. Пользователь:: {request.user.username}'
                logger.info(log_msg)
                return redirect(reverse('order', args=[code]))
    return render(request, 'app_shops/cart.html',
                  {'order_list': cart_list, 'total_cost': total_cost})


@login_required
def order_payment_view(request, code):
    """Show payment view."""
    order = Order.objects.get(code=code)
    queryset = OrderedItem.objects.select_related('item').filter(order_id=order.id).only('quantity', 'total_cost',
                                                                                         'item__name',
                                                                                         'item__price')
    total_cost = sum([obj.total_cost
                      for obj in queryset])

    # synchronize changes in Order, Profile and Item models
    with transaction.atomic():
        if request.method == 'POST':
            profile = Profile.objects.get(user_id=request.user.id)
            # check if enough money
            if profile.funds >= total_cost:
                # renew order time and status
                order.created = tz.now()
                order.status = 'b'
                order.save()
                # reduce the available funds by the purchase total cost
                new_funds = profile.funds - total_cost
                profile.funds = new_funds
                old_status = profile.buyer_status
                profile.purchases += queryset.count()
                profile.save()
                new_status = profile.buyer_status
                if new_status != old_status:
                    log_msg = f'Пользователь:: {request.user.username}. Статус покупателя повышен:: {new_status}'
                    logger.info(log_msg)
                # reduce the available items in shop
                items = []
                for ordered_item in queryset:
                    item = Item.objects.get(id=ordered_item.item_id)
                    item.amount -= ordered_item.quantity
                    items.append(item)
                Item.objects.bulk_update(items, ['amount'])
                log_msg = f'Заказ #{order.id} оплачен. С пользователя {request.user.username} ' \
                          f'списано {total_cost} руб.'
                logger.info(log_msg)
                return HttpResponse(_('платеж успешно проведен').capitalize())
    return render(request, 'app_shops/view_items_in_order.html',
                  {'item_list': queryset, 'total_cost': total_cost,
                   'order': order})


class ReplenishFundsView(LoginRequiredMixin, generic.UpdateView):
    """Replenishes money on the account."""
    model = Profile
    fields = ['funds']
    template_name = 'app_shops/replenish_funds.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        """Redefine method to change user funds."""
        old_funds = self.model.objects.get(id=self.object.id).funds

        log_msg = f'Пользователь:: {self.request.user.username}. ' \
                  f'Пополнение счета на {self.object.funds} руб.'
        logger.info(log_msg)
        self.object.funds += old_funds
        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, generic.ListView):
    """Show user's history of orders."""
    model = Order
    template_name = 'app_shops/order_history.html'
    context_object_name = 'item_list'
    paginate_by = 10

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        queryset = self.model.objects.filter(user_id=user_id).defer('user_id')
        return queryset


def get_promotions(request):
    """Show a list of promotions and allow to add them to cart."""
    promotions_cache_key = f'promotions:{request.user.username}'
    #item_list = Item.objects.filter(is_promotion=True).only('name', 'price')
    file_list = File.objects.select_related('item').filter(item__is_promotion=True). \
        only('file', 'item_id', 'item__name', 'item__price')

    cached_data = cache.get_or_set(promotions_cache_key, file_list, 60 * 60)

    # Select only first image for each item
    unique_files = dict()
    for file in cached_data:
        item_id = file.item_id
        if unique_files.get(item_id) is None:
            unique_files[item_id] = {'item_name': file.item.name,
                                     'file': file.file,
                                     'item_price': file.item.price,
                                     'item_id': item_id
                                     }
    unique_files = list(unique_files.values())
    paginator = Paginator(unique_files, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        if request.user.is_authenticated:
            item_id = request.POST.get('add')
            obj, created = Cart.objects.get_or_create(user_id=request.user.id, item_id=item_id)
        else:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
    return render(request, 'app_shops/view_promotions.html',
                  {'page_obj': page_obj})


def get_offers(request):
    """ show a list of special offers and allow to add them to cart """
    offers_cache_key = f'offers:{request.user.username}'
    #item_list = Item.objects.filter(is_offer=True).only('name', 'price')
    file_list = File.objects.select_related('item').filter(item__is_offer=True). \
        only('file', 'item_id', 'item__name', 'item__price')
    cached_data = cache.get_or_set(offers_cache_key, file_list, 60 * 60)

    # Select only first image for each item
    unique_files = dict()
    for file in cached_data:
        item_id = file.item_id
        if unique_files.get(item_id) is None:
            unique_files[item_id] = {'item_name': file.item.name,
                                     'file': file.file,
                                     'item_price': file.item.price,
                                     'item_id': item_id
                                     }
    unique_files = list(unique_files.values())
    paginator = Paginator(unique_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        if request.user.is_authenticated:
            item_id = request.POST.get('add')
            obj, created = Cart.objects.get_or_create(user_id=request.user.id, item_id=item_id)
        else:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
    return render(request, 'app_shops/view_offers.html',
                  {'page_obj': page_obj})


class ViewStatistics(LoginRequiredMixin, PermissionRequiredMixin, generic.View):
    """Show sale statistics for shop."""
    permission_required = ['app_shops.change_shop', 'app_shops.change_item']

    def get(self, request, pk: int):
        form = TimeInterval
        return render(request, 'app_shops/time_interval.html', {'form': form})

    def post(self, request, pk: int):
        form = TimeInterval(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('date_from')
            end_date = form.cleaned_data.get('date_to')
            queryset = OrderedItem.objects.select_related('item'). \
                select_related('order').filter(order__created__range=(start_date, end_date)).\
                filter(item__shop_id=pk).only('item__id', 'quantity', 'item__code', 'item__name', 'order__id')

            # dict for unique items
            item_dict = dict()
            for item in queryset:
                if item.item_id not in item_dict:
                    item_dict[item.item_id] = {'code': item.item.code,
                                               'quantity': item.quantity,
                                               'name': item.item.name}
                else:
                    item_dict[item.item_id]['quantity'] += item.quantity
            return render(request, 'app_shops/statistics.html', {'ordered_items': item_dict})
        return render(request, 'app_shops/time_interval.html', {'form': form})


