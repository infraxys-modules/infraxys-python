import os

from infraxys.logger import Logger
from .json_window import JsonWindow


class JsonResource(object):

    def __init__(self):
        self.json_window = json_window
        self.logger = Logger.get_logger(self.__class__.__name__)

    def _get_json_window(self):
        if not self.json_window:
            self.json_window = JsonWindow.get_instance()
            self.json_window.show(css_file="{}/shared/main.css".format(os.environ['MCKINSEY_CORE_MODULE_ROOT']))

        return self.json_window
