from django.http import JsonResponse
from django.shortcuts import render , redirect , get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import FileSystemStorage
from django.core.mail import  send_mail
from django.conf import settings
from .models import TechnicianRequest, UserRegistration, Notification, FavoriteTechnician, TechnicianAvailability, Booking,Payment, Feedback
from datetime import date, datetime, timedelta
from django.urls import reverse
from django.utils import timezone



def home(request):
    return render(request, 'home.html')  

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def work(request):
    return render(request, 'work.html')

def contact_page(request):
    return render(request, 'contact.html')

def login_view(request):
    context = {}

    # 🔹 Pull errors from session if they exist, then remove them
    if "username_error" in request.session:
        context["username_error"] = request.session.pop("username_error")
    if "password_error" in request.session:
        context["password_error"] = request.session.pop("password_error")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # -------------------- 1️⃣ Check if admin or staff (Django User) --------------------
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")

            # Redirect based on role
            if user.is_superuser:
                return redirect("admin_home")   # Admin dashboard
            elif hasattr(user, "profile") and user.profile.role == "technician":
                return redirect("technician_home")   # Technician dashboard
            else:
                return redirect("user_dashboard")   # Other Django users
            
        
        # -------------------- 2️⃣ Check TechnicianRequest --------------------
        try:
            technician = TechnicianRequest.objects.get(username=username, password=password)
    
            # Save session info for all technicians
            request.session['technician_id'] = technician.id
            request.session['technician_username'] = technician.username

            if technician.status == "Approved":
                messages.success(request, "Technician login successful!")
            else:
                messages.info(request, "Your technician account is pending approval.")

            return redirect("technician_home")

        except TechnicianRequest.DoesNotExist:
            pass

        # -------------------- 2️⃣ Check normal user from UserRegistration --------------------
        try:
            normal_user = UserRegistration.objects.get(username=username, password=password)
            # Save user info in session
            request.session['user_id'] = normal_user.id
            request.session['username'] = normal_user.username
            messages.success(request, "Login successful!")
            return redirect("user_home")
        except UserRegistration.DoesNotExist:
            # Neither Django user nor UserRegistration found
            # messages.error(request, "Invalid username or password.")
            # return redirect("login")
            request.session["username_error"] = "Invalid username."
            request.session["password_error"] = "Invalid password."
            return redirect("login")  
        

    return render(request, "login.html", context)


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')

# Check if user is admin
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, "admin_page/admin_dashboard.html")

def admin_home(request):
    total_users = UserRegistration.objects.count()
    total_technicians = TechnicianRequest.objects.filter(status="Approved").count()
    total_bookings = Booking.objects.count()
    total_transactions = Payment.objects.count()  # count of all payments

    context = {
        'total_users': total_users,
        'total_technicians': total_technicians,
        'total_bookings': total_bookings,
        'total_transactions': total_transactions,
    }
    return render(request, 'admin_page/admin_home.html', context)

import re
def register_user(request):
    # Pull previous errors from session if they exist
    context = {}
     # --- Retrieve session errors if they exist ---
    for key in ['phone_error', 'email_error', 'username_error', 'name_error', 'password_error', 'profile_error']:
        if key in request.session:
            context[key] = request.session.pop(key)

    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')
        profile_image = request.FILES.get('profile_image')  # file input

        # --- Full Name Validation (only letters and spaces) ---
        if not re.match(r'^[A-Za-z\s]+$', name):
            request.session['name_error'] = "Full name can contain only letters and spaces."
            return redirect('register_user')

        # --- Phone validation ---
        if not re.match(r'^[1-9][0-9]{9}$', phone):
            request.session['phone_error'] = "Phone number must be 10 digits, cannot start with 0 or be all zeros"
            return redirect('register_user')
        
        # --- Email format validation ---
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_regex, email):
            request.session['email_error'] = "Invalid email format."
            return redirect('register_user')
        

        # --- Password & Confirm Password match ---
        if password != confirm_password:
            request.session['password_error'] = "Passwords do not match."
            return redirect('register_user')
        
        # --- Password minimum length check ---
        if len(password) < 6:
            request.session['password_error'] = "Password must be at least 6 characters long."
            return redirect('register_user')

        # --- Username uniqueness ---
        if UserRegistration.objects.filter(username=username).exists():
            request.session['username_error'] = "Username already taken."
            return redirect('register_user')

        # --- Email uniqueness ---
        if UserRegistration.objects.filter(email=email).exists():
            request.session['email_error'] = "Email already registered."
            return redirect('register_user')
        
        # --- Profile image validation ---
        if not profile_image:
            request.session['profile_error'] = "Please upload a profile image."
            return redirect('register_user')

        allowed_extensions = ['jpg', 'jpeg', 'png']
        file_extension = profile_image.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            request.session['profile_error'] = "Only JPG, JPEG, or PNG files are allowed."
            return redirect('register_user')

        # ✅ Save user including phone and profile image
        user = UserRegistration.objects.create(
            username=username,
            email=email,
            password=password,   
            full_name=name,
            phone=phone,
            profile_image=profile_image
        )

        request.session['user_id'] = user.id
        request.session['username'] = user.username

        return redirect('user_dashboard')
    # Pre-fill values (optional)
    context['name'] = request.POST.get('name', '')
    context['username'] = request.POST.get('username', '')
    context['email'] = request.POST.get('email', '')
    context['phone'] = request.POST.get('phone', '')

    return render(request, 'register_user.html', context)


def register_technician(request):

    context = {}

    # Pull previous validation errors from session
    for field in ['full_name_error', 'username_error', 'email_error', 'phone_error', 'profile_image_error','password_error']:
        if field in request.session:
            context[field] = request.session.pop(field)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        city = request.POST.get("city")
        category = request.POST.get("category")
        experience = request.POST.get("experience")
        document = request.FILES.get("document")
        profile_image = request.FILES.get("profile_image")
        id_proof = request.FILES.get("id_proof")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # ✅ Full name validation
        if not re.match(r'^[A-Za-z\s]+$', full_name):
            request.session["name_error"] = "Full name can contain only letters and spaces."
            return redirect("register_technician")
        
        # ✅ Username uniqueness validation
        if TechnicianRequest.objects.filter(username=username).exists():
            request.session['username_error'] = "Username already exists. Please choose another one."
            return redirect('register_technician')
        
         # ✅ Email format validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_regex, email):
            request.session['email_error'] = "Invalid email format."
            return redirect('register_technician')

        # ✅ Email uniqueness validation
        if TechnicianRequest.objects.filter(email=email).exists():
            request.session['email_error'] = "Email already registered. Please use another email."
            return redirect('register_technician')
        
        # ✅ Phone validation — 10 digits, cannot start with 0 or be all zeros
        if not re.match(r'^[1-9][0-9]{9}$', phone):
            request.session['phone_error'] = "Phone number must be 10 digits, cannot start with 0 or be all zeros."
            return redirect('register_technician')
        
        # ✅ Profile Image validation
        if not profile_image:
            request.session['profile_image_error'] = "Profile picture is required."
            return redirect('register_technician')
        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = profile_image.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            request.session['profile_image_error'] = "Profile picture must be a JPG or PNG image."
            return redirect('register_technician')
        
         # ✅ Password length validation
        if len(password) < 6:
            request.session['password_error'] = "Password must be at least 6 characters."
            return redirect('register_technician')

        # ✅ Password match validation
        if password != confirm_password:
            request.session['password_error'] = "Passwords do not match."
            return redirect('register_technician')

        # ✅ Save to DB
        tech = TechnicianRequest(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            city=city,
            category=category,
            experience=experience,
            document=document,
            profile_image=profile_image,
            id_proof=id_proof,
            password=password,   # Save password
            status="Pending"
        )
        tech.save()

        messages.success(request, "Your application has been submitted for admin approval.")
        return redirect("login")

    return render(request, "register_technician.html", context)



def pending_technicians(request):
    # Adjust the filter according to your model's status field
    requests = TechnicianRequest.objects.filter(status="Pending")
    return render(request, "admin_page/pending_technicians.html", {"requests": requests})



def technician_detail(request, pk):
    technician = get_object_or_404(TechnicianRequest, id=pk)
    return render(request, "admin_page/technician_detail.html", {"technician": technician})

# Approve Technician and send email
def approve_technician(request, pk):
    technician = get_object_or_404(TechnicianRequest, pk=pk)

    # ✅ Update status to Approved
    technician.status = "Approved"
    technician.save()

    Notification.objects.create(
        title="Account Approved",
        message=f"Hi {technician.full_name}, your account is now approved! You can log in and start accepting bookings.",
        recipient_type="technicians"
    )

    # ✅ Prepare email
    subject = "Your Technician Account is Approved"
    message = f"""
    Hi {technician.full_name},

    Your technician account for FixItNow has been approved by the admin.

    You can now log in and start receiving service requests.

    Regards,
    FixItNow Team
    """
    recipient_list = [technician.email]

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  # From email
            recipient_list,
            fail_silently=False,
        )
        messages.success(request, f"{technician.full_name} has been approved and email sent ✅")
    except Exception as e:
        messages.warning(request, f"{technician.full_name} approved but email failed ❌\nError: {e}")

    return redirect("pending_technicians")


def reject_technician(request, pk):
    technician = get_object_or_404(TechnicianRequest, pk=pk)
    technician.delete()  # or mark as rejected instead of deleting
    messages.warning(request, f"{technician.full_name} has been rejected ❌")
    return redirect("pending_technicians")

def verified_technicians(request):
    technicians = TechnicianRequest.objects.filter(status="Approved")
    return render(request, "admin_page/verified_technicians.html", {"technicians": technicians})


def verified_tech_detail(request, pk):
    technician = get_object_or_404(TechnicianRequest, id=pk,status="Approved")
    return render(request, "admin_page/verified_tech_detail.html", {"technician": technician})

def delete_technician(request, pk):
    technician = get_object_or_404(TechnicianRequest, pk=pk, status="Approved")
    technician.delete()
    messages.success(request, f"{technician.full_name} has been deleted successfully.")
    return redirect("verified_technicians")


def users_list(request):
    users = UserRegistration.objects.all()
    return render(request, "admin_page/users_list.html", {"users": users})

def delete_user(request, user_id):
    user = get_object_or_404(UserRegistration, id=user_id)
    user.delete()
    return redirect('users_list')


def send_notification(request):
    if request.method == "POST":
        title = request.POST.get("title")
        message_text = request.POST.get("message")
        recipient_type = request.POST.get("recipient_type")

        if title and message_text:
            Notification.objects.create(
                title=title,
                message=message_text,
                recipient_type=recipient_type
            )
            messages.success(request, "Notification sent successfully!")
            return redirect("send_notification")
        else:
            messages.error(request, "Title and message cannot be empty.")

    return render(request, "admin_page/send_notification.html")


def admin_feedback_view(request):
    # Get all feedbacks
    feedbacks = Feedback.objects.select_related('user', 'technician').order_by('-created_at')
    context = {
        'feedbacks': feedbacks
    }
    return render(request, 'admin_page/admin_feedbacks.html', context)

def admin_completed_bookings(request):
    # Use 'status' instead of 'completion_status'
    bookings = Booking.objects.filter(status='Completed').order_by('-date')  # date field is your booking date
    context = {
        'bookings': bookings
    }
    return render(request, 'admin_page/admin_completed_bookings.html', context)

def admin_transaction_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id) 
    payment = getattr(booking, 'payment', None)  # in case Payment has OneToOne relation

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'admin_page/admin_transaction_detail.html', context)



def user_dashboard(request):
    user_obj = None
    notifications = []

    if 'user_id' in request.session:
        try:
            user_obj = UserRegistration.objects.get(id=request.session['user_id'])

            # Fetch all notifications for users and both
            notifications = Notification.objects.filter(
                recipient_type__in=["users", "both"]
            ).order_by('-created_on')  # all notifications

        except UserRegistration.DoesNotExist:
            user_obj = None

    return render(request, 'user_page/user_dashboard.html', {
        'user_obj': user_obj,
        'notifications': notifications
    })


def user_home(request):
    user_obj = None
    if 'user_id' in request.session:
        try:
            user_obj = UserRegistration.objects.get(id=request.session['user_id'])
        except UserRegistration.DoesNotExist:
            return redirect('login')  # if session user not found
    else:
        return redirect('login')  # if not logged in

    return render(request, 'user_page/user_home.html', {'user_obj': user_obj})


def user_services(request):
    # Fetch logged-in user
    user_obj = None
    if 'user_id' in request.session:
        try:
            user_obj = UserRegistration.objects.get(id=request.session['user_id'])
        except UserRegistration.DoesNotExist:
            return redirect('login')
    else:
        return redirect('login')

    # Define the service details manually
    services = [
        {"name": "Electrician", "description": "Wiring, installations, repairs, and electrical maintenance.", "icon": "ri-flashlight-line", "color": "blue"},
        {"name": "Plumber", "description": "Pipe repairs, installations, drain cleaning, and emergency plumbing.", "icon": "ri-drop-line", "color": "green"},
        {"name": "HVAC", "description": "Heating, ventilation, AC installation, repair, and maintenance.", "icon": "ri-tools-line", "color": "orange"},
        {"name": "Carpentry", "description": "Custom woodwork, furniture repair, cabinet installation, and general carpentry.", "icon": "ri-hammer-line", "color": "purple"},
        {"name": "Mechanical", "description": "Car repairs, maintenance, diagnostics, and mobile mechanic services.", "icon": "ri-car-line", "color": "indigo"},
        {"name": "Painting", "description": "Interior and exterior painting, wall preparation, and decorative finishes.", "icon": "ri-paint-brush-line", "color": "teal"},
    ]

    # Count approved technicians per category
    for service in services:
        service['tech_count'] = TechnicianRequest.objects.filter(category=service["name"], status='Approved').count()

    return render(request, "user_page/user_services.html", {
        "services": services,
        "user_obj": user_obj  
    })

def user_tech_list(request):
    user_obj = None
    category = request.GET.get('category')

    # Fetch user if logged in
    if 'user_id' in request.session:
        try:
            user_obj = UserRegistration.objects.get(id=request.session['user_id'])
        except UserRegistration.DoesNotExist:
            user_obj = None

    technicians = TechnicianRequest.objects.filter(status="Approved")
    if category:
        technicians = technicians.filter(category=category)

    # List of technician IDs favorited by the logged-in user
    if user_obj:
        favorited_ids = FavoriteTechnician.objects.filter(user=user_obj).values_list('technician_id', flat=True)
    else:
        favorited_ids = []

    return render(request, "user_page/user_tech_list.html", {
        "user_obj": user_obj,
        "technicians": technicians,
        "favorited_ids": favorited_ids,
        "category_name": category
    })


def toggle_favorite_technician(request):
    if request.method == 'POST':
        tech_id = request.POST.get('tech_id')
        try:
            tech = TechnicianRequest.objects.get(id=tech_id)
        except TechnicianRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Technician not found'})

        # Fetch logged-in user
        user_obj = None
        if 'user_id' in request.session:
            try:
                user_obj = UserRegistration.objects.get(id=request.session['user_id'])
            except UserRegistration.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Not logged in'})

        # Toggle favorite in FavoriteTechnician table ONLY
        favorite, created = FavoriteTechnician.objects.get_or_create(user=user_obj, technician=tech)

        if created:
            status = 'added'   # Heart turns red
        else:
            favorite.delete()
            status = 'removed' # Heart turns white

        return JsonResponse({'status': status})

def user_favorite_list(request):
    user_obj = None
    if 'user_id' in request.session:
        try:
            user_obj = UserRegistration.objects.get(id=request.session['user_id'])
        except UserRegistration.DoesNotExist:
            user_obj = None

    # Fetch favorite technicians for this user
    favorite_techs = FavoriteTechnician.objects.filter(user=user_obj).select_related('technician') if user_obj else []

    return render(request, "user_page/user_favorite_list.html", {
        "favorite_techs": favorite_techs,
        "user_obj": user_obj
    })

def book_now(request, tech_id):
    technician = get_object_or_404(TechnicianRequest, id=tech_id, status='Approved')
    user_obj = None
    user_id = request.session.get('user_id')
    if user_id:
        user_obj = UserRegistration.objects.get(id=user_id)

    if request.method == 'POST':
        date_input = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        repair_details = request.POST.get('repair_details')

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
            date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date or time format!")
            return redirect('book_now', tech_id=tech_id)

        # Check if slot is available
        availability = TechnicianAvailability.objects.filter(
            technician=technician,
            date=date_obj,
            start_time__lte=start_time,
            end_time__gte=end_time,
            status='Available'
        ).first()

        if not availability:
            messages.error(request, "Selected time slot is not available.")
            return redirect('book_now', tech_id=tech_id)

        # Save booking
        booking = Booking.objects.create(
            user=user_obj,
            technician=technician,
            date=date_obj,
            time_slot=f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}",
            repair_details=repair_details,
            status='Booked'
        )

        # Update availability: split the slot if necessary
        if availability.start_time < start_time:
            TechnicianAvailability.objects.create(
                technician=technician,
                date=date_obj,
                start_time=availability.start_time,
                end_time=start_time,
                status='Available'
            )

        if availability.end_time > end_time:
            TechnicianAvailability.objects.create(
                technician=technician,
                date=date_obj,
                start_time=end_time,
                end_time=availability.end_time,
                status='Available'
            )

        # Mark booked slot as unavailable
        availability.status = 'Booked'
        availability.start_time = start_time
        availability.end_time = end_time
        availability.save()

        messages.success(request, f"Booking confirmed for {date_obj} with {technician.full_name}")
        return redirect('my_bookings')

    # Show available slots
    schedule = TechnicianAvailability.objects.filter(
        technician=technician,
        date__gte=date.today(),
        status='Available'  # only available slots
    ).order_by('date', 'start_time')

    # Fetch user bookings
    bookings = Booking.objects.filter(user=user_obj, technician=technician).order_by('-date')

    feedbacks = Feedback.objects.filter(technician=technician).order_by('-created_at')

    return render(request, 'user_page/book_now.html', {
        'technician': technician,
        'user_obj': user_obj,
        'schedule': schedule,
        'bookings': bookings,
        'feedbacks': feedbacks
    })


def user_profile(request):
    user_id = request.session.get('user_id')  # or use request.user.id if using Django auth
    user_obj = get_object_or_404(UserRegistration, id=user_id)

    if request.method == 'POST':
        # Update fields
        user_obj.full_name = request.POST.get('full_name')
        user_obj.phone = request.POST.get('phone')
        user_obj.address = request.POST.get('address')  # manually entered
        user_obj.city = request.POST.get('city')        # auto-detected
        user_obj.latitude = request.POST.get('latitude') 
        user_obj.longitude = request.POST.get('longitude')

        # Convert latitude and longitude to float if they exist
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')

        user_obj.latitude = float(lat) if lat else None
        user_obj.longitude = float(lon) if lon else None

        profile_image = request.FILES.get('profile_image')
        if profile_image:
            user_obj.profile_image = profile_image

        user_obj.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('user_profile')

    context = {
        'user_obj': user_obj
    }
    return render(request, 'user_page/user_profile.html', context)

def my_bookings(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user_obj = UserRegistration.objects.get(id=user_id)
    bookings = Booking.objects.filter(user=user_obj).order_by('-id')

    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        try:
            booking = Booking.objects.get(id=booking_id, user=user_obj)
            
            # Parse start and end times from booking.time_slot
            start_str, end_str = booking.time_slot.split(" - ")
            start_time = datetime.strptime(start_str.strip(), "%I:%M %p").time()
            end_time = datetime.strptime(end_str.strip(), "%I:%M %p").time()

            # Update corresponding TechnicianAvailability slot
            availability = TechnicianAvailability.objects.filter(
                technician=booking.technician,
                date=booking.date,
                start_time=start_time,
                end_time=end_time
            ).first()

            if availability:
                availability.status = "Available"
                availability.save()

                # --- MERGE ADJACENT AVAILABLE SLOTS ---
                adjacents = TechnicianAvailability.objects.filter(
                    technician=booking.technician,
                    date=booking.date,
                    status='Available'
                ).order_by('start_time')

                merged_slots = []
                current_start = None
                current_end = None

                for slot in adjacents:
                    if current_start is None:
                        current_start = slot.start_time
                        current_end = slot.end_time
                    else:
                        # Check if slot is adjacent
                        if slot.start_time <= current_end:
                            # Extend current_end
                            current_end = max(current_end, slot.end_time)
                        else:
                            # Save merged slot
                            merged_slots.append((current_start, current_end))
                            current_start = slot.start_time
                            current_end = slot.end_time

                if current_start is not None:
                    merged_slots.append((current_start, current_end))

                # Delete old slots and create merged slots
                TechnicianAvailability.objects.filter(
                    technician=booking.technician,
                    date=booking.date,
                    status='Available'
                ).delete()

                for start, end in merged_slots:
                    TechnicianAvailability.objects.create(
                        technician=booking.technician,
                        date=booking.date,
                        start_time=start,
                        end_time=end,
                        status='Available'
                    )
                # --- END MERGE ---

            booking.delete()
            messages.success(request, "Booking cancelled successfully!")

        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
        except Exception as e:
            messages.error(request, f"Error cancelling booking: {e}")

        return redirect('my_bookings')

    return render(request, 'user_page/my_bookings.html', {'bookings': bookings, 'user_obj': user_obj})


def user_payment_history(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    user_obj = get_object_or_404(UserRegistration, id=user_id)

    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        method = request.POST.get("method")
        try:
            payment = Payment.objects.get(id=payment_id, booking__user=user_obj)
            payment.payment_status = "Paid"
            payment.payment_method = method
            payment.payment_date = timezone.now()
            payment.save()
            messages.success(request, "Payment successful!")
        except Payment.DoesNotExist:
            messages.error(request, "Payment record not found.")
        return redirect("user_payment_history")

    payments = Payment.objects.filter(booking__user=user_obj).order_by('-payment_date')
    notifications = Notification.objects.filter(
        recipient_type__in=["users", "both"]
    ).order_by('-created_on')

    return render(request, "user_page/user_payment_history.html", {
        "payments": payments,
        "notifications": notifications,
        "user_obj": user_obj
    })


def user_feedback(request, tech_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user_obj = UserRegistration.objects.get(id=user_id)
    technician = TechnicianRequest.objects.get(id=tech_id, status="Approved")

    if request.method == "POST":
        comment = request.POST.get("feedback")
        rating = int(request.POST.get("rating", 5))

        Feedback.objects.create(
            user=user_obj,
            technician=technician,
            rating=rating,
            comment=comment
        )

        messages.success(request, "Feedback submitted successfully!")
        return redirect('user_payment_history')

    return render(request, "user_page/user_feedback.html", {
        "technician": technician,
        "user_obj": user_obj
    })


def view_user_feedback(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user_obj = UserRegistration.objects.get(id=user_id)

    # Fetch all feedback submitted by this user
    feedbacks = Feedback.objects.filter(user=user_obj).order_by('-created_at')

    return render(request, 'user_page/view_user_feedback.html', {
        'user_obj': user_obj,
        'feedbacks': feedbacks
    })

from functools import wraps


def approved_technician_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        tech_id = request.session.get("technician_id")
        if not tech_id:
            messages.error(request, "Please login first.")
            return redirect("login")

        technician = TechnicianRequest.objects.filter(id=tech_id).first()
        if not technician:
            messages.error(request, "Technician not found.")
            return redirect("login")

        if technician.status != "Approved":
            messages.error(request, "Your account is still pending approval.")
            return redirect("technician_home")  # or another page for pending status

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def technician_dashboard(request):
    tech_id = request.session.get("technician_id")
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = TechnicianRequest.objects.filter(id=tech_id).first()
    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    return render(request, "technician_page/technician_dashboard.html", {
        "technician": technician,
        "notifications": notifications
    })


def technician_home(request):
    tech_id = request.session.get('technician_id')
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = TechnicianRequest.objects.filter(id=tech_id).first()
    if not technician:
        return redirect("login")

    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    # Decide what content to show based on status
    if technician.status == "Approved":
        # Approved -> show welcome home
        return render(request, 'technician_page/technician_home.html', {
            'technician': technician,
            'notifications': notifications,
            'approved': True,  # flag for template
        })
    else:
        # Pending -> show pending approval message
        return render(request, 'technician_page/technician_home.html', {
            'technician': technician,
            'approved': False,  # flag for template
        })

@approved_technician_required
def technician_profile(request):
    tech_id = request.session.get('technician_id')
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = get_object_or_404(TechnicianRequest, id=tech_id)
    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    if request.method == "POST":
        # Update fields
        technician.full_name = request.POST.get('full_name')
        technician.phone = request.POST.get('phone')
        technician.category = request.POST.get('category')
        technician.experience = request.POST.get('experience')
        technician.city = request.POST.get('city')        # auto-detected city

        # Latitude/Longitude validation
        lat = request.POST.get('latitude')
        lon = request.POST.get('longitude')
        technician.latitude = float(lat) if lat else None
        technician.longitude = float(lon) if lon else None

        # Optional profile image update
        profile_image = request.FILES.get('profile_image')
        if profile_image:
            technician.profile_image = profile_image

        technician.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('technician_profile')

    return render(request, 'technician_page/technician_profile.html', {
        'technician': technician,
        'notifications': notifications})

@approved_technician_required
def my_calendar(request):
    tech_id = request.session.get('technician_id')
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = TechnicianRequest.objects.get(id=tech_id)
    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    

    if request.method == 'POST':
        date_input = request.POST.get('date')
        start_time_str = request.POST.get('start_time')  # e.g., "10:00 AM"
        end_time_str = request.POST.get('end_time')      # e.g., "12:00 PM"
        status = request.POST.get('status')


        # Convert string times to time objects
        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            messages.error(request, "Invalid time format!")
            return redirect('technician_calendar')

        TechnicianAvailability.objects.create(
            technician=technician,
            date=date_input,
            start_time=start_time,
            end_time=end_time,
            status=status
        )
        messages.success(request, "Schedule added successfully!")
        return redirect('technician_calendar')

    schedule_list = TechnicianAvailability.objects.filter(
        technician=technician,
        date__gte=date.today()
    ).order_by('-date', 'start_time')

    return render(request, 'technician_page/technician_calendar.html', {
        'technician': technician,
        'notifications': notifications,
        'schedule_list': schedule_list,
    })


def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(TechnicianAvailability, id=schedule_id)

    if schedule.status == 'Available':
        schedule.delete()
        messages.success(request, "Schedule deleted successfully.")
    else:
        messages.error(request, "Cannot delete a booked schedule.")

    return redirect('technician_calendar')

@approved_technician_required
def technician_bookings(request):
    tech_id = request.session.get("technician_id")
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = TechnicianRequest.objects.get(id=tech_id)
    filter_status = request.GET.get('status', 'Booked')  # default = Pending(Booked)

    # ✅ Filter bookings based on selected tab
    bookings = Booking.objects.filter(technician=technician, status=filter_status).order_by('-date')

    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    # ✅ Handle Accept / Reject
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")

        try:
            booking = Booking.objects.get(id=booking_id, technician=technician)
            start_str, end_str = booking.time_slot.split(" - ")
            start_time = datetime.strptime(start_str.strip(), "%I:%M %p").time()
            end_time = datetime.strptime(end_str.strip(), "%I:%M %p").time()

            if action == "accept":
                booking.status = "Accepted"
                booking.save()
                messages.success(request, "Booking accepted successfully!")
                return redirect(f"{reverse('technician_bookings')}?status=Accepted")

                                
            elif action == "reject":
                booking.status = "Rejected"
                booking.save()
                availability = TechnicianAvailability.objects.filter(
                    technician=booking.technician,
                    date=booking.date,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                if availability:
                    availability.status = "Available"
                    availability.save()
                messages.info(request, "Booking rejected and slot reopened.")
                return redirect(f"{reverse('technician_bookings')}?status=Rejected")


            elif action == "complete":
                booking.status = "Completed"
                booking.save()
                messages.success(request, "Booking marked as completed!")
                return redirect(f"{reverse('technician_bookings')}?status=Completed")

        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
        except Exception as e:
            messages.error(request, f"Error processing booking: {e}")

        return redirect('technician_bookings')  # reload default (pending)

    return render(request, 'technician_page/technician_bookings.html', {
        'technician': technician,
        'bookings': bookings,
        'notifications': notifications,
        'filter_status': filter_status,  # send current tab
    })


def payment_details(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    tech_id = request.session.get("technician_id")
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")
    
    technician = get_object_or_404(TechnicianRequest, id=tech_id)
    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    if request.method == "POST":
        # Create Payment only when form is submitted
        labour_charge = request.POST.get("labour_charge", 0)
        item_charge = request.POST.get("item_charge", "")
        additional_charge = request.POST.get("additional_charge", "")

        total = (float(labour_charge) if labour_charge else 0) + \
                (float(item_charge) if item_charge else 0) + \
                (float(additional_charge) if additional_charge else 0)

        payment = Payment.objects.create(
            booking=booking,
            repair_description=request.POST.get("repair_description", ""),
            labour_charge=float(labour_charge) if labour_charge else 0,
            item_charge=float(item_charge) if item_charge else 0,
            additional_charge=float(additional_charge) if additional_charge else 0,
            total_amount=total,
            payment_status="Pending"
        )

        booking.status = "Completed"
        booking.save()

        messages.success(request, "Payment details submitted successfully!")
        return redirect(f"{reverse('technician_bookings')}?status=Completed")

    return render(request, "technician_page/payment_details.html", {
        "booking": booking,
        "technician": technician,
        "notifications": notifications
    })



def technician_payment_history(request):
    tech_id = request.session.get("technician_id")
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = TechnicianRequest.objects.get(id=tech_id)
    payments = Payment.objects.filter(booking__technician=technician).order_by('-payment_date')

    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    return render(request, "technician_page/technician_payment_history.html", {
        "technician": technician,
        "payments": payments,
        "notifications": notifications
    })


def delete_payment(request, payment_id):
    tech_id = request.session.get("technician_id")
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    if request.method == "POST":
        payment = get_object_or_404(Payment, id=payment_id)

        # Optional: double-check ownership before deleting
        if payment.booking.technician.id != tech_id:
            messages.error(request, "Unauthorized action.")
            return redirect("technician_payment_history")

        # Delete payment
        payment.delete()
        messages.success(request, "Payment record deleted successfully!")

        # Redirect back to payment history
        return redirect("technician_payment_history")

    return redirect("technician_payment_history")

@approved_technician_required
def technician_feedbacks(request):
    tech_id = request.session.get('technician_id')
    if not tech_id:
        messages.error(request, "Please login first.")
        return redirect("login")

    technician = get_object_or_404(TechnicianRequest, id=tech_id)
    feedbacks = Feedback.objects.filter(technician=technician).order_by('-created_at')
    # Only notifications sent after technician applied
    notifications = Notification.objects.filter(
        recipient_type__in=["technicians", "both"],
        created_on__gte=technician.applied_on  # use applied_on
    ).order_by('-created_on')

    return render(request, "technician_page/technician_feedbacks.html", {
        "technician": technician,
        "feedbacks": feedbacks,
        "notifications": notifications
    })

# views.py
from django.http import JsonResponse
from math import radians, cos, sin, asin, sqrt
from .models import TechnicianRequest, UserRegistration

def haversine(lat1, lon1, lat2, lon2):
    # Haversine formula to calculate distance in km
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

def find_nearby_technicians(request):
    user_id = request.session.get('user_id')
    category = request.GET.get('category')
    location = request.GET.get('location')
    max_distance = 10  # km

    if not user_id:
        return JsonResponse({"technicians": []})

    user = UserRegistration.objects.get(id=user_id)
    technicians = TechnicianRequest.objects.filter(status='Approved', category=category)
    if category:
        technicians = technicians.filter(category__iexact=category)
    if location:
        technicians = technicians.filter(city__icontains=location)
    

    nearby = []
    favorited_ids = FavoriteTechnician.objects.filter(user=user).values_list('technician_id', flat=True)

    for tech in technicians:
        if tech.latitude and tech.longitude:
            distance = haversine(user.latitude, user.longitude, tech.latitude, tech.longitude)
            if distance <= max_distance:
                nearby.append({
                    "id": tech.id,
                    "full_name": tech.full_name,
                    "city": tech.city,
                    "category": tech.category,
                    "distance": distance,
                    'experience': tech.experience,
                    "profile_image": tech.profile_image.name if tech.profile_image else None
                })

    return JsonResponse({"technicians": nearby, "favorited_ids": list(favorited_ids)})

