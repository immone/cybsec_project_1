from django.db import models

from django.contrib.auth.models import User

class Resource(models.Model):
    name = models.TextField()
    available = models.IntegerField(default=0)

class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    resources = models.ManyToManyField(Resource)
    currency = models.IntegerField(default=0)

