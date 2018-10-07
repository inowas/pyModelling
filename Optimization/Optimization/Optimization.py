import os
import shutil
import random
import json
import uuid
import numpy as np
from mystic.solvers import NelderMeadSimplexSolver
from mystic.monitors import Monitor
from mystic.termination import CandidateRelativeTolerance as CRT
from sklearn.cluster import KMeans
from deap import base
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
import copy
import pika
import logging
import logging.config


class OptimizationBase(object):
    """
    Optimization algorithm class

    """
    logger = logging.getLogger('optimization')

    def __init__(self, optimization_id, request_data, response_channel, response_queue, rabbit_host,
                 rabbit_port, rabbit_vhost, rabbit_user, rabbit_password, simulation_request_queue,
                 simulation_response_queue):

        self.optimization_id = optimization_id
        self.response_queue = response_queue
        self.response_channel = response_channel
        self.host = rabbit_host
        self.port = int(rabbit_port)
        self.login = rabbit_user
        self.password = rabbit_password
        self.virtualhost = rabbit_vhost
        self.request_data = request_data
        try:
            self.report_frequency = int(self.request_data['optimization']['parameters']['report_frequency'])
        except Exception:
            self.logger.warning('report_frequency is not defined, set to 0')
            self.report_frequency = 0

        self._progress_log = []
        self._simulation_count = 0
        self._iter_count = 0
        self.response = {'optimization_id': self.optimization_id,
                         'message': ''}

        self.initial_solutions = self.request_data['optimization'].get('solutions', [])
        self.initial_solution_id =  self.request_data['optimization']['parameters'].get('initial_solution_id')
        self.logger.info('Initial solution: {}'.format(self.initial_solution_id))
        try:
            self.progress_global = self.request_data['optimization']['progress']['GA']
        except:
            self.progress_global = {}
        self.progress_local = {}

        try:
            self.var_template = copy.deepcopy(
                [i['objects'] for i in self.initial_solutions if i['id'] == self.initial_solution_id][0]
            )
            self.logger.info('Variables template is build from initial solution')
        except Exception:
            self.var_template = copy.deepcopy(self.request_data['optimization']['objects'])
            self.logger.info('Variables template is build from optimization objects')
        
        self.weights = [i["weight"] for i in self.request_data["optimization"]["objectives"]]

        self.var_map, self.bounds, self.initial_values = self.read_optimization_data()

        # Rabbit stuff
        self.simulation_request_queue = simulation_request_queue
        self.simulation_response_queue = simulation_response_queue

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtualhost,
                credentials=pika.PlainCredentials(self.login, self.password),
            )
        )

        self.channel = self.connection.channel()
        self.logger.info('Declaring simulation request queue: ' + self.simulation_request_queue)
        self.channel.queue_declare(
            queue=self.simulation_request_queue,
            durable=True
        )

        self.logger.info('Declaring simulation response queue: ' + self.simulation_response_queue)
        self.channel.queue_declare(
            queue=self.simulation_response_queue,
            durable=True
        )

    def publish_simulation_job(self, individual, ind_id):
        self.logger.info("Requesting fitness for individual {}".format(individual))
        self.logger.debug("Publishing simulation job for individual {} to the queue: {}"
              .format(individual, self.simulation_request_queue))

        objects_data = self.apply_individual(individual=individual)

        request_data = {
            'ind_id': ind_id,
            'simulation_id': str(uuid.uuid4()),
            'objects_data': objects_data,
            'optimization_id': self.optimization_id
        }
        request_data = json.dumps(request_data).encode()

        self.channel.basic_publish(
            exchange='',
            routing_key=self.simulation_request_queue,
            body=request_data,
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        return

    def apply_individual(self, individual):
        """Write individual values to variable template and return the filled template"""
        var_template = copy.deepcopy(self.var_template)
        for ind_value, keys in zip(individual, self.var_map):
            if keys[1] == 'position':
                ind_value = int(ind_value)
                
            if keys[1] == 'concentration':
                for object_ in var_template:
                    if object_['id'] == keys[0]:
                        object_[keys[1]][keys[2]][keys[3]]['result'] = ind_value
                        break
            else:
                for object_ in var_template:
                    if object_['id'] == keys[0]:
                        object_[keys[1]][keys[2]]['result'] = ind_value
                        break

        return var_template

    def read_optimization_data(self):
        """
        Example of variables template, where values are fixed ones and Nones are optimized:
        
        Example of variables map and variables boundaries:
        var_map = [(0, flux, 0), (0, concentration, 0),(0, position, row),(0, position, col)]
        var_bounds = [(0, 10), (0, 1),(0, 30),(0, 30)]
        initial_values = [0, 0, 10, 10]
        """

        var_map = []
        var_bounds = []
        initial_values = []

        for object_ in self.var_template:
            for parameter, value in object_.items():
                if parameter == 'position':
                    for axis, axis_data in value.items():
                        if axis_data['min'] != axis_data['max']:
                            var_map.append((object_['id'], 'position', axis))
                            var_bounds.append((axis_data['min'], axis_data['max']))
                            initial_value = axis_data.get('result')
                            if initial_value is None:
                                initial_values.append(int((axis_data['max']+axis_data['min'])/2))
                            else:
                                initial_values.append(initial_value)
                            object_['position'][axis]['result'] = None
                        else:
                            object_['position'][axis]['result'] = axis_data['min']


                elif parameter == 'flux':
                    for period, period_data in value.items():
                        if period_data['min'] != period_data['max']:
                            var_map.append((object_['id'], 'flux', period))
                            var_bounds.append((period_data['min'], period_data['max']))
                            initial_value = period_data.get('result')
                            if initial_value is None:
                                initial_values.append((period_data['max']+period_data['min'])/2)
                            else:
                                initial_values.append(initial_value)
                            object_['flux'][period]['result'] = None  
                        else:
                            object_['flux'][period]['result'] = period_data['min']


                elif parameter == 'concentration':
                    for period, period_data in value.items():
                        for component, component_data in period_data.items():
                            if component_data['min'] != component_data['max']:
                                var_map.append((object_['id'], 'concentration', period, component))
                                var_bounds.append((component_data['min'], component_data['max']))
                                initial_value = component_data.get('result')
                                if initial_value is None:
                                    initial_values.append((component_data['max']+component_data['min'])/2)
                                else:
                                    initial_values.append(initial_value)
                                object_[parameter][period][component]['result'] = None
                            else:
                                object_[parameter][period][component]['result'] = component_data['min']

        return var_map, var_bounds, initial_values


class NSGA(OptimizationBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._hypervolume_ref_point = None
        self._diversity_ref_point = None

    def run(self):

        ngen = self.request_data['optimization']['parameters']['ngen']
        pop_size = self.request_data['optimization']['parameters']['pop_size']
        mutpb = self.request_data['optimization']['parameters']['mutpb']
        cxpb = self.request_data['optimization']['parameters']['cxpb']
        mu = pop_size
        eta = self.request_data['optimization']['parameters']['eta']
        indpb = self.request_data['optimization']['parameters']['indpb']
        ncls = self.request_data['optimization']['parameters']['ncls']
        qbound = self.request_data['optimization']['parameters']['qbound']
        diversity_flg = self.request_data['optimization']['parameters']['diversity_flg']
        #Ensure that number of clusters not larger that 1/3 pop_size
        if ncls > pop_size/3:
            self.logger.warning(
                'Specified number of clusters is {}, wil be reduced to 1/3 pop_size'.format(ncls)
            )
            ncls = int(pop_size/3)
            

        creator.create(
            "Fitnessmulti", base.Fitness,
            weights=self.weights
        )
        creator.create("Individual", list, fitness=creator.Fitnessmulti)
        self.toolbox = base.Toolbox()
        self.toolbox.register("candidate", self.make_candidate, self.bounds)
        self.toolbox.register(
            "mutate", tools.mutPolynomialBounded,
            low=[i[0] for i in self.bounds], up=[i[1] for i in self.bounds],
            eta=eta, indpb=indpb
        )
        self.toolbox.register(
            "mate", tools.cxSimulatedBinaryBounded,
            low=[i[0] for i in self.bounds], up=[i[1] for i in self.bounds],
            eta=eta
        )
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self.toolbox.candidate)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("select", tools.selNSGA2)
        
        if len(self.weights) > 1:
            self.hall_of_fame = tools.ParetoFront()
        else:
            self.hall_of_fame = tools.HallOfFame(maxsize=10)
        

        pop = self.toolbox.population(n=mu)
        pop = self.evaluate_population(pop=pop)
        # This is just to assign the crowding distance to the individuals
        # no actual selection is done
        pop = self.toolbox.select(pop, len(pop))
        self.hall_of_fame.update(pop)
        self.calculate_hypervolume(pop)
        self.logger.info('Generating response for iteration No. {}'.format(0))
        self.callback(final=False)

        # Begin the generational process
        for gen in range(1, ngen):
            offspring = self.generate_offspring(
                pop=pop,
                cxpb=cxpb,
                mutpb=mutpb,
                lambda_=mu
            )
            offspring = self.evaluate_population(pop=offspring)
            combined_pop = pop + offspring

            if diversity_flg:
                pop = self.check_diversity(combined_pop, ncls, qbound, mu)
            else:
                pop = self.toolbox.select(combined_pop, mu)

            self.hall_of_fame.update(pop)
            self.calculate_hypervolume(pop)
            self.logger.info('Generating response for iteration No. {}'.format(gen))
            self.callback(final=gen == ngen - 1)

        return

    def callback(self, final=False, status_code=200):
        """
        Generate response json of the NSGA algorithm
        exmple of response
        response = {
            optimization_id: 1,
            status_code: 200,
            solutions: [
                {
                    fitness: [1.0, 2.0],
                    variables: [1,2,3,1,2,3...],
                    locally_optimized: False,
                    objects: [
                        {
                            id: 1,
                            lay: {
                                "min": 0,
                                "max": 5,
                                "result: 3
                            },
                            row... etc.
                            
                        },
                        .....
                    ]
                },
                .....
            ],
            progress: {
                GA: {
                    progress_log: [1,2,3...],
                    simulation: 12,
                    simulation_total: 50,
                    iteration: 30,
                    iteration_total: 30,
                    final: true
                },
                Simplex: {}
                
            }
            
        }
        """ 
        self.response['status_code'] = status_code
        self.response['progress'] = {}
        self.response['progress']['Simplex'] = self.progress_local
        self.response['progress']['GA'] = {}
        self.response['progress']['GA']['progress_log'] = self._progress_log
        self.response['progress']['GA']['simulation'] = self._simulation_count
        self.response['progress']['GA']['simulation_total'] = self.request_data['optimization']['parameters']['pop_size']
        self.response['progress']['GA']['iteration'] = self._iter_count
        self.response['progress']['GA']['iteration_total'] = self.request_data['optimization']['parameters']['ngen']
        self.response['progress']['GA']['final'] = final
        self.response['solutions'] = []
        for individual in self.hall_of_fame:
            self.response['solutions'].append(
                {
                    'id': str(uuid.uuid4()),
                    'locally_optimized': False,
                    'fitness': list(individual.fitness.values),
                    'variables': list(individual),
                    'objects': self.apply_individual(individual)
                }
            )

        self.response_channel.basic_publish(
            exchange='',
            routing_key=self.response_queue,
            body=json.dumps(self.response).encode(),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )

        return

    def generate_offspring(self, pop, cxpb, mutpb, lambda_):
        # Vary population. Taken from def varOr()
        offspring = []
        for _ in range(lambda_):
            op_choice = random.random()
            if op_choice < cxpb:  # Apply crossover
                ind1, ind2 = map(self.toolbox.clone, random.sample(pop, 2))
                ind1, ind2 = self.toolbox.mate(ind1, ind2)
                del ind1.fitness.values
                offspring.append(ind1)
            elif op_choice < cxpb + mutpb:  # Apply mutation
                ind = self.toolbox.clone(random.choice(pop))
                ind, = self.toolbox.mutate(ind)
                del ind.fitness.values
                offspring.append(ind)
            else:  # Apply reproduction
                offspring.append(random.choice(pop))

        return offspring

    def check_diversity(self, pop, ncls, qbound, mu):
        self.logger.info('Performing clustering and diversity calculation...')

        Q_diversity, cluster_labels = self.project_and_cluster(
            ncls=ncls, pop=pop, weights=self.weights
        )
        self.logger.info('Q_diversity: {}, clusters: {}'. format(Q_diversity, cluster_labels))

        if self._diversity_ref_point is not None and Q_diversity < self._diversity_ref_point:
            self.logger.info(' Q diversity index {} lower than boundary {}, population will be diversified'.format(
                Q_diversity, self._diversity_ref_point
            ))

            pop = self.diversity_enhanced_selection(
                pop=pop, cluster_labels=cluster_labels,
                mu=mu, selection_method=self.toolbox.select
            )
        else:
            pop = self.toolbox.select(pop, mu)

        self._diversity_ref_point = qbound * Q_diversity

        return pop

    def calculate_hypervolume(self, pop):

        self.logger.info('Calculating hypervolume...')

        if self._hypervolume_ref_point is None:
            self.logger.info('Calculating hypervolume reference point...')
            worst_values = []
            fitness_array = np.array([i.fitness.values for i in pop])
            maxs = np.max(fitness_array, 0)
            mins = np.min(fitness_array, 0)
            for i, weight in enumerate(self.weights):
                if weight <= 0:
                    worst_values.append(maxs[i])
                else:
                    worst_values.append(mins[i])
            self._hypervolume_ref_point = np.array(worst_values)

        hv = hypervolume(pop, self._hypervolume_ref_point)
        self._progress_log.append(hv)
        self.logger.info('Hypervolume of the generation: {}'.format(self._progress_log[-1]))

    def evaluate_population(self, pop):
        self._simulation_count = 0
        self._iter_count += 1

        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        results = {}
        for _id, ind in enumerate(invalid_ind):
            self.publish_simulation_job(
                ind, _id
            )

        consumer_tag = str(uuid.uuid4())

        def consumer_callback(channel, method, properties, body):
            self._simulation_count += 1
            if self.report_frequency > 0 and \
                self._simulation_count % \
                int(self.request_data['optimization']['parameters']['pop_size'] /\
                self.report_frequency) == 0:
                self.callback()

            channel.basic_ack(delivery_tag=method.delivery_tag)
            content = json.loads(body.decode())
            if content['status_code'] == '500':
                raise Exception(
                    'Error during evaluation occured.' + '\r\n' + \
                    content['message']
                )

            results[content['ind_id']] = content['fitness']
            if len(results) == len(invalid_ind):
                self.logger.debug('Fetched results from the simulation response queue: ' + self.simulation_response_queue)
                self.channel.basic_cancel(
                    consumer_tag=consumer_tag
                )
                
            return

        self.logger.debug('Consuming results from the simulation response queue: ' + self.simulation_response_queue)
        self.channel.basic_consume(
            consumer_callback=consumer_callback,
            queue=self.simulation_response_queue,
            consumer_tag=consumer_tag
        )
        self.channel.start_consuming()

        for _id, ind in enumerate(invalid_ind):
            ind.fitness.values = results[_id]

        return pop

    @staticmethod
    def make_candidate(bounds):
        """Generates random initial individual"""
        return [
            random.randint(value[0], value[1]) for value in bounds
        ]

    @staticmethod
    def project_and_cluster(ncls, pop, weights):
        """Implementation of the Project And Cluster algorithm proposed by Syndhya et al."""
        fitnesses = np.array([ind.fitness.values for ind in pop])
        fitnesses_reprojected = np.zeros(fitnesses.shape)
        maxs = np.max(fitnesses, 0)
        mins = np.min(fitnesses, 0)
        worst_values = []
        for i, weight in enumerate(weights):
            if weight <= 0:
                worst_values.append(maxs[i])
            else:
                worst_values.append(mins[i])
        ws = np.array(worst_values) ** -1

        for i, fitness in enumerate(fitnesses):
            fitnesses_reprojected[i] = ((1 - np.dot(ws, fitness)) / np.dot(ws, ws)) * ws + fitness

        # Applying K-means clustering
        kmeans = KMeans(n_clusters=ncls, random_state=0).fit(fitnesses_reprojected)
        cluster_labels = kmeans.labels_
        centroids = kmeans.cluster_centers_

        # Calculating cluster diversity index
        Q_diversity = 0
        for cluster_label, centroid in zip(np.unique(cluster_labels), centroids):
            cluster_inds = [i for i, j in zip(pop, cluster_labels) if j == cluster_label]
            sum_of_distances = 0
            for ind in cluster_inds:
                sum_of_distances += np.linalg.norm(centroid - ind.fitness.values)
            Q_diversity += sum_of_distances / len(cluster_inds)

        return Q_diversity, cluster_labels

    @staticmethod
    def diversity_enhanced_selection(pop, cluster_labels, mu, selection_method):
        # Returns population with enhanced deversity
        diverse_pop = []
        cluster_pop_sorted = {}

        for cluster in np.unique(cluster_labels):
            cluster_inds = [i for i, j in zip(pop, cluster_labels) if j == cluster]
            cluster_pop_sorted[cluster] = selection_method(cluster_inds, len(cluster_inds))

        rank = 0
        while len(diverse_pop) < mu:
            for p in cluster_pop_sorted.values():
                try:
                    diverse_pop.append(p[rank])
                except IndexError:
                    pass
                if len(diverse_pop) == mu:
                    return diverse_pop
            rank += 1

        return diverse_pop


class NelderMead(OptimizationBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._best_scalar_fitness = None
        self._best_fitness = None
        self._best_individual = None
        self.objective_targets, self.z_nadir, self.z_utopian = None, None, None
        self.scalarization_method = 'achievement'
        
        try:
            self.objective_targets = [i['target'] for i in self.request_data['optimization']['objectives']]
            self.logger.info('Objective target values are: {}'.format(self.objective_targets))
            if len(self.initial_solutions) > 0:
                fitness_array = np.array([i['fitness'] for i in self.initial_solutions])
                self.z_nadir, self.z_utopian = self.calculate_z(fitness_array)
                self.logger.info(
                    'Nadir and utopian vectors calculated from initial solutions are: {}, {}'.format(self.z_nadir, self.z_utopian)
                )
        except KeyError:
            self.logger.info('Missing objective target values, scalars will be calculated using weights')
        except:
            self.logger.error('Unknown error', exc_info=True)

        if None in (self.objective_targets, self.z_nadir, self.z_utopian):
            self.scalarization_method = 'linear'
            self.logger.info('Scalarization method: linear')
        else:
            self.logger.info('Scalraization method: achievement scalarization')
                

    def run(self):
        self.logger.info('Start local optimization...')
        maxf = self.request_data['optimization']['parameters']['maxf']
        xtol = self.request_data['optimization']['parameters']['xtol']
        ftol = self.request_data['optimization']['parameters']['ftol']

        solver = NelderMeadSimplexSolver(len(self.initial_values))
        solver.SetInitialPoints(self.initial_values)
        solver.SetStrictRanges([i[0] for i in self.bounds], [i[1] for i in self.bounds])
        solver.SetEvaluationLimits(evaluations=maxf)
        solver.SetTermination(CRT(xtol=ftol, ftol=ftol))
        solver.Solve(
            self.evaluate_single_solution,
            callback=self.callback
        )
        solver.enable_signal_handler()

        self.callback(
            individual=solver.Solution(),
            final=True
        )

        return

    def compose_solutions(self):
        solutions = []
        if self.initial_solution_id is None:
            solution_id = str(uuid.uuid4())
        else:
            solution_id = self.initial_solution_id

        for initial_solution in self.initial_solutions:
            if initial_solution['id'] != solution_id:
                solutions.append(initial_solution)
            
        solutions.append(
            {
                'id': solution_id,
                'locally_optimized': True,
                'fitness': list(self._best_fitness),
                'variables': list(self._best_individual),
                'objects': self.apply_individual(self._best_individual)
            }
        )
        return solutions

    def callback(self, individual, final=False, status_code=200):
        """
        Generate response json of the Siplex algorithm
        """
        self._iter_count += 1
        self._progress_log.append(self._best_scalar_fitness)
        
        self.response['status_code'] = status_code
        self.response['progress'] = {}
        self.response['progress']['GA'] = self.progress_global
        self.response['progress']['Simplex'] = {}
        self.response['progress']['Simplex']['progress_log'] = self._progress_log
        self.response['progress']['Simplex']['iteration'] = self._iter_count
        self.response['progress']['Simplex']['iteration_total'] = self.request_data['optimization']['parameters']['maxf']
        self.response['progress']['Simplex']['final'] = final
        self.response['solutions'] = self.compose_solutions()

        self.response_channel.basic_publish(
            exchange='',
            routing_key=self.response_queue,
            body=json.dumps(self.response).encode(),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        return

    def evaluate_single_solution(self, individual, *weights):
        """Returns scalar fitness if weghts, else vector fitness of a single individual"""

        self.publish_simulation_job(individual, 0)

        fitness = []
        consumer_tag = str(uuid.uuid4())

        def consumer_callback(channel, method, properties, body):
            channel.basic_ack(delivery_tag=method.delivery_tag)
            content = json.loads(body.decode())

            if content['status_code'] == '500':
                raise Exception(
                    'Error during evaluation occurred.' + '\r\n' + content['message']
                )

            for i in content['fitness']:
                fitness.append(i)

            self.logger.info('Fetched result from the simulation response queue: ' + self.simulation_response_queue)
            self.logger.info('Fitness: {}'.format(fitness))
            self.channel.basic_cancel(consumer_tag=consumer_tag)
            return

        self.logger.info('Consuming results from the simulation response queue: ' + self.simulation_response_queue)
        self.channel.basic_consume(
            consumer_callback=consumer_callback,
            queue=self.simulation_response_queue,
            consumer_tag=consumer_tag
        )
        self.channel.start_consuming()

        if self.scalarization_method == 'achievement':
            scalar_fitness = self.achievement_scalarization(fitness)
        elif self.scalarization_method == 'linear':
            scalar_fitness = self.linear_sclarization(fitness)

        self.logger.info('Scalar fitness: {}'.format(scalar_fitness))

        if self._best_scalar_fitness is not None and scalar_fitness >= self._best_scalar_fitness:
            return scalar_fitness

        else:
            self._best_scalar_fitness = scalar_fitness
            self._best_fitness = fitness
            self._best_individual = individual

        return scalar_fitness
    
    def calculate_z(self, fitness_array):
        """Calculates nadir and utopian vectors from a fitness 
        array of shape (len(objectives), len(solutions))
        """
        try:
            z_nadir = []
            z_utopian = []
            maxs = np.max(fitness_array, 0)
            mins = np.min(fitness_array, 0)
            for i, weight in enumerate(self.weights):
                if weight <= 0:
                    z_nadir.append(maxs[i])
                    z_utopian.append(mins[i])
                else:
                    z_nadir.append(mins[i])
                    z_utopian.append(maxs[i])

            return np.array(z_nadir), np.array(z_utopian)
        except Exception:
            self.logger.error('Could not calculate Nadir and Utopian vectors', exc_info=True)
            return None, None
    
    def linear_sclarization(self, fitness):
        scalar_fitness = 0
        for value, weight in zip(fitness, self.weights):
            scalar_fitness += value * weight * -1
        return scalar_fitness
    
    def achievement_scalarization(self, fitness):
        """Calculates Achevement Based Scalar of a multidimensional fitness"""
        p = 10e-6 # augmentation coefficient
        fitness_normalized = []
        augmentation = []

        for fitness_i, objective_targets_i, z_nadir_i, z_utopian_i in zip(fitness, self.objective_targets, self.z_nadir, self.z_utopian):
            fitness_normalized.append(
                (fitness_i - objective_targets_i) / \
                (z_nadir_i - z_utopian_i)
            )
            augmentation.append(
                fitness_i / \
                (z_nadir_i - z_utopian_i)
            )

        fitness_normalized_augemnted = [i + p * sum(augmentation) for i in fitness_normalized]
        scalar_fitness = max(fitness_normalized_augemnted)

        return scalar_fitness