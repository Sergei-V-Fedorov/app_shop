from django.contrib import admin
from app_shops.models import Shop, Item, File, Order, Cart, OrderedItem
from django.utils.translation import gettext_lazy as _


class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'tags', 'logo']
    list_display_links = ['name']

    class Meta:
        verbose_name = _('магазин')
        verbose_name_plural = _('магазины')


class ItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'price', 'amount']

    class Meta:
        verbose_name = _('товар')
        verbose_name_plural = _('товары')


class FileAdmin(admin.ModelAdmin):
    list_display = ['item', 'file']

    class Meta:
        verbose_name = _('файл')
        verbose_name_plural = _('файлы')


class OrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'created', 'status', 'user']
    list_editable = ['status']

    class Meta:
        verbose_name = _('заказ')
        verbose_name_plural = _('заказы')


class CartAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity', 'user']

    class Meta:
        verbose_name = _('корзина')
        verbose_name_plural = _('корзина')


class OrderedItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'quantity', 'user', 'total_cost']

    class Meta:
        verbose_name_plural = _('заказанные товары')
        verbose_name = _('заказанный товар')


admin.site.register(Shop, ShopAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(OrderedItem, OrderedItemAdmin)
