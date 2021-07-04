from accounts.models import UserProfile
from testing_utils.testcases import TestCase


class UserProfileTests(TestCase):

    def SetUp(self):
        self.clear_cache()

    def test_profile_property(self):
        ray = self.create_user('ray')
        self.assertEqual(UserProfile.objects.count(), 0)
        p = ray.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)
