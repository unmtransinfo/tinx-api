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

class Protein(models.Model):
  tcrd_model = True

  id = models.IntegerField(primary_key=True)
  name = models.CharField(max_length=255)
  description = models.TextField()
  uniprot = models.CharField(max_length=20)
  up_version = models.IntegerField()
  geneid = models.IntegerField()
  sym = models.CharField(max_length=20)
  family = models.CharField(max_length=255)

  # TODO: This will need to become a foreign key!
  dtoid = models.CharField(max_length=13)

  class Meta:
    ordering = ('id', )
    db_table = 'protein'


class Target(models.Model):
  tcrd_model = True

  id = models.IntegerField(primary_key=True)
  name = models.CharField(max_length=255)
  ttype = models.CharField(max_length=255)
  description = models.TextField()
  tdl = models.CharField(max_length=255)
  fam = models.CharField(max_length=255)
  famext = models.CharField(max_length=255)

  class Meta:
    ordering = ('id', )
    db_table = 'target'


class T2TC(models.Model):
  tcrd_model = True
  target_id = models.ForeignKey(Target)
  protein_id = models.ForeignKey(Protein)
