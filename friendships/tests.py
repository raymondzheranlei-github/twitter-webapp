from friendships.models import Friendship
from friendships.services import FriendshipService
from testing_utils.testcases import TestCase


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.ray = self.create_user('ray')
        self.lux = self.create_user('lux')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for to_user in [user1, user2, self.lux]:
            Friendship.objects.create(from_user=self.ray, to_user=to_user)

        user_id_set = FriendshipService.get_following_user_id_set(self.ray.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id, self.lux.id})

        Friendship.objects.filter(from_user=self.ray, to_user=self.lux).delete()
        user_id_set = FriendshipService.get_following_user_id_set(self.ray.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id})