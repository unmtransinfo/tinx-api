# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.


class Disease(models.Model):
    tcrd_model = True

    # id = models.IntegerField(primary_key=True)
    doid = models.CharField(max_length=20, primary_key=True)
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
    tcrd_meta = True

    id = models.IntegerField(primary_key=True)
    tinx_disease = models.ForeignKey(Disease, on_delete=models.PROTECT)
    num_important_targets = models.IntegerField()

    class Meta:
        db_table = u'tinx_disease_metadata'


class DTO(models.Model):
    tcrd_model = True

    id = models.CharField(max_length=255, primary_key=True, db_column='dtoid')
    name = models.TextField()
    parent = models.CharField(max_length=255, db_column='parent_id')  # Actually a self-referential foreign key.
    definition = models.CharField(max_length=255, db_column='def')

    class Meta:
        db_table = u'dto'


class DoParent(models.Model):
    tcrd_model = True

    doid = models.CharField(max_length=20, primary_key=True)
    parent_id = models.CharField(max_length=20)

    class Meta:
        db_table = u"do_parent"


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
    dto = models.ForeignKey(DTO, db_column='dtoid', on_delete=models.PROTECT)

    class Meta:
        ordering = ('id',)
        db_table = 'protein'


class ProteinMetadata(models.Model):
    tcrd_model = True
    tcrd_meta = True

    id = models.IntegerField(primary_key=True)
    protein = models.ForeignKey(Protein, on_delete=models.PROTECT)
    num_important_targets = models.IntegerField()

    class Meta:
        ordering = ('id',)
        db_table = 'tinx_protein_metadata'


class Target(models.Model):
    tcrd_model = True

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    ttype = models.CharField(max_length=255)
    tdl = models.CharField(max_length=255)
    fam = models.CharField(max_length=255)
    famext = models.CharField(max_length=255)
    comment = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ('id',)
        db_table = 'target'


class TinxTarget(models.Model):
    tcrd_model = True

    target = models.ForeignKey(Target, primary_key=True, on_delete=models.PROTECT)
    protein = models.ForeignKey(Protein, on_delete=models.PROTECT)
    uniprot = models.CharField(max_length=255)
    sym = models.CharField(max_length=255)
    tdl = models.CharField(max_length=255)
    fam = models.CharField(max_length=255)
    family = models.CharField(max_length=255)

    class Meta:
        db_table = 'tinx_target'


class T2TC(models.Model):
    tcrd_model = True

    target = models.OneToOneField(Target, primary_key=True, on_delete=models.PROTECT)
    protein = models.ForeignKey(Protein, on_delete=models.PROTECT)

    class Meta:
        db_table = 't2tc'


class Novelty(models.Model):
    tcrd_model = True

    id = models.IntegerField(primary_key=True)
    protein = models.ForeignKey(Protein, on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=34, decimal_places=16)

    class Meta:
        db_table = 'tinx_novelty'


class Importance(models.Model):
    tcrd_model = True

    protein = models.ForeignKey(Protein, db_column='protein_id', on_delete=models.PROTECT)
    disease = models.ForeignKey(Disease, db_column='doid', primary_key=True, on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=34, decimal_places=16)

    class Meta:
        db_table = 'tinx_importance'


class Ancestor(models.Model):
    tcrd_meta = True

    doid = models.CharField(max_length=255, primary_key=True)
    max_ancestor = models.CharField(max_length=255)
    ancestor_path = models.CharField(max_length=255)

    class Meta:
        db_table = 'tinx_disease_ancestors'


class NDSRank(models.Model):
    tcrd_model = True

    id = models.IntegerField(primary_key=True)
    importance = models.ForeignKey(Importance, db_column='tinx_importance_id', on_delete=models.PROTECT)
    rank = models.IntegerField()

    class Meta:
        db_table = u'tinx_nds_rank'


class PubmedArticle(models.Model):
    tcrd_model = True

    id = models.IntegerField(primary_key=True)
    title = models.TextField()
    journal = models.TextField()
    date = models.CharField(max_length=10)
    authors = models.TextField()
    abstract = models.TextField()

    class Meta:
        db_table = 'pubmed'
