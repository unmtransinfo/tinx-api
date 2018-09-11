# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import filters

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework_filters.backends import DjangoFilterBackend

from models import *
from serializers import *
from filters import *
from paginators import RestrictedPagination


class DiseaseViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  serializer_class = DiseaseSerializer
  filter_backends = (filters.SearchFilter,)
  search_fields = ('^name',)

  def get_queryset(self):
    if 'parent_id' in self.kwargs:
        parent_id = self.kwargs['parent_id']
        parent = Disease.objects.filter(id=parent_id).first()
        return Disease.objects.extra(tables=['do_parent'],
                                     where=['do_parent.doid = tinx_disease.doid',
                                            'do_parent.parent=%s'],
                                     params=[parent.doid],
                                     select={'parent_id': 'do_parent.parent'}).all()
    else:
        return Disease.objects.all()


class TargetViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
  pagination_class = RestrictedPagination

  queryset = T2TC.objects\
    .select_related('target')\
    .select_related('protein')\
    .extra(tables=['tinx_novelty'],
           where=['tinx_novelty.protein_id = t2tc.protein_id'],
           select={'novelty': 'tinx_novelty.score'})\
    .all()

  serializer_class = TargetSerializer
  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  search_fields = ('^protein__sym', '^target__name')
  filter_class = TargetFilter


class TargetDiseasesViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  serializer_class = TargetDiseaseSerializer

  def get_queryset(self):
    protein = Protein.objects \
      .prefetch_related('importance_set') \
      .prefetch_related() \
      .filter(id = self.kwargs['target_id']) \
      .first()
    return protein._prefetched_objects_cache['importance'].all()


  def retrieve(self, request, *args, **kwargs):
    queryset = self.get_queryset()
    result = get_object_or_404(queryset, disease__id = kwargs['pk'])
    serializer = self.serializer_class(result)
    return Response(serializer.data)


class DiseaseTargetsViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  serializer_class = DiseaseTargetSerializer


  def get_queryset(self):
      disease = Disease.objects\
          .prefetch_related('importance_set')\
          .prefetch_related()\
          .filter(id = self.kwargs['disease_id'])  \
          .first()

      return disease._prefetched_objects_cache['importance'] \
          .prefetch_related('protein') \
          .extra(tables=['tinx_novelty', 't2tc', 'target'],
                 where=['tinx_novelty.protein_id = tinx_importance.protein_id',
                        't2tc.protein_id = tinx_importance.protein_id',
                        'target.id = t2tc.target_id'],
                 select={'novelty': 'tinx_novelty.score',
                         'target_id': 'target.id',
                         'target_name': 'target.name',
                         'target_fam': 'target.fam',
                         'target_famext' : 'target.famext',
                         'target_tdl' : 'target.tdl'})


  def retrieve(self, request, *args, **kwargs):
    queryset = self.get_queryset()
    result = get_object_or_404(queryset, protein__id = kwargs['pk'])
    serializer = self.serializer_class(result)
    return Response(serializer.data)


class ArticleViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  serializer_class = PubmedArticleSerializer

  queryset = PubmedArticle.objects.all()

  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  filter_class = PubmedArticleFilter
  search_fields = ('title',)
