from django.db import models
from property_app.models import Property


class Summary(models.Model):
    property = models.OneToOneField(
        Property, 
        on_delete=models.CASCADE, 
        related_name='summary', 
        db_column='property_id'
    )
    summary = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Summeries"

    def __str__(self):
        return f"Summary for Property: {self.property.title}"