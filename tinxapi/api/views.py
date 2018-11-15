# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import filters
from rest_framework.decorators import action

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
  """
  list:
  Browse all diseases in the database.

  retrieve:
  Get information about a specific disease.

  children:
  Retrieve a list of this disease's children.
  """
  base_query = Disease.objects.extra(
    tables=['tinx_disease_metadata'],
    where=['tinx_disease_metadata.tinx_disease_id = tinx_disease.id'],
    select={'num_important_targets' : 'tinx_disease_metadata.num_important_targets'}
  )
  queryset = base_query.all()
  pagination_class = RestrictedPagination
  serializer_class = DiseaseWithMetadataSerializer
  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  filter_class = DiseaseFilter
  search_fields = ('^name',)

  @action(detail = True)
  def children(self, request, *args, **kwargs):
    parent = self.get_object()
    queryset = self.base_query.extra(tables=['do_parent'],
                                     where=['do_parent.doid = tinx_disease.doid',
                                            'do_parent.parent=%s'],
                                     params=[parent.doid],
                                     select={'parent_id': 'do_parent.parent'}).all()
    return Response(self.serializer_class(queryset, many=True, context={'request': request}).data)

  @action(detail = True)
  def parent(self, request, *args, **kwargs):
    child = self.get_object()
    queryset = self.base_query.extra(tables=['do_parent'],
                                     where=['do_parent.parent = tinx_disease.doid',
                                            'do_parent.doid=%s'],
                                     params=[child.doid],
                                     select={'parent_id': 'do_parent.parent'}).first()
    return Response(self.serializer_class(queryset, many=False, context={'request': request}).data)





class TargetViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
  """
  list:
  Browse all targets in the database.

  retrieve:
  Get information about a specific target.
  """
  pagination_class = RestrictedPagination

  queryset = T2TC.objects\
    .select_related('target')\
    .select_related('protein')\
    .extra(tables=['tinx_novelty', 'protein_metadata'],
           where=['tinx_novelty.protein_id = t2tc.protein_id',
                  'protein_metadata.protein_id = t2tc.protein_id'],
           select={'novelty' : 'tinx_novelty.score',
                   'num_important_diseases' : 'protein_metadata.num_important_diseases'})\
    .all()

  serializer_class = TargetSerializer
  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  search_fields = ('^protein__sym', '^target__name')
  filter_class = TargetFilter


class TargetDiseasesViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
  """
  list:
  View the diseases associated with a specific target.

  retrieve:
  Retrieve information about a specific target-disease association.
  """
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
  """
  list:
  View targets associated with a specific disease.

  retrieve:
  Retrieve information about a specific disease-target association.
  """
  pagination_class = RestrictedPagination
  serializer_class = DiseaseTargetSerializer

  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  search_fields = ('^protein__sym', '^target__name')
  filter_class = DiseaseTargetFilter


  def get_queryset(self):
      disease = Disease.objects\
          .prefetch_related('importance_set')\
          .prefetch_related()\
          .filter(id = self.kwargs['disease_id'])  \
          .first()

      return disease._prefetched_objects_cache['importance'] \
          .prefetch_related('protein') \
          .extra(tables=['tinx_novelty', 't2tc', 'target', 'tinx_nds_rank'],
                 where=['tinx_novelty.protein_id = tinx_importance.protein_id',
                        't2tc.protein_id = tinx_importance.protein_id',
                        'target.id = t2tc.target_id',
                        'tinx_nds_rank.tinx_importance_id = tinx_importance.id'],
                 select={'novelty': 'tinx_novelty.score',
                         'target_id': 'target.id',
                         'target_name': 'target.name',
                         'target_fam': 'target.fam',
                         'target_famext' : 'target.famext',
                         'target_tdl' : 'target.tdl',
                         'nds_rank' : 'tinx_nds_rank.rank'})\
          .order_by('nds_rank')


  def retrieve(self, request, *args, **kwargs):
    queryset = self.get_queryset()
    result = get_object_or_404(queryset, protein__id = kwargs['pk'])
    serializer = self.serializer_class(result)
    return Response(serializer.data)


class ArticleViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
  """
  list:
  Browse and search all Pubmed articles in the database.

  retrieve:
  Retrieve information about a specific Pubmed article.
  """
  pagination_class = RestrictedPagination
  serializer_class = PubmedArticleSerializer

  queryset = PubmedArticle.objects.all()

  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  filter_class = PubmedArticleFilter
  search_fields = ('title',)

  def get_queryset(self):
    if 'disease_id' in self.kwargs and 'target_id' in self.kwargs:
      return PubmedArticle.objects\
        .extra(tables=['tinx_articlerank', 'tinx_importance', 't2tc'],
               where=['tinx_articlerank.pmid = pubmed.id',
                      'tinx_importance.id = tinx_articlerank.importance_id',
                      't2tc.protein_id = tinx_importance.protein_id',
                      'tinx_importance.disease_id = %s',
                      't2tc.target_id = %s'],
               params = [self.kwargs['disease_id'], self.kwargs['target_id']])\
        .all()
    else:
      return PubmedArticle.objects.all()


class DTOViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
  """
  list:
  Browse and search all DTO entities in our database.

  retrieve:
  Retrieve information about a specific DTO entity,

  children:
  Retrieve the list of children for a given DTO entity.
  """
  pagination_class = RestrictedPagination
  serializer_class = DTOSerializer
  queryset = DTO.objects.prefetch_related('protein_set').all()

  filter_backends = (filters.SearchFilter, DjangoFilterBackend)
  filter_class = DTOFilter
  search_fields = ('name',)


  @action(detail = True)
  def children(self, request, *args, **kwargs):
    parent = self.get_object()
    queryset = self.get_queryset().filter(parent=parent.id)
    return Response(
      self.serializer_class(queryset, many=True, context={'request': request}).data
    )

