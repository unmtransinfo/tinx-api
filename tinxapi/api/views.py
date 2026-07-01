from api.filters import *
from api.models import *
from api.models import Importance, NDSRank, Novelty
from api.paginators import RestrictedPagination
from api.serializers import *
from django.db import models as django_models
from django.db.models import F, OuterRef, Subquery, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from haystack.inputs import AltParser
from haystack.query import SearchQuerySet
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.


class Search(APIView):

    def get(self, request, format=None):
        diseaseType = request.query_params.get("type") == "disease"
        model = Disease if diseaseType else TinxTarget
        default = (
            SearchQuerySet()
            .filter(
                content=AltParser("edismax", request.query_params.get("q"), df="text")
            )
            .models(model)
        )

        if diseaseType:
            targetGen = [e.get_stored_fields() for e in default]
        else:
            targetGen = [
                e.get_stored_fields() for e in default if e.get_stored_fields()["dtoid"]
            ]
        return Response(targetGen)


class DiseaseViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
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
    filterset_class = DiseaseFilter
    search_fields = ("^name",)
    lookup_field = "doid"

    def get_queryset(self):
        return Disease.objects.all()

    @action(detail=True)
    def children(self, request, *args, **kwargs):
        parent = self.get_object()
        queryset = DoParent.objects.filter(parent_id=parent.doid).all()

        return Response(
            DoParentSerializer(queryset, many=True, context={"request": request}).data
        )

    @action(detail=True)
    def parent(self, request, *args, **kwargs):
        child = self.get_object()
        queryset = DoParent.objects.filter(doid=child.doid).first()

        return Response(
            DoParentSerializer(queryset, many=False, context={"request": request}).data
        )


class TargetViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    list:
    Browse all targets in the database.

    retrieve:
    Get information about a specific target.
    """

    pagination_class = RestrictedPagination
    serializer_class = TargetSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ("^protein__sym", "^target__name")
    filterset_class = TargetFilter
    lookup_field = "target_id"

    def get_queryset(self):
        return T2TC.objects.select_related("target").select_related("protein").all()


class TargetDiseasesViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    list:
    View the diseases associated with a specific target.

    retrieve:
    Retrieve information about a specific target-disease association.
    """

    pagination_class = RestrictedPagination
    serializer_class = TargetDiseaseSerializer
    lookup_field = "doid"

    def get_queryset(self):
        protein = (
            Protein.objects.prefetch_related("importance_set")
            .filter(id=self.kwargs["target_id"])
            .first()
        )
        if protein is None:
            return Importance.objects.none()
        return protein.importance_set.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = get_object_or_404(queryset, disease_id=kwargs["doid"])
        serializer = self.serializer_class(result, context={"request": request})
        return Response(serializer.data)


class DiseaseTargetsViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    list:
    View targets associated with a specific disease.

    retrieve:
    Retrieve information about a specific disease-target association.
    """

    pagination_class = RestrictedPagination
    serializer_class = DiseaseTargetSerializer
    lookup_field = "target_id"

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ("^protein__sym", "^target__name")
    filterset_class = DiseaseTargetFilter

    def get_queryset(self):
        """
        NOTE: This get_queryset() function assumes the following is true on the DB-side (all queries should return empty set):
        mysql> SELECT protein_id, COUNT(*) FROM tinx_novelty GROUP BY protein_id HAVING COUNT(*) > 1;
        Empty set (0.02 sec)
        mysql> SELECT protein_id, doid, COUNT(*) FROM tinx_importance GROUP BY protein_id, doid HAVING COUNT(*) > 1;
        Empty set (6.88 sec)
        mysql> SELECT protein_id, COUNT(*) FROM t2tc GROUP BY protein_id HAVING COUNT(*) > 1;
        Empty set (0.01 sec)

        You should verify this is true if you ever update the tinx database.
        """
        doid = self.kwargs["doid"]

        qs = (
            NDSRank.objects.filter(doid=doid)
            .select_related("protein")
            .annotate(
                nds_rank=F("rank"),
                novelty=Subquery(
                    Novelty.objects.filter(protein=OuterRef("protein")).values("score")
                ),
                score=Subquery(
                    Importance.objects.filter(
                        protein=OuterRef("protein"), disease=doid
                    ).values("score")
                ),
                target_id=Subquery(
                    T2TC.objects.filter(protein=OuterRef("protein")).values(
                        "target__id"
                    )
                ),
                target_name=Subquery(
                    T2TC.objects.filter(protein=OuterRef("protein")).values(
                        "target__name"
                    )
                ),
                target_fam=Subquery(
                    T2TC.objects.filter(protein=OuterRef("protein")).values(
                        "target__fam"
                    )
                ),
                target_famext=Subquery(
                    T2TC.objects.filter(protein=OuterRef("protein")).values(
                        "target__famext"
                    )
                ),
                target_tdl=Subquery(
                    T2TC.objects.filter(protein=OuterRef("protein")).values(
                        "target__tdl"
                    )
                ),
                disease_id=Value(doid, output_field=django_models.CharField()),
            )
            .order_by(
                "rank", "target_id"
            )  # add target_id ordering as tiebreaker for deterministic behavior (nds_rank can have ties)
        )

        return qs

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = get_object_or_404(queryset, protein__id=kwargs["target_id"])
        serializer = self.serializer_class(result, context={"request": request})
        return Response(serializer.data)


class ArticleViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    list:
    Browse and search all Pubmed articles in the database.

    retrieve:
    Retrieve information about a specific Pubmed article.
    """

    pagination_class = RestrictedPagination
    serializer_class = PubmedArticleSerializer

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = PubmedArticleFilter
    search_fields = ("title",)

    def get_queryset(self):
        if "doid" in self.kwargs and "target_id" in self.kwargs:
            queryset = PubmedArticle.objects.extra(
                tables=["tinx_articlerank", "tinx_importance", "t2tc"],
                where=[
                    "tinx_articlerank.pmid = pubmed.id",
                    "tinx_importance.doid = tinx_articlerank.doid",
                    "tinx_importance.protein_id = tinx_articlerank.protein_id",
                    "t2tc.protein_id = tinx_importance.protein_id",
                    "tinx_importance.doid = %s",
                    "t2tc.target_id = %s",
                ],
                params=[self.kwargs["doid"], self.kwargs["target_id"]],
            )
            return queryset.all()
        else:
            return PubmedArticle.objects.all()


class DTOViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
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
    queryset = DTO.objects.prefetch_related("protein_set").all()

    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = DTOFilter
    search_fields = ("name",)

    @action(detail=True)
    def children(self, request, *args, **kwargs):
        parent = self.get_object()
        queryset = self.get_queryset().filter(parent=parent.id)
        return Response(
            self.serializer_class(
                queryset, many=True, context={"request": request}
            ).data
        )
