from django.contrib import admin
from .models import (
    TechnicianRequest, UserRegistration, Notification, 
    FavoriteTechnician, TechnicianAvailability, Booking,
    Payment, Feedback
)

admin.site.register(TechnicianRequest)
admin.site.register(UserRegistration)
admin.site.register(Notification)
admin.site.register(FavoriteTechnician)
admin.site.register(TechnicianAvailability)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Feedback)
