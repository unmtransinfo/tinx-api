# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework import mixins

from django.http import HttpResponse

from models import Disease, Target, T2TC, Importance, Protein
from serializers import DiseaseSerializer, TargetSerializer, TargetDiseaseSerializer
from paginators import RestrictedPagination


class DiseaseViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  queryset = Disease.objects.all()
  serializer_class = DiseaseSerializer


class TargetViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  queryset = T2TC.objects\
    .select_related('target')\
    .select_related('protein')\
    .prefetch_related('protein__novelty_set')\
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

