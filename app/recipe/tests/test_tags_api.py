'''Tests for the Tags API'''

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URLS = reverse('recipe:tag-list')

def details_url(tag_id):
    '''Create and return a tag detail url'''
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@example.com', password = "pass123456"):
    return get_user_model().objects.create_user(email = email, password = password)

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

        Tag.objects.create(user = self.user, name = "Cooking")
        Tag.objects.create(user = self.user, name = "Baking")
        
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

        tag = Tag.objects.create(user = self.user, name = 'Jelly')
        url = details_url(tag.id)
        payload = {
            'name' : 'Jellies'
        }

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(res.data['name'], tag.name)




   

