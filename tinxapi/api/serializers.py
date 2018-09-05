import collections

from rest_framework import serializers
from rest_framework.reverse import reverse

from models import Disease, Target, T2TC, Importance, Protein


class DiseaseSerializer(serializers.ModelSerializer):
  """
  Serializer for /diseases
  """

  # A better name for this field
  novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  # Populated by get_targets
  targets = serializers.SerializerMethodField()

  class Meta:
    model = Disease
    fields = ('id', 'doid', 'name', 'summary', 'novelty', 'targets')

  def get_targets(self, obj):
    """
    Populates the `targets` field above (by name) with a hyperlink to the
    target's diseases (e.g. /diseases/1/targets)

    :param obj: The object being serialized.
    :return: A hyperlink.
    """
    if 'request' in self.context:
      return reverse('disease-targets',
                     kwargs={'pk': obj.pk},
                     request=self.context['request'])
    else:
      return None


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
                   kwargs={'pk': obj.pk},
                   request=self.context['request'])


class TargetDiseaseSerializer(serializers.ModelSerializer):
  """
  Serializer for the /target/:id/diseases endpoint
  """

  disease = DiseaseSerializer()
  importance = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  class Meta:
    model = Importance
    fields = ('disease', 'importance',)


class DiseaseTargetSerializer(serializers.ModelSerializer):
  """
  Serializer results for the /disease/:id/targets endpoint
  """

  target = serializers.SerializerMethodField()
  importance = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  class Meta:
    model = Importance
    fields = ('protein', 'target', 'importance')

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
    return tmp

