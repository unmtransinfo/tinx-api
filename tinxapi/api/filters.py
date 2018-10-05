import django_filters
import models

class PubmedArticleFilter(django_filters.FilterSet):
  """
  Filters for the /articles endpoint
  """
  title = django_filters.CharFilter(name='title', lookup_expr='icontains')
  journal = django_filters.CharFilter(name='journal', lookup_expr='icontains')
  author = django_filters.CharFilter(name='authors', lookup_expr='icontains')
  abstract = django_filters.CharFilter(name='abstract', lookup_expr='icontains')

  class Meta:
    model = models.PubmedArticle
    fields = ['title', 'journal', 'author', 'abstract']


class TargetFilter(django_filters.FilterSet):
  """
  Filters for the /targets endpoint
  """
  name = django_filters.CharFilter(name='target__name', lookup_expr='icontains')
  uniprot = django_filters.CharFilter(name='protein__uniprot', lookup_expr='iexact')
  sym = django_filters.CharFilter(name='protein__sym', lookup_expr='iexact')
  fam = django_filters.CharFilter(name='target__fam', lookup_expr='icontains')
  famext = django_filters.CharFilter(name='target__famext', lookup_expr='icontains')
  tdl = django_filters.CharFilter(name='target__tdl', lookup_expr='iexact')

  class Meta:
    model = models.T2TC
    fields = ['name', 'uniprot', 'sym', 'fam', 'famext', 'tdl']


class DiseaseFilter(django_filters.FilterSet):
  """
  Filters for the /diseases endpoing
  """
  doid = django_filters.CharFilter(name='doid', lookup_expr='iexact')

  class Meta:
    model = models.Disease
    fields = ['doid']


