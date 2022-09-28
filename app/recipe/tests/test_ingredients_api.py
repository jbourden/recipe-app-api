'''
Tests for ingredients API
'''

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def details_url(ingredient_id):
    '''Create and return a ingredient detail url'''
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password="pass123456"):
    return get_user_model().objects.create_user(email=email, password=password)


def create_ingredient(email='user@example.com', name='Ingredient'):
    return Ingredient.objects.create(email=email, name=name)


class PublicIngredientsAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retrieving tags'''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='joshua@example.com',
            password='123456qwerty'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        '''Test retrieving a list of ingredients'''

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Rest list of ingredients is limited to authenticated user.'''

        other_user = create_user(
            email='new@example.com',
            password='123qwerty')

        ingredient = Ingredient.objects.create(user=self.user, name='Sauce')
        Ingredient.objects.create(user=self.user, name='Cheese')
        Ingredient.objects.create(user=other_user, name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        '''Test updating ingredient'''

        ingredient = Ingredient.objects.create(user=self.user, name='Sauce')
        payload = {
            'name': 'Dressing'
        }

        url = details_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        '''Test deleting ingredient'''
        Ingredient.objects.create(user=self.user, name='Salt')
        ingredient = Ingredient.objects.create(user=self.user, name='Sauce')

        self.assertEqual(Ingredient.objects.all().count(), 2)

        url = details_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.all().count(), 1)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        '''Test listing ingredients by those assigned to recipes'''

        i1 = Ingredient.objects.create(user=self.user, name='Salt')
        i2 = Ingredient.objects.create(user=self.user, name='Pepper')
        r1 = Recipe.objects.create(
            title='Spice Mix',
            time_minutes=43,
            price=Decimal('0.02'),
            user=self.user
        )
        r1.ingredients.add(i1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(i1)
        s2 = IngredientSerializer(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        '''Test filtere ingredients returns a unique list'''

        i1 = Ingredient.objects.create(user=self.user, name='Salt')

        r1 = Recipe.objects.create(
            title='Spice Mix',
            time_minutes=43,
            price=Decimal('0.02'),
            user=self.user
        )

        r2 = Recipe.objects.create(
            title='Popcorn Mix',
            time_minutes=23,
            price=Decimal('0.03'),
            user=self.user
        )

        r1.ingredients.add(i1)
        r2.ingredients.add(i1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
