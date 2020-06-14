class InstanceReference(object):

    def __init__(self, name, module_branch_path, environment_id, container_id, instance_id):
        self.name = name
        self.module_branch_path = module_branch_path
        self.environment_id = environment_id
        self.container_id = container_id
        self.instance_id = instance_id
