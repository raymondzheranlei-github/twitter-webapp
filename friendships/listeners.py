def friendship_changed(sender, instance, **kwargs):
    # importing in the method to prevent circular dependency
    from friendships.services import FriendshipService
    FriendshipService.invalidate_following_cache(instance.from_user_id)
