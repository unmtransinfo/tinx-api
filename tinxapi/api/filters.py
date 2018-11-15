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
  in_dto = django_filters.BooleanFilter(field_name="protein__dto", method="filter_in_dto")

  class Meta:
    model = models.T2TC
    fields = ['name', 'uniprot', 'sym', 'fam', 'famext', 'tdl', 'in_dto']

  def filter_in_dto(self, queryset, name, value):
    return queryset.filter(protein__dto__isnull = not value)

class DiseaseTargetFilter(django_filters.FilterSet):
  """
  Filters for the /disease/:diseaseId/targets endpoint
  """
  uniprot = django_filters.CharFilter(name='protein__uniprot', lookup_expr='iexact')
  sym = django_filters.CharFilter(name='protein__sym', lookup_expr='iexact')
  in_dto = django_filters.BooleanFilter(field_name="protein__dto", method="filter_in_dto")

  class Meta:
    model = models.Importance
    fields = ['uniprot', 'sym', 'in_dto']

  def filter_in_dto(self, queryset, name, value):
    return queryset.filter(protein__dto__isnull = not value)


class DiseaseFilter(django_filters.FilterSet):
  """
  Filters for the /diseases endpoing
  """
  doid = django_filters.CharFilter(name='doid', lookup_expr='iexact')

  class Meta:
    model = models.Disease
    fields = ['doid']

class DTOFilter(django_filters.FilterSet):
  """
  Filters for the /dto endpoint.
  """
  has_parent = django_filters.BooleanFilter(field_name="parent", method="filter_notnull")


  def filter_notnull(self, queryset, name, value):
    """
    A "not null" filter that returns rows for which the specified field is NULL
    if value is false, and rows for which the specificed field is NOT NULL if
    value is true.

    :param queryset: The queryset to filter.
    :param name: The name of the field to filter on.
    :param value: True (return rows where the field is not null) or false (where field is null).
    :return: A filtered queryset.
    """
    lookup = '__'.join([name, 'isnull'])
    return queryset.filter(**{lookup: not value})


  class Meta:
    model = models.DTO
    fields = ['has_parent']

