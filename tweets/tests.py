from testing_utils.testcases import TestCase
from datetime import timedelta
from utils.time_helpers import utc_now


class TweetTests(TestCase):
    def setUp(self):
        self.ray = self.create_user('ray')
        self.tweet = self.create_tweet(self.ray, content='Today is a good day')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.ray, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.ray, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        lux = self.create_user('lux')
        self.create_like(lux, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)
