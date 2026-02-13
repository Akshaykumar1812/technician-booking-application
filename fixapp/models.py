# fixapp/models.py
from django.db import models
from django.utils import timezone


class UserRegistration(models.Model):
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # plain password
    phone = models.CharField(max_length=15, null=True, blank=True)
    profile_image = models.ImageField(upload_to="user_profiles/", null=True, blank=True)

    # Added later by user
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    registered_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

class TechnicianRequest(models.Model):
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    experience = models.PositiveIntegerField()
    profile_image = models.ImageField(upload_to="technician_profiles/", null=True, blank=True)
    document = models.FileField(upload_to="technician_docs/")
    id_proof = models.FileField(upload_to="id_proofs/", null=True, blank=True) 
    password = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=20, default="Pending")
    applied_on = models.DateTimeField(auto_now_add=True)

    # ✅ New fields for location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.category})"
    
class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    # recipient_type can be "users", "technicians", or "both"
    recipient_type = models.CharField(
        max_length=20,
        choices=[("users","Users"),("technicians","Technicians"),("both","All")],
        default="both"
    )
    is_read = models.BooleanField(default=False)  # optional

    def __str__(self):
        return f"{self.title} ({self.recipient_type})"
    
    
class FavoriteTechnician(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='favorites')
    technician = models.ForeignKey(TechnicianRequest, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'technician')

    def __str__(self):
        return f"{self.user.username} → {self.technician.full_name}"
    

class TechnicianAvailability(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Booked', 'Booked'),
    ]

    technician = models.ForeignKey(TechnicianRequest, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.technician.username} - {self.date} ({self.start_time} to {self.end_time})"

class Booking(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    technician = models.ForeignKey(TechnicianRequest, on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('Booked','Booked'),
        ('Cancelled','Cancelled'),
        ('Accepted','Accepted'),
        ('Rejected','Rejected'),
        ('Completed','Completed')
    ], default='Booked')
    repair_details = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.technician.username} - {self.date} ({self.time_slot})"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    repair_description = models.TextField(blank=True, null=True)
    labour_charge = models.FloatField(default=0)
    item_charge = models.FloatField(default=0)
    additional_charge = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    payment_status = models.CharField(max_length=20, choices=[('Pending','Pending'),('Paid','Paid')], default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.booking}"


class Feedback(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    technician = models.ForeignKey(TechnicianRequest, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.technician.full_name} ({self.rating}/5)"