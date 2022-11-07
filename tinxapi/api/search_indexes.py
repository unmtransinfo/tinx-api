from api.models import *
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


class TargetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    tinx_id = indexes.CharField(model_attr='id', faceted=True)
    name = indexes.EdgeNgramField(model_attr='name')
    description = indexes.EdgeNgramField(model_attr='description', null=True)
    ttype = indexes.CharField(model_attr='ttype', null=True)
    tdl = indexes.CharField(model_attr='tdl', null=True)
    fam = indexes.CharField(model_attr='fam', null=True)
    famext = indexes.CharField(model_attr='famext', null=True)


    def get_model(self):
        return Target

    def index_queryset(self, using=None):
        return self.get_model().objects.all()