from friendships.services import FriendshipService
from rest_framework.test import APIClient
from testing_utils.testcases import TestCase
from utils.paginations import EndlessPagination


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        super(FriendshipApiTests, self).setUp()
        self.ray = self.create_user('ray')
        self.ray_client = APIClient()
        self.ray_client = APIClient()
        self.ray_client.force_authenticate(self.ray)

        self.lux = self.create_user('lux')
        self.lux_client = APIClient()
        self.lux_client.force_authenticate(self.lux)

        # create followings and followers for lux
        for i in range(2):
            follower = self.create_user('lux_follower{}'.format(i))
            self.create_friendship(from_user=follower, to_user=self.lux)
        for i in range(3):
            following = self.create_user('lux_following{}'.format(i))
            self.create_friendship(from_user=self.lux, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.ray.id)

        # login to follow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # use GET to follow
        response = self.lux_client.get(url)
        self.assertEqual(response.status_code, 405)
        # can't follow yourself
        response = self.ray_client.post(url)
        self.assertEqual(response.status_code, 400)
        # follow successfully
        response = self.lux_client.post(url)
        self.assertEqual(response.status_code, 201)
        # repeating follow is muted instead of throwing exceptions
        response = self.lux_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # reverse follow will create new data
        before_count = FriendshipService.get_following_count(self.ray.id)
        response = self.ray_client.post(FOLLOW_URL.format(self.lux.id))
        self.assertEqual(response.status_code, 201)
        after_count = FriendshipService.get_following_count(self.ray.id)
        self.assertEqual(after_count, before_count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.ray.id)

        # log in to unfollow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # can't use get to unfollow others
        response = self.lux_client.get(url)
        self.assertEqual(response.status_code, 405)
        # can't unfollow yourself
        response = self.ray_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow successfully
        self.create_friendship(from_user=self.lux, to_user=self.ray)
        before_count = FriendshipService.get_following_count(self.lux.id)
        response = self.lux_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        after_count = FriendshipService.get_following_count(self.lux.id)
        self.assertEqual(after_count, before_count - 1)
        # If not following, unfollow request will be muted
        before_count = FriendshipService.get_following_count(self.lux.id)
        response = self.lux_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        after_count = FriendshipService.get_following_count(self.lux.id)
        self.assertEqual(before_count, after_count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.lux.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # sort by timestamp
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'lux_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'lux_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            'lux_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.lux.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # sort by timestamp
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'lux_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'lux_follower0',
        )

    def test_followers_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.create_user('ray_follower{}'.format(i))
            friendship = self.create_friendship(from_user=follower, to_user=self.ray)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.lux, to_user=follower)

        url = FOLLOWERS_URL.format(self.ray.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # lux has followed users with even id
        response = self.lux_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.create_user('ray_following{}'.format(i))
            friendship = self.create_friendship(from_user=self.ray, to_user=following)
            friendships.append(friendship)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.lux, to_user=following)

        url = FOLLOWINGS_URL.format(self.ray.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # lux has followed users with even id
        response = self.lux_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # ray has followed all his following users
        response = self.ray_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.ray_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.create_user('big_v{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(self.create_friendship(from_user=self.ray, to_user=friend))
        response = self.ray_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], reversed(new_friendships)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # friendship is in ascending order, results is in descending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)
