from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import [[ entity_name.lower() ]]_views

router_[[ entity_name.lower() ]] = DefaultRouter()

#definir rutas
router_[[ entity_name.lower() ]].register(prefix='[[ entity_name.lower() ]]s', basename='[[ entity_name.lower() ]]s', viewset= [[ entity_name.lower() ]]_views.[[ entity_name|capitalize_first ]]ViewSet)

urlpatterns = [

    path('api/[[ entity_name.lower() ]]/', include(router_[[ entity_name.lower() ]].urls)),
    
]
