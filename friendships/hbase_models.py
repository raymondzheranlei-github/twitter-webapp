from django_hbase import models


class HBaseFollowing(models.HBaseModel):
    """
    store from_user_id who you are following，row_key is sorted by from_user_id + created_at
    can query：
     - A's following users sorted by followed timestamp
     - users who A followed in certain range of time
     - top K users A followed before/after certain timestamp
    """
    # row key
    from_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    to_user_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followings'
        row_key = ('from_user_id', 'created_at')


class HBaseFollower(models.HBaseModel):
    """
    store to_user_id who are following you，row_key is sorted by to_user_id + created_at
    can query：
     - A's followers sorted by followed timestamp
     - Who followed A in certain range of time
     - Top K users who followed A before/after certain timestamp
    """
    # row key
    to_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    from_user_id = models.IntegerField(column_family='cf')

    class Meta:
        row_key = ('to_user_id', 'created_at')
        table_name = 'twitter_followers'
