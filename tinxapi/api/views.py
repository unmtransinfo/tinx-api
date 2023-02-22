# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.shortcuts import render
from django.db.migrations.recorder import MigrationRecorder

# Create your views here.

from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework import mixins
from rest_framework import filters
from rest_framework.decorators import action

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models.query import Prefetch
from rest_framework_filters.backends import DjangoFilterBackend

from api.models import *
from api.serializers import *
from api.filters import *
from api.paginators import RestrictedPagination
from haystack.query import SearchQuerySet
from haystack.inputs import AltParser

from rest_framework.views import APIView
from rest_framework.response import Response


class Search(APIView):

    def get(self, request, format=None):
        diseaseType = request.query_params.get('type') == 'disease'
        model = Disease if diseaseType else TinxTarget
        default = SearchQuerySet().filter(
            content=AltParser('edismax', request.query_params.get('q'), df="text")
        ).models(model)

        if diseaseType:
            targetGen = [e.get_stored_fields() for e in default]
        else:
            targetGen = [e.get_stored_fields() for e in default if e.get_stored_fields()['dtoid']]
        return Response(targetGen)


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

    pagination_class = RestrictedPagination
    serializer_class = DiseaseWithMetadataSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filter_class = DiseaseFilter
    search_fields = ('^name',)

    def get_queryset(self):
        return Disease.objects.prefetch_related(
            'diseasemetadata_set'
        ).all()

    @action(detail=True)
    def children(self, request, *args, **kwargs):
        parent = self.get_object()
        queryset = DoParent.objects.filter(parent_id=parent.doid).all()

        return Response(DoParentSerializer(queryset, many=True, context={'request': request}).data)

    @action(detail=True)
    def parent(self, request, *args, **kwargs):
        child = self.get_object()
        queryset = DoParent.objects.filter(doid=child.doid).first()

        return Response(DoParentSerializer(queryset, many=False, context={'request': request}).data)


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
    serializer_class = TargetSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ('^protein__sym', '^target__name')
    filter_class = TargetFilter

    def get_queryset(self):
        return T2TC.objects \
            .select_related('target') \
            .select_related('protein') \
            .all()

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
            .filter(id=self.kwargs['target_id']) \
            .first()
        return protein._prefetched_objects_cache['importance'].all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = get_object_or_404(queryset, disease__id=kwargs['pk'])
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
        limit = int(self.request.query_params.get('limit')) or self.pagination_class.max_limit

        doid = DiseaseMetadata.objects \
            .filter(id=self.kwargs['disease_id']).first().tinx_disease_id

        query = """
            SELECT (tinx_novelty.score) AS novelty,
                   (target.id)          AS target_id,
                   (target.name)        AS target_name,
                   (target.fam)         AS target_fam,
                   (target.famext)      AS target_famext,
                   (target.tdl)         AS target_tdl,
                   (tinx_nds_rank.rank) AS nds_rank,
                   tinx_importance.protein_id,
                   tinx_importance.doid,
                   tinx_importance.score,
                   protein.id,
                   protein.name,
                   protein.description,
                   protein.uniprot,
                   protein.up_version,
                   protein.geneid,
                   protein.sym,
                   protein.family,
                   protein.dtoid,
                   tinx_disease.doid,
                   tinx_disease.name,
                   tinx_disease.summary,
                   tinx_disease.score
            FROM
                tinx_nds_rank
                INNER JOIN protein ON (tinx_nds_rank.protein_id = protein.id)
                join tinx_importance on tinx_nds_rank.doid = tinx_importance.doid
                INNER JOIN tinx_disease ON tinx_disease.doid = tinx_nds_rank.doid
                join t2tc on t2tc.protein_id = tinx_nds_rank.protein_id
                join tinx_novelty on tinx_novelty.protein_id = tinx_nds_rank.protein_id
                join target on t2tc.target_id = target.id
            WHERE tinx_nds_rank.doid = "{0}"
            ORDER BY nds_rank
            LIMIT {1};
        """.format(doid, limit)

        ndsRanks = Importance.objects.raw(query)

        class RawWrapper:
            def __init__(self, rawqueryset, model):
                self.rawQuerySet = rawqueryset
                self.model = model

            def all(self):
                return [i for i in self.rawQuerySet]

        qs = RawWrapper(ndsRanks, Importance)
        
        return qs

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = get_object_or_404(queryset, protein__id=kwargs['pk'])
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

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filter_class = PubmedArticleFilter
    search_fields = ('title',)

    def get_queryset(self):
        if 'disease_id' in self.kwargs and 'target_id' in self.kwargs:
            return PubmedArticle.objects \
                .extra(tables=['tinx_articlerank', 'tinx_importance', 't2tc'],
                       where=['tinx_articlerank.pmid = pubmed.id',
                              'tinx_importance.doid = tinx_articlerank.doid',
                              't2tc.protein_id = tinx_importance.protein_id',
                              'tinx_importance.doid = %s',
                              't2tc.target_id = %s'],
                       params=[self.kwargs['disease_id'], self.kwargs['target_id']]) \
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

    @action(detail=True)
    def children(self, request, *args, **kwargs):
        parent = self.get_object()
        queryset = self.get_queryset().filter(parent=parent.id)
        return Response(
            self.serializer_class(queryset, many=True, context={'request': request}).data
        )
