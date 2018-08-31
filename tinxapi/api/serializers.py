from rest_framework import serializers
from rest_framework.reverse import reverse

from models import Disease, Target, T2TC, Importance, Protein


class DiseaseSerializer(serializers.ModelSerializer):
  # A better name for this field
  novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  class Meta:
    model = Disease
    fields = ('id', 'doid', 'name', 'summary', 'novelty')


class TargetSerializer(serializers.Serializer):
  id = serializers.IntegerField(source='target_id')
  name = serializers.CharField(source='target.name')
  uniprot = serializers.CharField(source='protein.uniprot')
  sym = serializers.CharField(source='protein.sym')
  fam = serializers.CharField(source='target.fam')
  famext = serializers.CharField(source='target.famext')
  tdl = serializers.CharField(source='target.tdl')
  # TODO: Get this working...
  #  novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source='protein.novelty_set.score')

  diseases = serializers.SerializerMethodField()

  def get_diseases(self, obj):
    return reverse('target-diseases',
                   kwargs={'pk': obj.pk},
                   request=self.context['request'])


class ProteinSerializer(serializers.ModelSerializer):
  class Meta:
    model = Protein
    fields = ('name',)


class TargetDiseaseSerializer(serializers.ModelSerializer):
  disease = DiseaseSerializer()
  importance = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  class Meta:
    model = Importance
    fields = ('disease', 'importance',)

