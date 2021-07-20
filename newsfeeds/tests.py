from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from newsfeeds.tasks import fanout_newsfeeds_main_task
from testing_utils.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.ray = self.create_user('ray')
        self.lux = self.create_user('lux')

    def test_get_user_newsfeeds(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.lux)
            newsfeed = self.create_newsfeed(self.ray, tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

        # cache updated
        tweet = self.create_tweet(self.ray)
        new_newsfeed = self.create_newsfeed(self.ray, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        newsfeed_ids.insert(0, new_newsfeed.id)
        self.assertEqual([f.id for f in newsfeeds], newsfeed_ids)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.ray, self.create_tweet(self.ray))

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.ray.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.ray, self.create_tweet(self.ray))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual([f.id for f in feeds], [feed2.id, feed1.id])


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.ray = self.create_user('ray')
        self.lux = self.create_user('lux')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.ray, 'tweet 1')
        self.create_friendship(self.lux, self.ray)
        msg = fanout_newsfeeds_main_task(tweet.id, self.ray.id)
        self.assertEqual(msg, '1 newsfeeds are going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.ray)
        tweet = self.create_tweet(self.ray, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, self.ray.id)
        self.assertEqual(msg, '3 newsfeeds are going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.ray)
        tweet = self.create_tweet(self.ray, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, self.ray.id)
        self.assertEqual(msg, '4 newsfeeds are going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.ray.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.lux.id)
        self.assertEqual(len(cached_list), 3)
