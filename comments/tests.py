from testing_utils.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        super(CommentModelTests, self).setUp()
        self.ray = self.create_user('ray')
        self.tweet = self.create_tweet(self.ray)
        self.comment = self.create_comment(self.ray, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.ray, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.ray, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        lux = self.create_user('lux')
        self.create_like(lux, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)