from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:

    @classmethod
    def serialize(cls, instance):
        # Django serializers need a QuerySet or list to do serialization
        # so need to add [] to make the instance as a list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        # need to add ".object" to get original object data of the model
        return list(serializers.deserialize('json', serialized_data))[0].object
