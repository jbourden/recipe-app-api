'''
Tests for Recipe API
'''

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

def details_url(recipe_id):
    '''Create and return a recipe detail URL.'''
    return reverse("recipe:recipe-detail", args=[recipe_id])

def create_recipe(user, **params):

    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user = user, **defaults)
    return recipe

def create_user(**params):
    ''''Create and return a new user'''
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required to call API'''

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='john@test.com',password='qwerty')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test auth is required to call API'''

        create_recipe(user = self.user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        '''Test auth is required to call API'''

        other_user = create_user(
            email='jane@pain.com',
            password='qwerty'
        )

        create_recipe(user = self.user)
        create_recipe(user = other_user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''Test get recipe detail'''
        recipe = create_recipe(user= self.user)
        url = details_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        '''Test creating a recipe'''

        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        '''Test partial update of a recipe'''

        original_payload = {
            'user': self.user,
            'title':'A new title',
            'time_minutes': 26,
        }

        recipe = create_recipe(**original_payload)

        payload = {
            'title': 'The newer title.',
            'time_minutes': 30,
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.user, original_payload['user'])

    def test_full_update(self):

        recipe = create_recipe(
            user= self.user,
            title= "Banana Bread",
            description = "Nan's classic banana bread",
            price = Decimal("3.09"),
            link = "http://www.example.com/example",
            )

        payload = {
            'title' : "Nan's Best Bread",
            'description' : 'Nans classic BEST banana bread',
            'price' : Decimal('3.10'),
            'time_minutes': 45,
            'link' : "http://www.example.com/banana-bread",
        }

        url = details_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        recipe.refresh_from_db()
        
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        '''Test changing the recipe user results in an error'''
        new_user = create_user(email='123@example.com', password="1233456")
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = details_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        '''Test for deleting recipe.'''

        recipe = create_recipe(user = self.user)
        url = details_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id = recipe.id).exists())
        
    def test_delete_other_users_recipe_error(self):
        '''Test for deleting recipe.'''

        new_user = create_user(
            email = "bob@example.com", 
            password = "123456",
            )
        
        recipe = create_recipe(user = new_user)
        url = details_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id = recipe.id).exists())