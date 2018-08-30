from rest_framework import serializers

from models import Disease


class DiseaseSerializer(serializers.ModelSerializer):
  # A better name for this field
  novelty = serializers.DecimalField(max_digits=34, decimal_places=16, source='score')

  class Meta:
    model = Disease
    fields = ('id', 'doid', 'name', 'summary', 'novelty')
