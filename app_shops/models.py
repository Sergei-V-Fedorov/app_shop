from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class Shop(models.Model):
    seller = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                               related_name="shops", verbose_name=_('продавец'))
    name = models.CharField(max_length=36, verbose_name=_('название'))
    tags = models.CharField(max_length=150, verbose_name=_('теги'))
    logo = models.ImageField(upload_to='files/', blank=True, verbose_name=_('логотип'))

    class Meta:
        verbose_name = _('магазин')
        verbose_name_plural = _('магазины')

    def __str__(self):
        return f'{self.name} shop'


class Item(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE,
                             related_name="items", verbose_name=_('магазин'))
    code = models.IntegerField(verbose_name=_('артикул'), unique=True)
    name = models.CharField(max_length=150, verbose_name=_('наименование товара'))
    description = models.TextField(verbose_name=_('описание товара'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('цена'))
    amount = models.IntegerField(verbose_name=_('количество'), default=0)
    is_promotion = models.BooleanField(default=False, verbose_name=_('акция'))
    is_offer = models.BooleanField(default=False, verbose_name=_('специальное предложение'))

    class Meta:
        verbose_name_plural = _('товары')
        verbose_name = _('товар')
        ordering = ['code']

    def __str__(self):
        return self.name


class File(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='files',
                             verbose_name=_('товар'))
    file = models.ImageField(upload_to='files/', verbose_name=_('файл'))

    class Meta:
        verbose_name = _('файл')
        verbose_name_plural = _('файлы')


class Cart(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,
                             related_name='carts', verbose_name=_('товар'))
    quantity = models.PositiveIntegerField(verbose_name=_('количество'), default=1)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             related_name='carts', verbose_name=_('покупатель'))

    class Meta:
        verbose_name_plural = _('корзина')
        verbose_name = _('корзина')
        ordering = ['id']

    def __str__(self):
        return f'{self.item}'

    @property
    def get_total_cost(self):
        """Return total cost of purchase"""
        price = Item.objects.get(id=self.item_id).price
        return price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('b', _('куплено').capitalize()), ('o', _('оформлено').capitalize())
    ]
    code = models.CharField(max_length=25, verbose_name=_('код заказа'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('дата создания'))
    status = models.CharField(max_length=1, verbose_name=_('статус заказа'),
                              choices=STATUS_CHOICES, default='o')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             related_name='histories', verbose_name=_('покупатель'))

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = _('заказы')
        verbose_name = _('заказ')
        ordering = ['-created']


class OrderedItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='ordered_items', verbose_name=_('номер заказа'))
    item = models.ForeignKey(Item, on_delete=models.CASCADE,
                             related_name='ordered_items', verbose_name=_('товар'))
    quantity = models.PositiveIntegerField(verbose_name=_('количество'), default=1)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             related_name='ordered_items', verbose_name=_('покупатель'))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('общая сумма'))

    class Meta:
        verbose_name_plural = _('заказанные товары')
        verbose_name = _('заказанный товар')

    def __str__(self):
        return str(self.item.id)
