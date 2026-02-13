from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('work/', views.work, name='work'),
    path('contact/', views.contact_page, name='contact'),

    path('login/', views.login_view, name='login'),
    path("logout/", views.logout_view, name="logout"),


    path('admin_home/', views.admin_home, name='admin_home'),
    path("pending_technicians/", views.pending_technicians, name="pending_technicians"),
    path('technician/<int:pk>/', views.technician_detail, name='technician_detail'),
    path("technician/<int:pk>/approve/", views.approve_technician, name="approve_technician"),
    path("technician/<int:pk>/reject/", views.reject_technician, name="reject_technician"),
    path('verified-technicians/', views.verified_technicians, name='verified_technicians'),
    path("verified-technician/<int:pk>/", views.verified_tech_detail, name="verified_tech_detail"),
    path("verified-technician/<int:pk>/delete/", views.delete_technician, name="delete_technician"),
    path("users/", views.users_list, name="users_list"),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path("send-notification/", views.send_notification, name="send_notification"),
    path('admin_page/feedbacks/', views.admin_feedback_view, name='admin_feedbacks'),
    path('admin_page/completed-bookings/', views.admin_completed_bookings, name='admin_completed_bookings'),
    path('admin_page/transaction/<int:booking_id>/', views.admin_transaction_detail, name='admin_transaction_detail'),



    path('register_user/', views.register_user, name='register_user'),
    path('user-home/', views.user_home, name='user_home'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/services/', views.user_services, name='user_services'),
    path('user-tech-list/', views.user_tech_list, name='user_tech_list'),
    path('book-now/<int:tech_id>/', views.book_now, name='book_now'),
    path('user-favorites/', views.user_favorite_list, name='user_favorite_list'),
    path('toggle-favorite/', views.toggle_favorite_technician, name='toggle_favorite_technician'),
    path('profile/', views.user_profile, name='user_profile'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('user/payment-history/', views.user_payment_history, name='user_payment_history'),
    path('feedback/<int:tech_id>/', views.user_feedback, name='user_feedback'),
    path('view-user-feedback/', views.view_user_feedback, name='view_user_feedback'),
    path('find_nearby_technicians/', views.find_nearby_technicians, name='find_nearby_technicians'),


    path('register_technician/', views.register_technician, name='register_technician'),
    path('technician-home/', views.technician_home, name='technician_home'),
    path('technician-dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('technician/profile/', views.technician_profile, name='technician_profile'),
    path('technician_calendar/', views.my_calendar, name='technician_calendar'),
    path('calendar/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('technician_bookings/', views.technician_bookings, name='technician_bookings'),
    path("payment-details/<int:booking_id>/", views.payment_details, name="payment_details"),
    path('technician/payment-history/', views.technician_payment_history, name='technician_payment_history'),
    path("delete-payment/<int:payment_id>/", views.delete_payment, name="delete_payment"),
    path('technician/feedbacks/', views.technician_feedbacks, name='technician_feedbacks'),

]



