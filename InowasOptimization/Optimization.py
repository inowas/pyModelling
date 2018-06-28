import os
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
import asyncio
from aio_pika import connect_robust
from aio_pika.patterns import RPC
import pika

from SimulationRpcClient import SimulationRpcClient 


class Optimization(object):
    """
    Optimization algorithm class

    """

    def __init__(self, request_data, response_channel, response_queue, data_folder, rabbit_host,
                 rabbit_port, rabbit_vhost, rabbit_user, rabbit_password):

        self.response_queue = response_queue
        self.response_channel = response_channel
        self.host = rabbit_host
        self.port = int(rabbit_port)
        self.login = rabbit_user
        self.password = rabbit_password
        self.virtualhost = rabbit_vhost

        self.request_data = request_data

        self.progress_log = []
        self.hypervolume_ref_point = None
        self.diversity_ref_point = None
        
        try:
            self.optimization_id = self.request_data['optimization']['id']
        except KeyError:
            self.optimization_id = uuid.uuid4()

        data_dir = os.path.join(
            os.path.realpath(data_folder),
            'optimization-data-'+str(self.optimization_id)
        )
        config_file = os.path.join(
            data_dir,
            'config.json'
        )
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        with open(config_file, 'w') as f:
            json.dump(self.request_data, f)
        
        self.var_template = copy.deepcopy(self.request_data['optimization']['objects'])
        
        self.var_map, self.bounds = self.read_optimitation_data()
    
    def run_optimization(self):

        if self.request_data['optimization']['parameters']['method'] == 'GA':
            response = self.nsga_hybrid()
            # result, result_log = self.nsga_hybrid()
        
        elif self.request_data['optimization']['parameters']['method'] == 'Simplex':
            response = self.simplex()
        
        return response
    
    def simplex(self):
        print('Start local optimization')
        # Inverting weights (*-1) to convert problem to minimizing 
        weights = [i["weight"]*-1 for i in self.request_data["optimization"]["objectives"]]
        maxf = self.request_data['optimization']['parameters']['maxf']

        stepmon = Monitor()
        evalmon = Monitor()

        solver = NelderMeadSimplexSolver(len(weights))
        solver.SetInitialPoints(INITIAL_FITNESS)
        solver.SetEvaluationMonitor(evalmon)
        solver.SetGenerationMonitor(stepmon)
        solver.SetStrictRanges([i[0] for i in self.bounds], [i[1] for i in self.bounds])
        solver.SetEvaluationLimits(evaluations=MAXF)
        solver.SetTermination(CRT(xtol=1e-4, ftol=1e-4))
        solver.Solve(self.evaluate_single_solution, ExtraArgs={'weights': weights})
        solver.enable_signal_handler()
        
        solution = solver.Solution()
        solution_fitness = self.evaluate_single_solution(individual=solution)

        response = self.make_simplex_response(
            solution=solution,
            fitness=solution_fitness,
            evaluations=maxf
        )

    def make_simplex_response(self, solution, fitness, evaluations):
        """
        Generate response json of the NSGA algorithm
        """
        response = {}
        response['solutions'] = [
            {
                'fitness': list(fitness),
                'variables': list(solution),
                'objects': self.apply_individual(solution)
            }
        ]
        response['progess_log'] = self.progress_log
        response['generation'] = evaluations
        response['final'] = True
        
        response = json.dumps(response).encode()

        self.response_channel.basic_publish(
            exchange='',
            routing_key=self.response_queue,
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )

        return response


    def nsga_hybrid(self):

        ngen = self.request_data['optimization']['parameters']['ngen']
        pop_size = self.request_data['optimization']['parameters']['pop_size']
        mutpb = self.request_data['optimization']['parameters']['mutpb']
        cxpb = self.request_data['optimization']['parameters']['cxpb']
        mu = pop_size
        eta = self.request_data['optimization']['parameters']['eta']
        indpb = self.request_data['optimization']['parameters']['indpb']
        ncls = self.request_data['optimization']['parameters']['ncls']
        qbound = self.request_data['optimization']['parameters']['qbound']
        # diversity_flg = self.request_data['optimization']['parameters']['diversity_flg']
        diversity_flg = False

        creator.create(
            "Fitnessmulti", base.Fitness,
            weights=[i["weight"] for i in self.request_data["optimization"]["objectives"]]
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

        pop = self.toolbox.population(n=mu)
        pop = self.evaluate_population(pop=pop)
        # This is just to assign the crowding distance to the individuals
        # no actual selection is done
        pop = self.toolbox.select(pop, len(pop))
        response = self.make_ga_response(pop=pop, generation=0, final=False)

        # Begin the generational process
        for gen in range(1, ngen):
            offspring = self.generate_offspring(pop, cxpb, mutpb, mu)
            offspring = self.evaluate_population(pop=offspring)
            combined_pop = pop + offspring

            if diversity_flg:
                pop = self.check_diversity(combined_pop, ncls, qbound, mu)
            else:
                pop = self.toolbox.select(combined_pop, mu)
    
            print('Generating response for iteration No. {}'.format(gen))
            response = self.make_ga_response(pop=pop, generation=gen, final=gen==ngen-1)

        return response

    def make_ga_response(self, pop, generation, final):
        """
        Generate response json of the NSGA algorithm
        """
        response = {}
        response['solutions'] = []
        for individual in pop:
            response['solutions'].append(
                {
                    'fitness': list(individual.fitness.values),
                    'variables': list(individual),
                    'objects': self.apply_individual(individual)
                }
            )
        response['progess_log'] = self.progress_log
        response['generation'] = generation
        response['final'] = final
        
        response = json.dumps(response).encode()

        self.response_channel.basic_publish(
            exchange='',
            routing_key=self.response_queue,
            body=response,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )

        return response

    def generate_offspring(self, pop, cxpb, mutpb, mu):
        # Vary population. Taken from def varOr()
        offspring = []
        for _ in range(mu):
            op_choice = random.random()
            if op_choice < cxpb:            # Apply crossover
                ind1, ind2 = map(self.toolbox.clone, random.sample(pop, 2))
                ind1, ind2 = self.toolbox.mate(ind1, ind2)
                del ind1.fitness.values
                offspring.append(ind1)
            elif op_choice < cxpb + mutpb:  # Apply mutation
                ind = self.toolbox.clone(random.choice(pop))
                ind, = self.toolbox.mutate(ind)
                del ind.fitness.values
                offspring.append(ind)
            else:                           # Apply reproduction
                offspring.append(random.choice(pop))
        
        return offspring
    
    def check_diversity(self, pop, ncls, qbound, mu):

        Q_diversity, cluster_labels = self.project_and_cluster(n_clasters=ncls, pop=pop)
        if self.diversity_ref_point is None:
            self.diversity_ref_point = qbound * Q_diversity
    
        print('Performing clustering and diversity calculation...'.format(gen))
        
        if Q_diversity < Q_diversity_bound:
            print(' Q diversity index {} lower than boundary {}. Diversity will be enhanced...'.format(
                Q_diversity, self.diversity_ref_point
            ))

            pop = self.diversity_enhanced_selection(
                pop=pop, cluster_labels=cluster_labels,
                mu=mu, selection_method=self.toolbox.select
            )
        else:
            pop = self.toolbox.select(pop, mu)
        
        self.diversity_ref_point = qbound * Q_diversity

        return pop
    
    def calculate_hypervolume(self, pop):

        print('Calculating hypervolume...')

        if self.hypervolume_ref_point is None:
            fitness_array = np.array([i.fitness.values for i in pop])
            self.hypervolume_ref_point = np.max(fitness_array, 0)

        hv = hypervolume(pop, ref=self.hypervolume_ref_point)
        self.progress_log.append(hv)
        print('Hypervolume of the generation: {}'.format(self.progress_log[-1]))
    
    def evaluate_single_solution(self, individual, weights=None):
        """Returns scalar fitness if weghts, else vector fitness of a single individual"""
        loop = asyncio.get_event_loop()

        tasks = [
            loop.create_task(
                self.evaluate_async(individual, uuid.uuid4())
                )
        ]

        fitnesses = loop.run_until_complete(asyncio.gather(*tasks))
        fitness =fitness[0]
        if weights is not None:
            scalar_fitness = 0
            for value, weight in zip(fitness, weights):
                scalar_fitness += value * weight

            return scalar_fitness
        else:
            return fitness

    def evaluate_population(self, pop):
        # Create event loop
        loop = asyncio.get_event_loop()

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        tasks = [
            loop.create_task(
                self.evaluate_async(ind, uuid.uuid4())
                ) for ind in invalid_ind
        ]

        fitnesses = loop.run_until_complete(asyncio.gather(*tasks))

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        self.calculate_hypervolume(pop)

        return pop
    
    async def evaluate_async(self, individual, simulation_id):

        objects_data = self.apply_individual(
            individual = individual
        )

        request_data = {
            'simulation_id': simulation_id,
            'objects_data': objects_data,
            'optimization_id': self.optimization_id
        }

        print(" [x] Requesting fitness for individual {}".format(individual))

        connection = await connect_robust(
            host=self.host,
            port=self.port,
            login=self.login,
            password=self.password,
            virtualhost=self.virtualhost
        )
        channel = await connection.channel()

        rpc = await RPC.create(channel)

        response = await rpc.proxy.process(content=request_data)

        await connection.close()

        print(" [.] Received status code: {}, fitness: {}".format(response["status_code"], response["fitness"]))

        return tuple(response["fitness"])

    def apply_individual(self, individual):
        """Write individual values to variable template and return the filled template"""    
        for ind_value, keys in zip(individual, self.var_map):
            if keys[1] == 'concentration':
                for object_ in self.var_template:
                    if object_['id'] == keys[0]:
                        object_[keys[1]][keys[2]][keys[3]]['result'] = ind_value
                        break
            else:
                for object_ in self.var_template:
                    if object_['id'] == keys[0]:
                        object_[keys[1]][keys[2]]['result'] = ind_value
                        break
                    
        
        return self.var_template


    def read_optimitation_data(self):
        """
        Example of variables template, where values are fixed ones and Nones are optimized:
        
        Example of variables map and variables boundries:
        var_map = [(0, flux, 0), (0, concentration, 0),(0, position, row),(0, position, col)]
        var_bounds = [(0, 10), (0, 1),(0, 30),(0, 30)]
        """

        var_map = []
        var_bounds = []

        for object_ in self.var_template:
            for parameter, value in object_.items():
                if parameter == 'position':
                    for axis, axis_data in value.items():
                        if axis_data['min'] != axis_data['max']:
                            var_map.append((object_['id'], 'position', axis))
                            var_bounds.append((axis_data['min'], axis_data['max']))
                            object_['position'][axis]['result'] = None
                        else:
                            object_['position'][axis]['result'] = axis_data['min']

                elif parameter == 'flux':
                    for period, period_data in value.items():
                        if period_data['min'] != period_data['max']:
                            var_map.append((object_['id'], 'flux', period))
                            var_bounds.append((period_data['min'], period_data['max']))
                            object_['flux'][period]['result'] = None
                        else:
                            object_['flux'][period]['result'] = period_data['min']
                
                elif parameter == 'concentration':
                    for period, period_data in value.items():
                        for component, component_data in period_data.items():
                            if component_data['min'] != component_data['max']:
                                var_map.append((object_['id'], parameter, period, component))
                                var_bounds.append((component_data['min'], component_data['max']))
                                object_[parameter][period][component]['result'] = None
                            else:
                                object_[parameter][period][component]['result'] = component_data['min']
                    

        return var_map, var_bounds

    @staticmethod
    def make_candidate(bounds):
        """Generates random initial individual"""
        return [
            random.randint(value[0], value[1]) for value in bounds
        ]

    @staticmethod
    def project_and_cluster(n_clasters, pop):
        # Implementation of the Project And Cluster algorithm proposed by Syndhya et al.
        fitnesses = np.array([ind.fitness.values for ind in pop])
        fitnesses_reprojected = np.zeros(fitnesses.shape)
        maximals = np.max(fitnesses, axis=0)
        ws = maximals ** -1
        for i, fitness in enumerate(fitnesses):
            fitnesses_reprojected[i] = ((1-np.dot(ws, fitness))/np.dot(ws, ws)) * ws + fitness

        #Applying K-means clustering
        kmeans = KMeans(n_clusters=n_clasters, random_state=0).fit(fitnesses_reprojected)
        cluster_labels = kmeans.labels_
        centroids = kmeans.cluster_centers_

        #Calculating cluster diversity index
        Q_diversity = 0
        for cluster_label, centroid in zip(np.unique(cluster_labels), centroids):
            cluster_inds = [i for i, j in zip(pop, cluster_labels) if j == cluster_label]
            # print('Cluster inds of cluster '+str(cluster))
            # print(cluster_inds)
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

    @staticmethod
    def scalarization(fitness, reference_point, z_max, z_min):
        # Achevement Based Scalarization of a multidimensional fitness
        p = 10e-6 # augmentation coefficient
        w = [] # weight factors
        for i, j in zip(z_max, z_min):
            w.append(1 / (i - j))
        
        vector = []

        for i, j, k in zip(fitness, reference_point, w):
            vector.append(
                k * (i - j)
            )
        vector_augemnted = [i + p * sum(vector) for i in vector]
        scalar = max(vector_augemnted)

        return scalar