import json, os, requests, sys
from infraxys.communicator import Communicator
from infraxys.exceptions import BaseException
from infraxys.logger import Logger
from .json_window import JsonWindow
from infraxys.model.base_object import BaseObject
from pprint import pprint
from .packets import Packets


class JsonInstance(BaseObject):

    def __str__(self):
        if hasattr(self, 'name'):
            return self.name

        for attribute in self.get_attributes():
            if attribute.isKey:
                return self.__getattribute__(attribute.name)

        return super().__str__()

    def load_instance_form_response(self, server_response):
        form_fields = server_response.get_form_fields()
        self.load_instance_from_name_values(form_fields)

    def load_instance_from_name_values(self, name_values):
        for attribute in self.get_attributes():
            self.__setattr__(attribute.name, name_values[attribute.name])

    def load_instance_from_server(self, server_instance_json):
        self.db_id = server_instance_json["dbId"]
        self.container_db_id = server_instance_json["containerDbId"]
        self.environment_db_id = server_instance_json["environmentDbId"]
        for attribute in self.get_attributes():
            print("Setting {} to {}".format(attribute.name, server_instance_json[attribute.name]), flush=True)
            self.__setattr__(attribute.name, server_instance_json[attribute.name])

    def get_value_from_form_fields(self, attribute_name, form_fields):
        return form_fields[attribute_name]

    def to_json_fields(self):
        json = {}
        for attribute in self.get_attributes():
            value = self.__getattribute__(attribute.name)
            json.update({ attribute.name: value})

        return json

    def __init__(self, db_id=None, container_db_id=None, environment_db_id=None, parent_instance_id=None, audit_json={},
                 packet_type=None):
        super().__init__(db_id=db_id, container_db_id=container_db_id,environment_db_id=environment_db_id,
                         parent_instance_id=parent_instance_id, audit_json=audit_json, packet_type=packet_type)

        self._json_window = None

    def _get_json_window(self):
        if not self._json_window:
            self._json_window = JsonWindow.get_instance()
            css_file = os.getenv("JSON_WINDOW_CSS_FILE")
            if css_file:
                self._json_window.show(css_file="{}/{}".format(os.environ["MODULES_ROOT"], css_file))
            else:
                self._json_window.show()

        return self._json_window

    def show_instance_form_and_ensure(self, parent_instance_id):
        self.parent_instance_id = parent_instance_id

        form = self.form(self)
        form.add_button_click_listener("OK", self.create_new)
        self._get_json_window().set_form(form, auto_close=True)
