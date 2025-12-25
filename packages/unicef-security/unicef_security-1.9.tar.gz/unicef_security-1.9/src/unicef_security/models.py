from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.functional import cached_property

app_label = "unicef_security"


class TimeStampedModel:
    last_modify_date = models.DateTimeField(editable=False, blank=True, auto_now_add=True, auto_now=True)


class SecurityMixin(models.Model):
    azure_id = models.UUIDField(blank=True, unique=True, null=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    display_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta(AbstractUser.Meta):
        abstract = True
        app_label = "unicef_security"

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.label
        super().save(*args, **kwargs)

    @cached_property
    def label(self):
        if self.display_name:
            return self.display_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}:"
        if self.first_name:
            return self.first_name
        return self.username
