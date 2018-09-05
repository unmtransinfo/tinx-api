# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework import mixins

from django.http import HttpResponse

from models import Disease, Target, T2TC, Importance, Protein
from serializers import *
from paginators import RestrictedPagination


class DiseaseViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  serializer_class = DiseaseSerializer

  def get_queryset(self):
    parent_id = self.request.query_params.get('parent', None)
    parent = Disease.objects.filter(id=parent_id).first()
    if parent_id is None:
      return Disease.objects.all()
    else:
      return Disease.objects.extra(tables=['do_parent'],
                                   where=['do_parent.doid = tinx_disease.doid',
                                          'do_parent.parent=%s'],
                                   params=[parent.doid],
                                   select={'parent_id': 'do_parent.parent'}).all()



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

# TODO: Get pagination working. Probably needs to become a ListAPIView??
class TargetDiseasesView(generics.GenericAPIView):
  pagination_class = RestrictedPagination
  queryset = Protein.objects.prefetch_related('importance_set').prefetch_related().all()

  def get(self, request, *args, **kwargs):
    protein = self.get_object()
    importance = protein._prefetched_objects_cache['importance']
    serializer = TargetDiseaseSerializer(importance.all(), many=True)
    return Response(serializer.data)


class DiseaseTargetsView(generics.GenericAPIView):
  pagination_class = RestrictedPagination

  queryset = Disease.objects.prefetch_related('importance_set').prefetch_related().all()

  def get(self, request, *args, **kwards):
    disease = self.get_object()
    importance = disease._prefetched_objects_cache['importance'] \
      .prefetch_related('protein')\
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
    serializer = DiseaseTargetSerializer(importance.all(), many=True)
    return Response(serializer.data)

