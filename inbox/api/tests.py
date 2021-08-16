from notifications.models import Notification
from testing_utils.testcases import TestCase


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'


class NotificationTests(TestCase):

    def setUp(self):
        super(NotificationTests, self).setUp()
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


class NotificationApiTests(TestCase):

    def setUp(self):
        super(NotificationApiTests, self).setUp()
        self.ray, self.ray_client = self.create_user_and_client('ray')
        self.lux, self.lux_client = self.create_user_and_client('lux')
        self.ray_tweet = self.create_tweet(self.ray)

    def test_unread_count(self):
        # lux likes a ray's tweet
        self.lux_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ray_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.ray_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        # lux commented a ray's tweet
        comment = self.create_comment(self.ray, self.ray_tweet)
        self.lux_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        # ray can see two unread notifications
        response = self.ray_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)
        # lux cannot see any unread notification
        response = self.lux_client.get(url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        self.lux_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ray_tweet.id,
        })
        comment = self.create_comment(self.ray, self.ray_tweet)
        self.lux_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.ray_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        response = self.ray_client.get(mark_url)
        self.assertEqual(response.status_code, 405)

        # lux cannot mark ray's notifications as read
        response = self.lux_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)
        response = self.ray_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        # ray can mark his own notifications as read
        response = self.ray_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.ray_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.lux_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ray_tweet.id,
        })
        comment = self.create_comment(self.ray, self.ray_tweet)
        self.lux_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # unauthenticated user cannot access api
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        # lux cannot see any notifications
        response = self.lux_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # ray can see two notifications
        response = self.ray_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        # one unread after being tagged
        notification = self.ray.notifications.first()
        notification.unread = False
        notification.save()
        response = self.ray_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.ray_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.ray_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)

    def test_update(self):
        self.lux_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.ray_tweet.id,
        })
        comment = self.create_comment(self.ray, self.ray_tweet)
        self.lux_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.ray.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)
        # post is not allowed. only put
        response = self.lux_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        # other users cannot modify notification status
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # queryset is based on current signed in user, so return 404 instead of 403
        response = self.lux_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        # marked as read
        response = self.ray_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.ray_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)

        # mark as unread
        response = self.ray_client.put(url, {'unread': True})
        response = self.ray_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)
        # have to have  unread
        response = self.ray_client.put(url, {'verb': 'newverb'})
        self.assertEqual(response.status_code, 400)
        # cannot modify other information
        response = self.ray_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')
