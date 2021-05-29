from django.test import TestCase
from django.contrib.auth.models import User
from django.test import TestCase
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now

class TweetTests(TestCase):

    def test_hours_to_now(self):
        ray688 = User.objects.create_user(username='ray688')
        tweet = Tweet.objects.create(user=ray688, content='Today is a good day')
        tweet.created_at = utc_now() - timedelta(hours=5)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 5)

