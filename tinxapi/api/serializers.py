import collections

from rest_framework import serializers
from rest_framework.reverse import reverse

from api.models import *
from api import views
import urllib




class DiseaseSerializer(serializers.ModelSerializer):
  """
  Serializer for /diseases
  """

  # A better name for this field
  novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  # Populated by get_targets
  targets = serializers.SerializerMethodField()

  children = serializers.SerializerMethodField()

  parent = serializers.SerializerMethodField()


  class Meta:
    model = Disease
    fields = ('id', 'doid', 'name', 'summary', 'novelty', 'targets', 'children', 'parent')

  def get_targets(self, obj):
    """
    Populates the `targets` field above (by name) with a hyperlink to the
    target's diseases (e.g. /diseases/1/targets)

    :param obj: The object being serialized.
    :return: A hyperlink.
    """
    return reverse('disease-targets',
                   kwargs={'disease_id': obj.pk},
                   request=self.context['request'])

  def get_parent(self, obj):
    """
    Populates the `targets` field above (by name) with a hyperlink to the
    target's diseases (e.g. /diseases/1/targets)

    :param obj: The object being serialized.
    :return: A hyperlink.
    """
    return reverse('disease-parent',
                   kwargs={'pk': obj.pk},
                   request=self.context['request'])

  def get_children(self, obj):
    """
    Get a URL to retrieve the children of this disease.
    :param obj:
    :return:
    """
    if 'request' in self.context:
        return reverse('disease-children',
                       kwargs={'pk': obj.pk},
                       request=self.context['request'])


class DiseaseWithMetadataSerializer(DiseaseSerializer):
  """
  Extends DiseaseSerializer to add field from the metadata table, specifically:
  num_important_targets
  """

  num_important_targets = serializers.IntegerField()

  category = serializers.CharField()

  class Meta:
    model = Disease
    fields = ('id', 'doid', 'name', 'category', 'summary', 'num_important_targets', 'novelty', 'targets', 'children', 'parent')



class TargetSerializer(serializers.Serializer):
  """
  Serializer for /targets
  """
  id = serializers.IntegerField(source='target_id')
  name = serializers.CharField(source='target.name')
  uniprot = serializers.CharField(source='protein.uniprot')
  sym = serializers.CharField(source='protein.sym')
  fam = serializers.CharField(source='target.fam')
  famext = serializers.CharField(source='target.famext')
  tdl = serializers.CharField(source='target.tdl')
  dtoid = serializers.CharField(source='protein.dto.id')
  num_important_diseases = serializers.IntegerField()
  novelty = serializers.DecimalField(max_digits=34, decimal_places=16)
  diseases = serializers.SerializerMethodField()

  def get_diseases(self, obj):
    """
    Populates the `diseases` field above (by name) with a hyperlink to the
    target's diseases (e.g. /target/1/diseases)

    :param obj: The object being serialized.
    :return: A hyperlink.
    """
    return reverse('target-diseases',
                   kwargs={'target_id': obj.pk},
                   request=self.context['request'])


class TargetDiseaseSerializer(serializers.ModelSerializer):
  """
  Serializer for the /target/:id/diseases endpoint
  """
  disease = serializers.SerializerMethodField()
  articles = serializers.SerializerMethodField()
  importance = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')
  category = serializers.CharField()

  class Meta:
    model = Importance
    fields = ('disease', 'articles', 'importance', 'category',)

  def get_articles(self, obj):
    if 'request' in self.context:
      return reverse('target-disease-articles',
                     kwargs={'disease_id': obj.disease_id, 'target_id' : obj.protein_id },
                     request=self.context['request'])

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
    obj.disease.category = obj.category
    obj.disease.num_important_targets = obj.num_important_targets
    return DiseaseWithMetadataSerializer(obj.disease, many=False, context=self.context).data


class DiseaseTargetSerializer(serializers.ModelSerializer):
  """
  Serializer results for the /disease/:id/targets endpoint
  """

  target = serializers.SerializerMethodField()
  articles = serializers.SerializerMethodField()
  importance = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')
  nds_rank = serializers.IntegerField()


  class Meta:
    model = Importance
    fields = ('target', 'articles', 'nds_rank', 'importance')

  def get_target(self, obj):
    """
    Populates the value of `target` (matched by name)
    :param obj: The current Importance object.
    :return: An OrderedDict with fields matching results of TargetSerializer
    """
    tmp = collections.OrderedDict()
    tmp['id'] = obj.target_id
    tmp['name'] = obj.target_name
    tmp['uniprot'] = obj.protein.uniprot
    tmp['fam'] = obj.target_fam
    tmp['famext'] = obj.target_famext
    tmp['tdl'] = obj.target_tdl
    tmp['novelty'] = obj.novelty
    tmp['sym'] = obj.protein.sym
    tmp['dtoid'] = obj.protein.dto.id if hasattr(obj.protein, 'dto') else None
    return tmp

  def get_articles(self, obj):
    if 'request' in self.context:
      return reverse('disease-target-articles',
                     kwargs={'disease_id': obj.disease_id, 'target_id' : obj.protein_id },
                     request=self.context['request'])


class PubmedArticleSerializer(serializers.ModelSerializer):
  class Meta:
    model = PubmedArticle
    fields = ('id', 'title', 'journal', 'date', 'authors', 'abstract')

class DTOSerializer(serializers.ModelSerializer):
  target = serializers.SerializerMethodField()
  parent = serializers.SerializerMethodField()
  children = serializers.SerializerMethodField()

  class Meta:
    model = DTO
    fields = ('id', 'name', 'target', 'parent', 'children')

  def get_target(self, obj):
    # TODO: This is not very efficient.
    protein = obj._prefetched_objects_cache['protein'].first()

    if protein is None:
      return None
    else:
      queryset = views.TargetViewSet().get_queryset().filter(protein_id = protein.id)
      return TargetSerializer(queryset, many=True, context=self.context).data

  def get_parent(self, obj):
    if obj.parent is None:
      return None
    else:
      return reverse('dto-detail',
                     kwargs={'pk': obj.parent},
                     request = self.context['request'])

  def get_children(self,obj):
    return reverse('dto-children',
                   kwargs={'pk': obj.id },
                   request = self.context['request'])

