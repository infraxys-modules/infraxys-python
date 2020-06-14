import os, sys
from infraxys.logger import Logger
from infraxys.communicator import Communicator
from infraxys.json.packets import Packets


class BaseObject(object):

    def __init__(self, rest_client=None, db_id=None, parent_instance_reference=None, container_db_id=None, environment_db_id=None, parent_instance_id=None, audit_json={},
                 packet_type=None, parent_instance_guid=None):
        self.audit_json = audit_json
        self.rest_client = rest_client
        self.db_id = db_id
        self.parent_instance_reference = parent_instance_reference
        self.container_db_id = container_db_id
        self.environment_db_id = environment_db_id
        self.parent_instance_id = parent_instance_id
        self.parent_instance_guid = parent_instance_guid
        self._packet = None
        self.audit_json = audit_json
        self.packet_type = packet_type
        self.logger = Logger.get_logger(self.__class__.__name__)

        if not self.packet_type and not 'packet_guid' in self.__class__.__dict__:
            self.logger.error(
                "Static variable 'packet_guid' should be defined or constructor argument 'packet_type' should be passed in classes that inherit BaseObject.")
            sys.exit(1)

    def get_parent_instance_guid(self):
        return self.parent_instance_guid

    def set_parent_instance_guid(self, parent_instance_guid):
        self.parent_instance_guid = parent_instance_guid

    def set_status(self, message):
        Communicator.set_status(message)

    def from_environment(self):
        for attribute in self.get_attributes():
            self.__setattr__(attribute.name, os.getenv(attribute.name, ""))

        self._loaded()
        return self

    def _loaded(self):
        pass # override this method if you need to calculate variables after all values are set

    def get_packet(self):
        if not self._packet:
            if self.packet_type:
                self._packet = Packets.get_instance().get_packet(packet_type=self.packet_type)
            else:
                self._packet = Packets.get_instance().get_packet(guid=self.packet_guid)

        return self._packet

    def get_attributes(self):
        return self.get_packet().get_attributes()

    def audit_action_start(self, label):
        self.logger.audit_action_start(label=label, audit_json=self.audit_json)

    def audit_action_complete(self, label):
        self.logger.audit_action_complete(label=label, audit_json=self.audit_json)

    def audit_action(self, label, status=None):
        self.logger.audit_action(label=label, status=status, audit_json=self.audit_json)

    def get_from_db_by_velocity_name(self, velocity_name, container_id=None, environment_id=None):
        assert container_id or environment_id
        json = {
            "requestType": "GET INSTANCE",
            "velocityName": velocity_name
        }

        if container_id:
            json.update({"containerId": container_id})
        else:
            json.update({"environmentId": environment_id})

        answer = Communicator.get_instance().send_synchronous(json=json)
        print(answer, flush=True)
        self.load_instance_from_server(answer)

    def ensure_instance(self, compile_container=False, compile_instance=False, compile_environment=False):
        json = {
            "requestType": "ENSURE INSTANCE",
            "packetGuid": self.packet_guid,
            "parentInstanceId": self.parent_instance_id,
            "compileInstance": compile_instance,
            "compileContainer": compile_container,
            "compileEnvironment": compile_environment,
            "fields": self.to_json_fields()
        }
        answer = Communicator.get_instance().send_synchronous(json=json)
        self.instance_id = answer["dbId"]
        return answer

    def update_instance(self, compile_container=False, compile_instance=False, compile_environment=False):
        assert self.db_id
        json = {
            "requestType": "UPDATE INSTANCE",
            "dbId": self.db_id,
            "compileInstance": compile_instance,
            "compileContainer": compile_container,
            "compileEnvironment": compile_environment,
            "fields": self.to_json_fields()
        }
        answer = Communicator.get_instance().send_synchronous(json=json)
        return answer

    def execute_pipeline(self, pipeline_type="INSTALL", scope="ENVIRONMENT"):
        assert self.db_id
        assert scope == "ENVIRONMENT" or scope == "CONTAINER"
        json = {
            "requestType": "EXECUTE PIPELINE",
            "pipelineType": "INSTALL"
        }

        if scope == "CONTAINER":
            json.update({"containerId": self.container_db_id})
        else:
            json.update({"environmentId": self.environment_db_id})

        answer = self._execute_action(label="Executing {} {} pipeline for {}".format(scope, pipeline_type, self.__str__()),
                                      json=json)
        return answer

    def execute_action(self, filename, instance_id=None, label=None):
        raise Exception("Use REST-API to execute actions.")
        if instance_id == None:
            if self.instance_id == None:
                raise BaseException(
                    "instance_id should be passed to execute_action if it wasn't set during instance creation.")
        else:
            self.instance_id = instance_id

        json = {
            "requestType": "EXECUTE ACTION",
            "instanceId": self.instance_id,
            "filename": filename
        }

        if not label:
            label = "Executing action '{}' on '{}'".format(filename, self.__str__())

        answer = self._execute_action(label=label,
                                      json=json)
        return answer

    def _execute_action(self, label, json):
        self.set_status(label)
        self.logger.audit(label)
        answer = Communicator.get_instance().send_synchronous(json=json, return_on_first_answer=False)
        if answer:
            print("Answer: {}.".format(answer), flush=True)

        self.set_status("Finished: {}".format(label))
        return answer

    def create_new(self, server_response):
        self.logger.debug("Creating new.")
        self.load_instance_form_response(server_response)
        self.ensure_instance(compile_instance=True)
