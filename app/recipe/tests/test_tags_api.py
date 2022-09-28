'''Tests for the Tags API'''

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URLS = reverse('recipe:tag-list')


def details_url(tag_id):
    '''Create and return a tag detail url'''
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password="pass123456"):
    return get_user_model().objects.create_user(email=email, password=password)


class TagTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retrieving tags'''
        res = self.client.get(TAGS_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITest(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving list of tags'''

        Tag.objects.create(user=self.user, name="Cooking")
        Tag.objects.create(user=self.user, name="Baking")

        res = self.client.get(TAGS_URLS)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test lsit of tags is limited to that user'''

        new_user = create_user(email="tim@example.com")
        Tag.objects.create(user=new_user, name="Bread")
        tag = Tag.objects.create(user=self.user, name="Candy")

        res = self.client.get(TAGS_URLS)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''Test for updating tag.'''

        tag = Tag.objects.create(user=self.user, name='Jelly')
        url = details_url(tag.id)
        payload = {
            'name': 'Jellies'
        }

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(res.data['name'], tag.name)

    def test_delete_tag(self):
        '''Test deleting a tag'''
        Tag.objects.create(user=self.user, name='Spirits')
        Tag.objects.create(user=self.user, name='Wine')
        tag = Tag.objects.create(user=self.user, name='Beer')
        url = details_url(tag.id)
        res = self.client.delete(url)
        other_tags = Tag.objects.filter(user=self.user)
        deleted_tag = Tag.objects.filter(id=tag.id)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(len(Tag.objects.all()), 2)
        self.assertTrue(other_tags.exists())
        self.assertFalse(deleted_tag.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        '''Test listing tags by those assigned to recipes'''

        i1 = Tag.objects.create(user=self.user, name='Spices')
        i2 = Tag.objects.create(user=self.user, name='Seasoning')
        r1 = Recipe.objects.create(
            title='Spice Mix',
            time_minutes=43,
            price=Decimal('0.02'),
            user=self.user
        )
        r1.tags.add(i1)
        res = self.client.get(TAGS_URLS, {'assigned_only': 1})

        s1 = TagSerializer(i1)
        s2 = TagSerializer(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        '''Test filtered tags returns a unique list'''

        i1 = Tag.objects.create(user=self.user, name='Spices')
        Tag.objects.create(user=self.user, name='Seasoning')

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

        r1.tags.add(i1)
        r2.tags.add(i1)
        res = self.client.get(TAGS_URLS, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
