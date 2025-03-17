from django.urls import path, include
from .views import OfferViewset, OfferDetailsViewSet, OrderViewSet, OrderCountView, CompletedOrderCountView, ReviewViewSet, BaseInfoViewset
from rest_framework import routers


router = routers.SimpleRouter()
router.register(r'offers', OfferViewset)
router.register(r'offerdetails', OfferDetailsViewSet)  
router.register(r'orders', OrderViewSet)  
router.register(r'reviews', ReviewViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('order-count/<int:business_user_id>/', OrderCountView.as_view(), name='order-count'),
    path('completed-order-count/<int:business_user_id>/', CompletedOrderCountView.as_view(), name='completed-order-count'),
    path('base-info/', BaseInfoViewset.as_view(), name='base-info')
]
