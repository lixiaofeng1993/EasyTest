from django.db import models
from base.models import Project


# Create your models here.

class Api(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    method = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    body = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name