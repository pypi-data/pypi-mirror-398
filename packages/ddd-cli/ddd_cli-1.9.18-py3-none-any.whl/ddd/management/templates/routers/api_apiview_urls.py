from django.urls import path

from . import [[ entity_name.lower() ]]_views

urlpatterns = [

    path('api/[[ entity_name.lower() ]]/', [[ entity_name.lower() ]]_views.[[ entity_name|capitalize_first ]]APIView.as_view(), name="[[ entity_name.lower() ]]_apiview_views"),

]
