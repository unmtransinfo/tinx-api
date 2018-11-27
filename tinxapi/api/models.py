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
    ordering = ('name',)
    db_table = u'tinx_disease'

  def save(self, *args, **kwargs):
    raise Exception("This model is read-only")


class DiseaseMetadata(models.Model):
  tcrd_model = True

  id = models.IntegerField(primary_key=True)
  disease = models.ForeignKey(Disease)
  num_important_targets = models.IntegerField()
  category = models.TextField()


class DTO(models.Model):
  tcrd_model = True

  id = models.CharField(max_length=255, primary_key=True)
  name = models.TextField()
  parent = models.CharField(max_length=255) # Actually a self-referential foreign key.


  class Meta:
    db_table = u'dto'


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
  dto = models.ForeignKey(DTO, db_column='dtoid')

  class Meta:
    ordering = ('id', )
    db_table = 'protein'


class ProteinMetadata(models.Model):
  tcrd_model = True

  id = models.IntegerField(primary_key=True)
  protein = models.ForeignKey(Protein)
  num_important_diseases = models.IntegerField


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
  target = models.ForeignKey(Target, primary_key=True)
  protein = models.ForeignKey(Protein)

  class Meta:
    db_table = 't2tc'


class Novelty(models.Model):
  tcrd_model = True
  id = models.IntegerField(primary_key=True)
  protein = models.ForeignKey(Protein)
  score = models.DecimalField(max_digits=34, decimal_places=16)

  class Meta:
    db_table = 'tinx_novelty'


class Importance(models.Model):
  tcrd_model = True
  id = models.IntegerField(primary_key=True)
  protein = models.ForeignKey(Protein)
  disease = models.ForeignKey(Disease)
  score = models.DecimalField(max_digits=34, decimal_places=16)

  class Meta:
    db_table = 'tinx_importance'

class NDSRank(models.Model):
  tcrd_model = True
  id = models.IntegerField(primary_key=True)
  importance = models.ForeignKey(Importance)
  rank = models.IntegerField


class PubmedArticle(models.Model):
  tcrd_model = True
  id = models.IntegerField(primary_key=True)
  title  = models.TextField()
  journal = models.TextField()
  date = models.CharField(max_length=10)
  authors = models.TextField()
  abstract = models.TextField()

  class Meta:
    db_table = 'pubmed'

