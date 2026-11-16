from django.urls import path

from reservaciones import views

app_name = 'reservaciones'

urlpatterns = [
    path('', views.lista_reservaciones, name='lista'),
    path('nueva/', views.nueva_reservacion, name='nueva'),
]
