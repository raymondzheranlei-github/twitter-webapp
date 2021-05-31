from newsfeeds.models import NewsFeed
from friendships.models import Friendship
from rest_framework.test import APIClient
from testing_utils.testcases import TestCase


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.ray = self.create_user('ray')
        self.ray_client = APIClient()
        self.ray_client.force_authenticate(self.ray)

        self.diana = self.create_user('diana')
        self.diana_client = APIClient()
        self.diana_client.force_authenticate(self.diana)

    def test_list(self):
        # need to login
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # cannot use post
        response = self.ray_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # newsfeeds display nothing at the beginning
        response = self.ray_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # user can see his own tweets
        self.ray_client.post(POST_TWEETS_URL, {'content': 'Hello World'})
        response = self.ray_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # user can see the following's tweets
        self.ray_client.post(FOLLOW_URL.format(self.diana.id))
        response = self.diana_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter',
        })
        posted_tweet_id = response.data['id']
        response = self.ray_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)