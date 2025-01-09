# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/distributor/', views.register_distributor, name='register-distributor'),
    path('register/agent/', views.register_agent, name='register-agent'),
    path('register/superadmin/', views.register_super_admin, name='register_super_admin'),
    path('distributor/agents/', views.get_agents_for_distributor, name='get_agents_for_distributor'),
]