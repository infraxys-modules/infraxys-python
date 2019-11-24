import json

from infraxys.logger import Logger


class JsonUtils(object):

    instance = None

    def __init__(self):
        self.logger = Logger.get_logger(self.__class__.__name__)

    def load_from_file(self, filename):
        self.logger.info("Loading json from file {}.".format(filename))
        with open(filename, "r") as file:
            return json.load(file)

    @staticmethod
    def get_instance():
        if not JsonUtils.instance:
            JsonUtils.instance = JsonUtils()

        return JsonUtils.instance
