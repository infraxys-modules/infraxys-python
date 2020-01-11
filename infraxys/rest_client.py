import json
import os

import requests

from .json import json_instance


class RestClient(object):

    def __init__(self):
        self.endpoint = os.environ['INFRAXYS_REST_ENDPOINT']

    def get_child_instance_by_attribute_value(self, parent_instance_guid, attribute_name,
                                              attribute_value):
        json_object = self.get_child_instances_by_attribute_value(parent_instance_guid=parent_instance_guid,
                                                               attribute_name=attribute_name,
                                                               attribute_value=attribute_value)

        if len(json_object['instances']) == 0:
            return None
        elif len(json_object['instances']) > 1:
            raise Exception(
                "Expecting only 1 child instance, but found {} for attribute '{}' with value '{}' under instance guid '{}'.".format(
                    len(json_object['instances']), attribute_name, attribute_value, parent_instance_guid)
            )

        return json_object["instances"][0]

    def get_child_instances_by_attribute_value(self, parent_instance_guid, attribute_name,
                                               attribute_value):

        assert attribute_name and attribute_value

        request_path = f'instance/{parent_instance_guid}/byAttributeValue'
        url = "{}/{}".format(self.endpoint, request_path)
        json_body = {
            "attributeName": attribute_name,
            "attributeValue": attribute_value
        }
        response = self.execute_request(request_method='GET', url=url, json_body=json_body)
        json_object = json.loads(response.content.decode('utf-8'))
        return json_object

    def get_child_instances(self, parent_instance_guid, child_packet_guid=None, child_packet_key=None):
        assert child_packet_guid or child_packet_key
        request_path = f'instance/{parent_instance_guid}/children'
        url = "{}/{}".format(self.endpoint, request_path)
        if child_packet_guid:
            json_body = {
                "packetGuid": child_packet_guid
            }
        else:
            json_body = {
                "packetKey": child_packet_key
            }

        response = self.execute_request(request_method='GET', url=url, json_body=json_body)
        return response

    def ensure_instance(self, instance, parent_instance_guid):
        assert isinstance(instance, json_instance.JsonInstance)
        request_path = f'instance/{parent_instance_guid}/children/ensure'
        url = "{}/{}".format(self.endpoint, request_path)
        json_body = {
            "instances": [
            instance.to_json_fields()
                ]
        }
        response = self.execute_request(request_method='POST', url=url, json_body=json_body)
        return response

    def execute_request(self, request_method, url, headers: object = {}, json_body=None):
        # bearer = ''; # get from a Variable or from an external Vault, ... Not needed for Infraxys developer
        # headers.update({'Authorization': 'Bearer {}'.format(bearer)
        #                })
        headers.update({'Content-Type': 'application/json'})

        print("Executing {} to REST endpoint: {}".format(request_method, url))
        response = requests.request(request_method, url, headers=headers, verify=False, json=json_body)

        print("Status code: {}".format(response.status_code))
        return response
