from copy import deepcopy
import docker
import logging
import logging.config


class DockerManager(object):
    _running_containers = {}
    logger = logging.getLogger('docker_manager')

    def __init__(self, configuration):

        self.logger.info('### Initializing DockerManager ### ')
        self.logger.info('### Configuration:'+str(configuration))

        self.configuration = configuration
        self.client = docker.from_env()

        self.optimization_image = self.configuration['OPTIMIZATION_IMAGE']
        self.logger.info('### Pulling image ' + str(self.optimization_image))
        self.client.images.pull(self.optimization_image)

        self.simulation_image = self.configuration['SIMULATION_IMAGE']
        self.logger.info('### Pulling image ' + str(self.simulation_image))
        self.client.images.pull(self.simulation_image)

        volume_name = self.configuration['OPTIMIZATION_DATA_VOLUME']
        self.volumes = {
            volume_name: {'bind': self.configuration['OPTIMIZATION_DATA_FOLDER'], 'mode': 'rw'}
        }
        self.network = self.configuration['RABBITMQ_NETWORK']

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

        self.logger.info('Run container type ' + container_type + '.', environment)

        for _ in range(number):
            container = self.client.containers.run(
                image,
                environment=environment,
                volumes=self.volumes,
                network=self.network,
                detach=True
            )
  
            self.logger.info('ContainerId: ' + str(container))
            
            try:
                self._running_containers[job_id].append(container)
            except KeyError:
                self._running_containers[job_id] = [container]
        return
    
    def inspect_containers(self, job_id):
        exited_containers = {}
        for container in self._running_containers[job_id]:
            state = self.client.api.inspect_container(container.id)['State']
            if state['Running'] == False:
                exited_containers[container.id] = {
                    'state': state,
                    'logs': self.client.api.logs(container.id)
                }

        return exited_containers
    
    def delete_inactive_jobs(self):
        for job_id in self._running_containers:
            job_active = False
            for container in self._running_containers[job_id]:
                state = self.client.api.inspect_container(container.id)['State']
                if state['Running'] == True:
                    job_active = True
                else:
                    container.stop()
                    container.remove()
                    del container
            if not job_active:
                del self._running_containers[job_id]

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
                self.logger.error(str(e), exc_info=True)

        del self._running_containers[job_id]

        return not_stopped_containers

    def clean(self):
        for job_id in self._running_containers:
            for container in self._running_containers[job_id]:
                container.stop()
                container.remove()

    # def remove_exited_containers(self):
    #     containers = self.client.containers.list(
    #         filters={
    #             'status': 'exited'
    #         }
    #     )
    #     for container in containers:
    #         container.remove()
