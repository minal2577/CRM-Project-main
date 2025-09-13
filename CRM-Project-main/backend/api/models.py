from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save

# Create your models here.


class User(AbstractUser):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def profile(self):
        profile = Profile.objects.get(user=self)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=1000)
    verified = models.BooleanField(default=False)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Record(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=20)


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)


class Customer(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    visits = models.PositiveIntegerField(default=0)
    last_active_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Order(models.Model):
    STATUS_CHOICES = (
        ("CREATED", "CREATED"),
        ("PAID", "PAID"),
        ("CANCELLED", "CANCELLED"),
        ("REFUNDED", "REFUNDED"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="CREATED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.amount} - {self.status}"


class Segment(models.Model):
    name = models.CharField(max_length=120)
    rules = models.JSONField(default=dict)
    audience_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Segment({self.name})"


class Campaign(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name="campaigns")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Campaign #{self.id} -> {self.segment.name}"


class CommunicationLog(models.Model):
    STATUS_CHOICES = (
        ("SENT", "SENT"),
        ("FAILED", "FAILED"),
        ("PENDING", "PENDING"),
    )

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="logs")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="communications")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="PENDING")
    vendor_message_id = models.CharField(max_length=64, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CommLog #{self.id} - {self.customer.email} - {self.status}"
