'''
Tests for Recipe API
'''

from decimal import Decimal
from reprlib import recursive_repr
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

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

    def test_create_recipe_with_new_tags(self):
        '''Creating recipe with new tags'''

        payload = {
            'title': 'Lasagna',
            'time_minutes': 22,
            'price': Decimal('9.45'),
            'description': 'Creamy lasagna',
            'link': 'http://example.com/recipe.pdf',
            'tags': [{'name':'Cream'}, {'name': 'Cheesy'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user = self.user)
        recipe = recipes[0]

        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'], 
                user = self.user
                ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        '''Creating recipe with existing tags'''

        Tag.objects.create(user = self.user, name = 'Pasta')

        payload = {
            'title': 'Lasagna',
            'time_minutes': 22,
            'price': Decimal('9.45'),
            'description': 'Creamy lasagna',
            'link': 'http://example.com/recipe.pdf',
            'tags': [{'name' : 'Pasta'}, {'name':'Garfield'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        all_tags = Tag.objects.all()
        pasta_tag = Tag.objects.filter(name = 'Pasta')
        
        self.assertEqual(len(all_tags), 2)
        self.assertEqual(len(pasta_tag), 1)

    def test_create_tag_on_update(self):
        '''Test creating tag when updating recipe'''

        recipe = create_recipe(user = self.user)

        payload = {
            'title': 'Spicy Chicken Pizza',
            'time_minutes': 42,
            'price': Decimal('9.45'),
            'description': 'A very spicy pizza',
            'link': 'http://example.com/spicy-pizza.pdf',
            'tags': [{'name' : 'Pizza'}, {'name':'Spicy'}],
        }

        url = details_url(recipe.id)

        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user = self.user, name = 'Spicy')

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        '''Test assigning an existing tag when updating recipe'''

        tag_breakfast = Tag.objects.create(user = self.user, name = 'Breakfast')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user = self.user, name = 'Lunch')
        payload = {
            'tags': [
                {
                    'name': 'Lunch',
                }
            ]
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clear_recipe_tags(self):
        '''Test clearing the tags for a recipe'''
        tag = Tag.objects.create(user = self.user, name = 'Fish')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag)

        payload = {
            'tags': []
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)


    def test_create_recipe_with_new_ingredients(self):
        '''Test creating a recipe with new ingredients'''

        payload = {
            'title': 'Cookies',
            'time_minutes': 20,
            'price' : Decimal('43.23'),
            'ingredients' : [{'name': 'Sugar'}, {'name': 'Cookie dough'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        recipes = Recipe.objects.filter(user = self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        '''Test creating a new recipe with existing ingredient'''

        ingredient = Ingredient.objects.create(user = self.user, name = 'Garlic')
        Ingredient.objects.create(user = self.user, name = 'Ginger')

        payload = {
            'title' : 'Stir Fry',
            'time_minutes' : 45,
            'price' : Decimal('34.23'),
            'ingredients' : [{'name' : 'Garlic'}, {'name' : 'Cheese'}]
        }

        res = self.client.post(RECIPES_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        ingredients = Ingredient.objects.filter(user = self.user)
        recipes = Recipe.objects.filter(user = self.user)
        recipe = recipes[0]

        self.assertEqual(ingredients.count(), 3)
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'], 
                user = self.user
                ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        '''Test creating ingredient on update'''

        recipe = create_recipe(user = self.user)
        self.assertEqual(Ingredient.objects.all().count(), 0)
        url = details_url(recipe.id)
        payload = {
            'title' : 'Tasty Oats',
            'time_minutes' : 30,
            'price' : Decimal('32.23'),
            'ingredients' : [{'name' : 'Cilantro'}, {'name' : 'Banana'}],
        }
        
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.filter(user = self.user)

        self.assertEqual(ingredients.count(), 2)
        recipe.refresh_from_db()
        for ingredient in payload['ingredients']:

            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists()

            self.assertTrue(exists)

    def test_update_recipe_assign_ingredient(self):
        '''Test assigning an existing ingredient when updating a recipe'''

        ingredient1 = Ingredient.objects.create(name = 'Tofu', user = self.user)
        ingredient2 = Ingredient.objects.create(name = 'Spices', user = self.user)

        recipe = create_recipe(user = self.user)

        recipe.ingredients.add(ingredient1)

        payload = {'ingredients' : [{'name' : 'Spices'}]}

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format= 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        all_ingredients = Ingredient.objects.all()

        recipe.refresh_from_db()
        self.assertEqual(all_ingredients.count(), 2)
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        '''Test clearing a recipe ingredients list'''
        ingredient = Ingredient.objects.create(user = self.user, name = '')
        recipe = create_recipe(user = self.user)
        self.assertEqual(Ingredient.objects.all().count(), 1)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients' : []
        }

        url = details_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.all().count(), 0)

        
















