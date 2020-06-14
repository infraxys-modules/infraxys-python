from infraxys.logger import Logger
from infraxys.infraxys_rest_client import InfraxysRestClient

class BaseService(object):

    def __init__(self):
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.infraxys_rest_client = InfraxysRestClient()

    def save(self, instance):
        assert instance.get_parent_instance_guid()
        self.infraxys_rest_client.ensure_instance(instance=instance)

