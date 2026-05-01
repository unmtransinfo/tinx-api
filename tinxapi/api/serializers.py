import collections

from api.models import *
from rest_framework import serializers
from rest_framework.reverse import reverse


class DoParentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = DoParent
        fields = ("doid", "parent_id", "name")

    def get_name(self, obj):
        disease = Disease.objects.filter(doid=obj.doid).first()
        if not disease:
            return
        return disease.name


class DiseaseSerializer(serializers.ModelSerializer):
    """
    Serializer for /diseases
    """

    # A better name for this field
    novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source="score")

    # Populated by get_targets
    targets = serializers.SerializerMethodField()

    children = serializers.SerializerMethodField()

    parent = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = (
            "id",
            "doid",
            "name",
            "summary",
            "novelty",
            "targets",
            "children",
            "parent",
        )

    def get_targets(self, obj):
        """
        Populates the `targets` field above (by name) with a hyperlink to the
        target's diseases (e.g. /diseases/1/targets)

        :param obj: The object being serialized.
        :return: A hyperlink.
        """
        metadata = DiseaseMetadata.objects.filter(doid=obj.pk).first()
        if not metadata:
            return None
        return reverse(
            "disease-targets",
            kwargs={"disease_id": metadata.pk},
            request=self.context["request"],
        )

    def get_parent(self, obj):
        """
        Populates the `parent` field above (by name) with a hyperlink to the
        target's parent (e.g. /diseases/1/parent)

        :param obj: The object being serialized.
        :return: A hyperlink.
        """
        return reverse(
            "disease-parent", kwargs={"pk": obj.pk}, request=self.context["request"]
        )

    def get_children(self, obj):
        """
        Populates the `children` field above (by name) with a hyperlink to the
        target's parent (e.g. /diseases/1/children)

        :param obj:
        :return:
        """
        if "request" in self.context:
            return reverse(
                "disease-children",
                kwargs={"pk": obj.pk},
                request=self.context["request"],
            )


class DiseaseWithMetadataSerializer(DiseaseSerializer):
    """
    Extends DiseaseSerializer to add field from the metadata table, specifically:
    num_important_targets
    """

    doid = serializers.CharField()
    name = serializers.CharField()
    summary = serializers.CharField()
    num_important_targets = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = (
            "doid",
            "name",
            "category",
            "summary",
            "num_important_targets",
            "novelty",
            "targets",
            "children",
            "parent",
        )

    def get_num_important_targets(self, obj):
        metadata = DiseaseMetadata.objects.filter(doid=obj.doid).first()
        return metadata.num_important_targets if metadata else 0

    def get_category(self, obj):
        metadata = DiseaseMetadata.objects.filter(doid=obj.doid).first()
        return metadata.category if metadata and metadata.category else obj.name


class TargetSerializer(serializers.Serializer):
    """
    Serializer for /targets
    """

    id = serializers.IntegerField(source="target_id")
    name = serializers.CharField(source="target.name")
    uniprot = serializers.CharField(source="protein.uniprot")
    sym = serializers.CharField(source="protein.sym")
    fam = serializers.CharField(source="target.fam")
    famext = serializers.CharField(source="target.famext")
    tdl = serializers.CharField(source="target.tdl")
    dtoid = serializers.SerializerMethodField()
    num_important_diseases = serializers.SerializerMethodField()
    novelty = serializers.SerializerMethodField()
    diseases = serializers.SerializerMethodField()

    class Meta:
        model = Target
        fields = (
            "id",
            "name",
            "uniprot",
            "sym",
            "fam",
            "famext",
            "tdl",
            "dtoid",
            "num_important_diseases",
            "novelty",
            "diseases",
        )

    def get_novelty(self, obj):
        nov = Novelty.objects.filter(protein=obj.protein.id).first()
        return nov.score if nov else None

    def get_num_important_diseases(self, obj):
        number = ProteinMetadata.objects.filter(protein_id=obj.protein.id).first()
        return number.num_important_diseases if number else None

    def get_dtoid(self, obj):
        try:
            return obj._protein_cache.dto_id.replace("_", ":")
        except Exception as e:
            return None

    def get_diseases(self, obj):
        """
        Populates the `diseases` field above (by name) with a hyperlink to the
        target's diseases (e.g. /target/1/diseases)

        :param obj: The object being serialized.
        :return: A hyperlink.
        """
        return reverse(
            "target-diseases",
            kwargs={"target_id": obj.pk},
            request=self.context["request"],
        )


class TargetDiseaseSerializer(serializers.ModelSerializer):
    """
    Serializer for the /target/:id/diseases endpoint
    """

    disease = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    importance = serializers.DecimalField(
        max_digits=34, decimal_places=16, source="score"
    )
    category = serializers.SerializerMethodField()

    class Meta:
        model = Importance
        fields = (
            "disease",
            "articles",
            "importance",
            "category",
        )

    def get_category(self, obj):
        return DiseaseWithMetadataSerializer(
            obj.disease, many=False, context=self.context
        ).data["category"]

    def get_articles(self, obj):
        if "request" in self.context:
            metadata = DiseaseMetadata.objects.filter(doid=obj.disease_id).first()
            if not metadata:
                return None
            return reverse(
                "target-disease-articles",
                kwargs={"disease_id": metadata.id, "target_id": obj.protein_id},
                request=self.context["request"],
            )

    def get_disease(self, obj):
        """
        Serializes the disease property of this Target-Disease association. The
        Disease model does not have all properties that are necessary to use the
        DiseaseWithMetadataSerializer. Instead, these properties (such as category
        and num_important_targets) are retrieved as part of the base query (they
        are properties of obj instead of obj.disease). This function moves those
        properties into obj.disease and then serializes it.

        function
        :param obj:
        :return:
        """
        return DiseaseWithMetadataSerializer(
            obj.disease, many=False, context=self.context
        ).data


class DiseaseTargetSerializer(serializers.ModelSerializer):
    """
    Serializer results for the /disease/:id/targets endpoint
    """

    target = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    importance = serializers.DecimalField(
        max_digits=34, decimal_places=16, source="score"
    )
    nds_rank = serializers.IntegerField()

    class Meta:
        model = Importance
        fields = ("target", "articles", "nds_rank", "importance")

    def get_target(self, obj):
        """
        Populates the value of `target` (matched by name)
        :param obj: The current Importance object.
        :return: An OrderedDict with fields matching results of TargetSerializer
        """

        tmp = collections.OrderedDict()
        tmp["id"] = obj.target_id
        tmp["name"] = obj.target_name
        tmp["uniprot"] = obj.protein.uniprot
        tmp["fam"] = obj.target_fam
        tmp["famext"] = obj.target_famext
        tmp["tdl"] = obj.target_tdl
        tmp["novelty"] = obj.novelty
        tmp["sym"] = obj.protein.sym
        tmp["dtoid"] = obj.protein.dto_id if hasattr(obj.protein, "dto_id") else None
        return tmp

    def get_articles(self, obj):
        if "request" in self.context:
            metadata = DiseaseMetadata.objects.filter(doid=obj.disease_id).first()
            if not metadata:
                return None
            return reverse(
                "disease-target-articles",
                kwargs={"disease_id": metadata.id, "target_id": obj.protein_id},
                request=self.context["request"],
            )


class PubmedArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PubmedArticle
        fields = ("id", "title", "journal", "date", "authors", "abstract")


class DTOSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = DTO
        fields = ("id", "name", "target", "parent", "children")

    def get_target(self, obj):
        # TODO: This is not very efficient.
        # Database values need to be changed for this to work, currently protein uses `_` not `:` as a seperator
        # protein = obj._prefetched_objects_cache['protein'].first()

        # TODO: Seems there aren't any connections between Protein and DTO tables
        protein = Protein.objects.filter(dto=obj.id.replace(":", "_")).first()

        if protein is None:
            return None
        else:
            from api import views

            queryset = (
                views.TargetViewSet().get_queryset().filter(protein_id=protein.id)
            )
            return TargetSerializer(queryset, many=True, context=self.context).data

    def get_parent(self, obj):
        if obj.parent is None:
            return None
        else:
            return reverse(
                "dto-detail", kwargs={"pk": obj.parent}, request=self.context["request"]
            )

    def get_children(self, obj):
        return reverse(
            "dto-children", kwargs={"pk": obj.id}, request=self.context["request"]
        )
