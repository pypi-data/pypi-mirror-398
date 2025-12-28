from django.db import models

# Create your models here.
class Acc(models.Model):
    name = models.CharField(max_length=100)