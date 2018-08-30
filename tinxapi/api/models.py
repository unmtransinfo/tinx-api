# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Disease(models.Model):
  tcrd_model = True

  id = models.IntegerField(primary_key=True)
  doid = models.CharField(max_length=20)
  name = models.TextField()
  summary = models.TextField()
  score = models.DecimalField(max_digits=34, decimal_places=16)

  class Meta:
    ordering = ('id',)
    db_table = u'tinx_disease'

  def save(self, *args, **kwargs):
    raise Exception("This model is read-only")

