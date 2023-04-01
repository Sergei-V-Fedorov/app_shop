from django.urls import path
from app_shops.views import *

urlpatterns = [
    path('', HomePageView.as_view(), name='shops_home'),
    path('shops/', AllShopListView.as_view(), name='shop_list'),
    path('personal/cart/', view_cart, name='cart'),
    path('personal/<int:pk>/founds/', ReplenishFundsView.as_view(), name='replenish_funds'),
    path('personal/order/<str:code>/', order_payment_view, name='order'),
    path('personal/history/<int:pk>/', OrderListView.as_view(), name='order_history'),
    path('create/', CreateShopView.as_view(), name='create_shop'),
    path('my_shops/', ShopListView.as_view(), name='my_shop_list'),
    path('my_shops/<int:pk>/statistics/', ViewStatistics.as_view(), name='statistics'),
    path('my_shops/<int:pk>/', items_in_shop, name='items_in_shop'),
    path('edit/<int:pk>/', ShopEditView.as_view(), name='edit_shop'),
    path('detail/<int:pk>/', ShopDetailView.as_view(), name='detail_shop'),
    path('item/<int:pk>/create/', ItemCreateView.as_view(), name='create_item'),
    path('item/<int:pk>/upload/', upload_item_from_file, name='upload_item'),
    path('item/<int:pk>/edit/', ItemEditView.as_view(), name='edit_item'),
    path('item/<int:pk>/', item_detail_view, name='detail_item'),
    path('promotions/', get_promotions, name='promotions'),
    path('special-offers/', get_offers, name='offers'),
]
