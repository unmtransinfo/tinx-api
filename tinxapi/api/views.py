# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import mixins

from django.http import HttpResponse

from models import Disease
from serializers import DiseaseSerializer
from paginators import RestrictedPagination


class DiseaseViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
  pagination_class = RestrictedPagination

  queryset = Disease.objects.all()
  serializer_class = DiseaseSerializer

