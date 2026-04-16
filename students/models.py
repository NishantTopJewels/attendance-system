from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    age = models.IntegerField(default=0)
    roll_number = models.IntegerField(unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.roll_number} - {self.first_name} {self.last_name}"
