'''
Views for the Recipe API
'''


from symbol import parameters
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import (
    viewsets,
    mixins,
    status,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)
from recipe import serializers

@extend_schema_view(
    list = extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma seperated list of tag IDs to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma seperated list of ingredient IDs to filter'
            )
        ]
    )
)

class RecipeViewSet(viewsets.ModelViewSet):
    ''' View for manage recipe APIs.'''

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        '''Convert a list of strings to integers'''
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in = ingredient_ids)

        return queryset.filter(
            user = self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        '''Return the serializer for request'''
        if self.action == 'list':
            return serializers.RecipeSerializer

        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class
    
    def perform_create(self, serializer):
        '''Create a new recipe'''
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail = True, url_path = 'upload_image')
    def upload_image(self, request, pk = None):
        '''Upload an image to recipe.'''

        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

class BaseRecipeAttrViewset(mixins.UpdateModelMixin, 
                            mixins.ListModelMixin, 
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet,):
    '''Base viewset'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter queryset to authenticated user'''
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        '''Create a new recipe'''
        serializer.save(user=self.request.user) 

class TagViewSet(BaseRecipeAttrViewset):
    '''Manage tags in the database.'''

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

class IngredientViewSet(BaseRecipeAttrViewset):
    
    '''Manage Ingredients in the database.'''

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
