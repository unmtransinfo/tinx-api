from api.models import *
from api.serializers import *
from haystack import indexes


class DiseaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    doid = indexes.CharField(model_attr='doid', faceted=True)
    name = indexes.EdgeNgramField(model_attr='name')
    summary = indexes.EdgeNgramField(model_attr='summary')

    def get_model(self):
        return Disease

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class TinxTargetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    tinx_id = indexes.CharField()
    target = indexes.CharField(model_attr='target')
    protein = indexes.CharField(model_attr='protein')
    name = indexes.CharField()
    dtoid = indexes.CharField()
    uniprot = indexes.CharField(model_attr='uniprot', null=True)
    sym = indexes.CharField(model_attr='sym', null=True)
    tdl = indexes.CharField(model_attr='tdl', null=True)
    fam = indexes.CharField(model_attr='fam', null=True)
    family = indexes.CharField(model_attr='family', null=True)

    def get_model(self):
        return TinxTarget

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_name(self, obj):
        return Target.objects.filter(id=obj.target_id).first().name

    def prepare_dtoid(self, obj):
        try:
            return Protein.objects.filter(id=obj.protein_id).first().dto_id.replace('_', ':')
        except Exception as e:
            return None

    def prepare_tinx_id(self, obj):
        return obj.target_id

