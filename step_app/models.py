from django.db import models
from django.utils.translation import gettext_lazy as _

class Step(models.Model):
    tittle = models.CharField(_('Tittle'), max_length=150)

    def __str__(self):
        return self.tittle


