'''
Serializers for Recipe API
'''

from dataclasses import fields
from core.models import Recipe, Tag
from rest_framework import serializers

class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for Recipes'''
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link',]
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

class TagSerializer(serializers.ModelSerializer):
    '''Serializer for Tags'''
    
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
