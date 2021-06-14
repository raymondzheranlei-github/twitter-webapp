from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing_utils.testcases import TestCase

COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'


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

    def test_destroy(self):
        comment = self.create_comment(self.ray, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # Unauthenticated client cannot delete
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Unauthorized user of the object cannot delete
        response = self.lux_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Only owner can delete
        count = Comment.objects.count()
        response = self.ray_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.ray, self.tweet, 'original')
        another_tweet = self.create_tweet(self.lux)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # while using put
        # Unauthenticated client cannot update
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        # Unauthorized user of the object cannot update
        response = self.lux_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')
        # Can only update content. All else updates will be silently processed
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.ray_client.put(url, {
            'content': 'new',
            'user_id': self.lux.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.ray)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)
