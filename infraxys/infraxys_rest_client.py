import json

import requests

from infraxys.json.json_utils import JsonUtils
from infraxys.logger import Logger
from .exceptions import BadRequestException, UnauthorizedException, NotFoundException
from .json import json_instance


class InfraxysRestClient(object):
    logger = Logger.get_logger("InfraxysRestClient")
    _instances = {}

    @staticmethod
    def get_instance(infraxys_config_variable):
        if not infraxys_config_variable in InfraxysRestClient._instances:
            filename = f"/tmp/infraxys/variables/INFRAXYS-CONFIG/{infraxys_config_variable}"
            InfraxysRestClient.logger.info(f'Retrieving Infraxys token from {filename}')
            jsonObject = JsonUtils.get_instance().load_from_file(filename=filename)
            endpoint = jsonObject["endpoint"]
            api_token = jsonObject["token"]
            InfraxysRestClient._instances[infraxys_config_variable] = \
                InfraxysRestClient(endpoint=endpoint, api_token=api_token)

        return InfraxysRestClient._instances[infraxys_config_variable]

    def __init__(self, endpoint, api_token):
        self.endpoint = endpoint
        self.api_token = api_token
        self.logger = Logger.get_logger(self.__class__.__name__)

    def get_child_instance(self, parent_instance_guid, container_guid, child_packet_guid=None,
                           child_packet_type=None, child_packet_key=None, attribute_name=None,
                           attribute_value=None, branch='master', json_body={}):

        json_object = self.get_child_instances(parent_instance_guid=parent_instance_guid, container_guid=container_guid,
                                               child_packet_type=child_packet_type, child_packet_key=child_packet_key,
                                               attribute_name=attribute_name, attribute_value=attribute_value,
                                               branch=branch, json_body=json_body)

        instances = json_object["instances"]
        if len(instances) == 0:
            return None
        elif len(instances) == 1:
            return instances[0]
        else:
            raise Exception("Multiple instances returned while maximum 1 is expected.")

    def get_child_instances(self, parent_instance_guid, container_guid, child_packet_guid=None,
                            child_packet_type=None, child_packet_key=None, attribute_name=None,
                            attribute_value=None, branch='master', json_body={}):
        if container_guid:
            request_path = f'container/{container_guid}/instances/{parent_instance_guid}/children'
        else:
            request_path = f'instance/{branch}/{parent_instance_guid}/children'

        if attribute_name and attribute_value:
            json_body.update({
                "attributeName": attribute_name,
                "attributeValue": attribute_value
            })

        url = "{}/api/v1/{}".format(self.endpoint, request_path)

        if child_packet_type:
            json_body.update({
                "packetType": child_packet_type
            })

        if child_packet_guid:
            json_body.update({
                "packetGuid": child_packet_guid
            })

        if child_packet_key:
            json_body.update({
                "packetKey": child_packet_key
            })

        response = self.execute_request(request_method='GET', url=url, json_body=json_body)
        json_object = json.loads(response.content.decode('utf-8'))
        return json_object

    def ensure_instance(self, instance, parent_instance_guid, parent_container_guid=None, branch='master'):
        assert isinstance(instance, json_instance.JsonInstance)
        if parent_container_guid:
            request_path = f'instance/{branch}/{parent_container_guid}/instances/{parent_instance_guid}/children/ensure'
        else:
            request_path = f'instance/{branch}/{parent_instance_guid}/children/ensure'

        url = "{}/api/v1/{}".format(self.endpoint, request_path)
        json_body = {
            "instances": [
                instance.to_json_fields()
            ]
        }
        response = self.execute_request(request_method='POST', url=url, json_body=json_body)
        json_object = json.loads(response.content.decode('utf-8'))

        print(json_object)
        if "status" in json_object and json_object["status"] == "FAILED":
            message = 'Error creating instance: {}'.format(json_object["message"])
            raise Exception(message)

        return response

    def execute_request(self, request_method, url, headers: object = {}, json_body=None):
        headers.update({'Authorization': 'token {}'.format(self.api_token)
                        })
        headers.update({'Content-Type': 'application/json'})

        print("Executing {} to REST endpoint: {}".format(request_method, url))
        response = requests.request(request_method, url, headers=headers, verify=False, json=json_body)

        if response.status_code == 200:
            pass
        elif response.status_code == 204:
            self.logger.info("Successful deletion.")
        elif response.status_code == 400:
            raise BadRequestException()
        elif response.status_code == 403:
            raise UnauthorizedException()
        elif response.status_code == 404:
            raise NotFoundException()
        else:
            self.logger.warn("Status code: {}".format(response.status_code))
            try:
                if "token" not in response.content:
                    self.logger.warn(response.content)
            finally:
                pass

        return response
