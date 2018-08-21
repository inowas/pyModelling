import docker
import os
from copy import deepcopy


class DockerManager(object):
    _simulation_server_command = 'python /Simulation/SimulationServer.py'
    _optimization_server_command = 'python /Optimization/OptimizationManager.py'
    _running_containers = {}

    def __init__(self, configuration):
        self.configuration = configuration
        self.client = docker.from_env()
        self.optimization_image = self.configuration['OPTIMIZATION_IMAGE']
        self.simulation_image = self.configuration['SIMULATION_IMAGE']

        self.volumes = {
            os.path.realpath(self.configuration['HOST_TEMP_FOLDER']): {'bind': self.configuration['DOCKER_TEMP_FOLDER'],
                                                                       'mode': 'rw'},
            os.path.realpath('./Optimization'): {'bind': '/Optimization', 'mode': 'rw'},
            os.path.realpath('./Simulation'): {'bind': '/Simulation', 'mode': 'rw'}
        }

    def run_container(self, container_type, job_id, number):
        if container_type == "optimization":
            image = self.optimization_image
            command = self._optimization_server_command
        elif container_type == "simulation":
            image = self.simulation_image
            command = self._simulation_server_command

        environment = deepcopy(self.configuration)
        environment['OPTIMIZATION_ID'] = job_id
        environment['SIMULATION_RESPONSE_QUEUE'] += job_id
        environment['SIMULATION_REQUEST_QUEUE'] += job_id

        for _ in range(number):
            container = self.client.containers.run(
                image,
                command=command,
                environment=environment,
                volumes=self.volumes,
                detach=True
            )
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
        return not_stopped_containers

        del self._running_containers[job_id]

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
