from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('tabla/<str:item>/', views.tabla, name='tabla'),
    path("telecomando/", views.telecomando, name="telecomando"),
    path("update/", views.update, name="update"),
    path("update/modificar_tabla/", views.modificar_tabla, name="modificar_tabla"),
    path("delete/", views.delete, name="delete"),
    path("delete/borrar_datos/", views.borrar_datos, name="borrar_datos"),
    path('change_language/', views.change_language, name='change_language'),
    path("create_models/", views.create_models, name="create_models"),
    path("send_data/", views.send_data, name="send_data"),
    path("download_tables/", views.download_tables, name="download_tables"),
]