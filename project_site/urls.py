from django.urls import path

from .views import registerView, homePageView, validateView, addView, listView, spendView

urlpatterns = [
    path('', homePageView, name='home'),
    path('register/', registerView, name='register'),
    path('register/validate', validateView, name='validate'),
    path('add/', addView, name='add'),
    path('list/', listView, name='list'),
    path('spend/', spendView, name='spend')
]
