from copy import deepcopy
import docker


class DockerManager(object):
    _running_containers = {}

    def __init__(self, configuration):

        print(' ### Initializing DockerManager ### ')
        print(' ### Configuration:', configuration)

        self.configuration = configuration
        self.client = docker.from_env()
        self.optimization_image = self.configuration['OPTIMIZATION_IMAGE']
        self.client.images.pull(self.optimization_image)

        self.simulation_image = self.configuration['SIMULATION_IMAGE']
        self.client.images.pull(self.simulation_image)

        self.volumes = {
            self.configuration['OPTIMIZATION_DATA_FOLDER_IN_CONTAINER']:
                {'bind': self.configuration['OPTIMIZATION_DATA_FOLDER_IN_CONTAINER'], 'mode': 'rw'}
        }

    def run_container(self, container_type, job_id, number):
        if container_type == "optimization":
            image = self.optimization_image
        elif container_type == "simulation":
            image = self.simulation_image
        else:
            return

        environment = deepcopy(self.configuration)
        environment['OPTIMIZATION_ID'] = job_id
        environment['SIMULATION_RESPONSE_QUEUE'] += job_id
        environment['SIMULATION_REQUEST_QUEUE'] += job_id

        print('Run container type ' + container_type + '.', environment)

        for _ in range(number):
            container = self.client.containers.run(
                image,
                environment=environment,
                volumes=self.volumes,
                detach=True
            )
            print('ContainerId: ' + str(container))
            try:
                self._running_containers[job_id].append(container)
            except KeyError:
                self._running_containers[job_id] = [container]
        return

    def stop_all_job_containers(self, job_id, remove=True):
        not_stopped_containers = []
        for container in self._running_containers[job_id]:
            try:
                container.stop()
                if remove:
                    container.remove()
                    del container
            except Exception as e:
                not_stopped_containers.append(container)
                print(str(e))

        del self._running_containers[job_id]

        return not_stopped_containers

    def clean(self):
        for job_id in self._running_containers:
            for container in self._running_containers[job_id]:
                container.stop()
                container.remove()

    def remove_exited_containers(self):
        containers = self.client.containers.list(
            filters={
                'status': 'exited'
            }
        )
        for container in containers:
            container.remove()
