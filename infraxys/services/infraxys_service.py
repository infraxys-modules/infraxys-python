import json
import importlib

from infraxys.infraxys_rest_client import InfraxysRestClient
from infraxys.model.base_object import BaseObject
from infraxys.json.json_utils import JsonUtils
from infraxys.model.packet import Packet
from .packet_service import PacketService
from infraxys.services.base_service import BaseService
from ..json.instance_reference import InstanceReference


class InfraxysService(BaseService):
    _instance = None

    def get_instance():
        if not InfraxysService._instance:
            InfraxysService._instance = InfraxysService()

        return InfraxysService._instance

    def get_by_reference(self, instance_reference, target_class):
        json_body = instance_reference.to_rest_get_json()
        response = InfraxysRestClient.get_instance().execute_get(path='instances', json_body=json_body)
        json_response = json.loads(response.content.decode('utf-8'))
        instance_json = json_response['instance']
        return self._get_instance_from_instance_json(instance_json, target_class)

    def get_child_by_attribute(self, parent_instance, attribute_name, attribute_value, target_class):
        json_body = parent_instance.instance_reference.to_rest_get_json()
        json_body.update({
            'attributeName': attribute_name,
            'attributeValue': attribute_value
        })
        response = InfraxysRestClient.get_instance().execute_get(path='instances/byAttributeNameAndValue', json_body=json_body)
        json_response = json.loads(response.content.decode('utf-8'))
        print(json_response)
        if 'instance' in json_response:
            instance_json = json_response['instance']
            result = self._get_instance_from_instance_json(instance_json, target_class)
            return result

        return None

    def _get_instance_from_instance_json(self, instance_json, target_class):
        instance_reference = InstanceReference(instance_json['moduleBranchPath'],
                                               instance_json['containerId'],
                                               instance_json['id'],
                                               instance_json['environmentId'])
        instance = target_class(instance_reference=instance_reference)
        if 'attributes' in instance_json:
            attributes_json = instance_json['attributes']
            self.logger.info(f'Creating instance of class {target_class}')

            for attribute_json in attributes_json:
                attribute_name = attribute_json['name']
                if hasattr(instance, attribute_name):
                    self.logger.debug(f'Setting attribute {attribute_name}.')
                    instance.__setattr__(attribute_name, attribute_json['value'])
                else:
                    self.logger.debug(f'Python class doesn\'t have attribute {attribute_name}')

        return instance

    def save(self, instance):
        assert isinstance(instance, BaseObject)
        assert instance.instance_reference or instance.parent_instance_reference

        packet = instance.get_packet() #PacketService.get_instance().get_packet(for_instance=instance)
        assert packet
        instance_body = {
            "packetId": packet.id,
            "packetPath": packet.module_branch_path
        }

        attributes = []
        for attribute in packet.attributes:
            value = None
            print(f'Processing attribute {attribute.name}')
            if hasattr(instance, attribute.name):
                value = instance.__getattribute__(attribute.name)
                print(f'Attribute value: {value}')

            if not value and attribute.default_value:
                value = attribute.default_value

            print(f'Adding attribute {attribute.name} with value {value}.')
            attributes.append({
                "id": attribute.id,
                "name": attribute.name,
                "value": value
            })

        if instance.instance_reference: # existing instance
            instance_body.update({
                "id": instance.instance_reference.instance_id,
                "moduleBranchPath": instance.instance_reference.module_branch_path,
                "environmentId": instance.instance_reference.environment_id,
                "containerId": instance.instance_reference.container_id
            })
        else: # add to parent
            instance_body.update({
                "parentId": instance.parent_instance_reference.instance_id,
                "moduleBranchPath": instance.parent_instance_reference.module_branch_path,
                "environmentId": instance.parent_instance_reference.environment_id,
                "containerId": instance.parent_instance_reference.container_id
            })

        instance_body.update({
            "attributes": attributes
        })

        json_body = {
            "instance": instance_body
        }

        print(json_body)
        print('---------------')
        response = InfraxysRestClient.get_instance().execute_post(path='instances', json_body=json_body)
        json_object = json.loads(response.content.decode('utf-8'))

        print(json_object)
        if "status" in json_object and json_object["status"] == "FAILED":
            message = 'Error creating instance: {}'.format(json_object["message"])
            raise Exception(message)

        return response

