from friendships.models import Friendship
from rest_framework.test import APIClient
from testing_utils.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'

class FriendshipApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.ray = self.create_user('ray')
        self.ray_client = APIClient()
        self.ray_client.force_authenticate(self.ray)

        self.diana = self.create_user('diana')
        self.diana_client = APIClient()
        self.diana_client.force_authenticate(self.diana)

        # create followings and followers for diana
        for i in range(2):
            follower = self.create_user('diana_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.diana)
        for i in range(3):
            following = self.create_user('diana_following{}'.format(i))
            Friendship.objects.create(from_user=self.diana, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.ray.id)

        # Need to login before following other users
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # The request method of following cannot be get
        response = self.diana_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot follow yourself
        response = self.ray_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow successfully
        response = self.diana_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual('created_at' in response.data, True)
        self.assertEqual('user' in response.data, True)
        self.assertEqual(response.data['user']['id'], self.ray.id)
        self.assertEqual(response.data['user']['username'], self.ray.username)
        # raise 400 if there are duplicate follow requests
        response = self.diana_client.post(url)
        self.assertEqual(response.status_code, 400)
        # reverse follow relation will generate new data
        count = Friendship.objects.count()
        response = self.ray_client.post(FOLLOW_URL.format(self.diana.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.ray.id)

        # need to login before unfollowing others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # cannot use get method to make unfollow request
        response = self.diana_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow yourself
        response = self.ray_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow successfully
        Friendship.objects.create(from_user=self.diana, to_user=self.ray)
        count = Friendship.objects.count()
        response = self.diana_client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)
        # mute the unfollow requests if not followed originally
        count = Friendship.objects.count()
        response = self.diana_client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.diana.id)
        # post is not allowed for following action
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)
        # make sure sorted by time from latest to oldest
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'diana_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'diana_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'diana_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.diana.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)
        # make sure sorted by time from latest to oldest
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'diana_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'diana_follower0',
        )