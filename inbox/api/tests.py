from notifications.models import Notification
from testing_utils.testcases import TestCase


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'


class NotificationTests(TestCase):

    def setUp(self):
        self.ray, self.ray_client = self.create_user_and_client('ray')
        self.lux, self.lux_client = self.create_user_and_client('lux')
        self.lux_tweet = self.create_tweet(self.lux)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.ray_client.post(COMMENT_URL, {
            'tweet_id': self.lux_tweet.id,
            'content': 'well...',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.ray_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.lux_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)