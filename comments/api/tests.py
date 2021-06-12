from testing_utils.testcases import TestCase
from rest_framework.test import APIClient


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.ray = self.create_user('ray')
        self.ray_client = APIClient()
        self.ray_client.force_authenticate(self.ray)
        self.lux = self.create_user('lux')
        self.lux_client = APIClient()
        self.lux_client.force_authenticate(self.lux)

        self.tweet = self.create_tweet(self.ray)

    def test_create(self):
        # must login before posting comments
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # must have at least one parameter
        response = self.ray_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # only tweet_id is not ok
        response = self.ray_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # only content is not ok
        response = self.ray_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # content cannot be too long
        response = self.ray_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # tweet_id and content must all be transferred
        response = self.ray_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.ray.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')