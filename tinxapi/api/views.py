# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import mixins

from django.http import HttpResponse

from models import Disease, Target, T2TC
from serializers import DiseaseSerializer, TargetSerializer
from paginators import RestrictedPagination


class DiseaseViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  queryset = Disease.objects.all()
  serializer_class = DiseaseSerializer


class TargetViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
  pagination_class = RestrictedPagination
  queryset = T2TC.objects\
    .select_related('target')\
    .select_related('protein')\
    .prefetch_related('protein__novelty_set')\
    .all()

  serializer_class = TargetSerializer

