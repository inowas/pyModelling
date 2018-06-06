import random
import json
import numpy as np
import scipy
from multiprocessing import Pool, current_process
# from mystic.solvers import fmin, NelderMeadSimplexSolver
# from mystic.monitors import Monitor
# from mystic.termination import CandidateRelativeTolerance as CRT

from sklearn.cluster import KMeans
from deap import base
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools
import copy
import asyncio

from InowasOptimization.OptimizationObjects import OptWell
from InowasOptimization.rabbitmq_evaluation_rcp_client import EvaluationRpcClient


class Optimization(object):
    """
    Optimization class

    """
    evaluation_rcp_client = EvaluationRpcClient

    def __init__(self, request_data):

        self.request_data = request_data
        self.objects, self.objects_map, self.bounds = self.read_optimitation_data(request_data["optimization"])

    def nsga_hybrid(self):

        NGEN = self.request_data['optimization']['parameters']['ngen']
        POP_SIZE = self.request_data['optimization']['parameters']['pop_size']
        MUTPB = self.request_data['optimization']['parameters']['mutpb']
        CXPB = self.request_data['optimization']['parameters']['cxpb']
        MU = POP_SIZE
        ETA = self.request_data['optimization']['parameters']['eta']
        INDPB = self.request_data['optimization']['parameters']['indpb']
        NCLS = self.request_data['optimization']['parameters']['ncls']
        NLOCAL = self.request_data['optimization']['parameters']['nlocal']
        QBOUND = self.request_data['optimization']['parameters']['qbound']
        REFPOINT = self.request_data['optimization']['parameters']['refpoint']
        MAXF = self.request_data['optimization']['parameters']['maxf']

        creator.create(
            "FitnessMulti", base.Fitness,
            weights=[i["weight"] for i in self.request_data["optimization"]["objectives"]]
        )
        creator.create("Individual", list, fitness=creator.FitnessMulti)
        toolbox = base.Toolbox()
        toolbox.register("candidate", self.make_candidate, self.bounds)
        # toolbox.register("evaluate", self.evaluate_async)
        toolbox.register(
            "mutate", tools.mutPolynomialBounded,
            low=[i[0] for i in self.bounds], up=[i[1] for i in self.bounds],
            eta=ETA, indpb=INDPB
        )
        toolbox.register(
            "mate", tools.cxSimulatedBinaryBounded,
            low=[i[0] for i in self.bounds], up=[i[1] for i in self.bounds],
            eta=ETA
        )
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.candidate)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("select", tools.selNSGA2)

        # stats paramters
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        # stats.register("hypervolume", np.max, axis=0)
        
        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"
        hypervolume_log = []

        pop = toolbox.population(n=MU)

        # Create event loop
        loop = asyncio.get_event_loop()

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]

        tasks = [
            loop.create_task(
                self.evaluate_async(loop, ind, 0, idx)
                ) for idx, ind in enumerate(invalid_ind)
        ]

        fitnesses = loop.run_until_complete(asyncio.gather(*tasks))
        print(fitnesses)

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # This is just to assign the crowding distance to the individuals
        # no actual selection is done
        pop = toolbox.select(pop, len(pop))
        # Calculating initial diversity boundary
        Q_diversity, cluster_labels = self.project_and_cluster(n_clasters=NCLS, pop=pop)
        Q_diversity_bound = QBOUND * Q_diversity
        
        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(invalid_ind), **record)
        print(logbook.stream)

        # Begin the generational process
        for gen in range(1, NGEN):
            # Vary population. From def varOr()
            offspring = []
            for _ in range(MU):
                op_choice = random.random()
                if op_choice < CXPB:            # Apply crossover
                    ind1, ind2 = map(toolbox.clone, random.sample(pop, 2))
                    try:
                        ind1, ind2 = toolbox.mate(ind1, ind2)
                    except TypeError:
                        raise
                    del ind1.fitness.values
                    offspring.append(ind1)
                elif op_choice < CXPB + MUTPB:  # Apply mutation
                    ind = toolbox.clone(random.choice(pop))
                    ind, = toolbox.mutate(ind)
                    del ind.fitness.values
                    offspring.append(ind)
                else:                           # Apply reproduction
                    offspring.append(random.choice(pop))

            
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            # fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

            tasks = [
                loop.create_task(
                    self.evaluate_async(loop, ind, gen, idx)
                    ) for idx, ind in enumerate(invalid_ind)
            ]

            fitnesses = loop.run_until_complete(asyncio.gather(*tasks))
            print(fitnesses)


            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            combined_pop = pop + offspring
            
            print('Generation: {0}. Performing clustering and diversity evaluation...'.format(gen))
            
            # Check diversity and perform clustering
            
            Q_diversity, cluster_labels = self.project_and_cluster(n_clasters=NCLS, pop=combined_pop)
            print('Generation: {0}. Q diversity index: {1}'.format(gen, Q_diversity))
            
            # Select the next generation population after checking diversity of the population
          
            if Q_diversity < Q_diversity_bound:
                print('Generation: {0}. Q diversity index {1} lower than boundary {2}. Diversity will be enhanced...'.format(
                    gen, Q_diversity, Q_diversity_bound
                ))

                pop = diversity_enhanced_selection(
                    pop=combined_pop, cluster_labels=cluster_labels,
                    mu=MU, selection_method=toolbox.select
                )
            else:
                pop = toolbox.select(combined_pop, MU)
            
            Q_diversity_bound = QBOUND * Q_diversity

            print('Generation: {0}. Calculating hypervolume...'.format(gen))
            if gen == 1:
                fitness_array = np.array([i.fitness.values for i in pop])
                reference_point = np.max(fitness_array, 0)
                print('Generation: {0}. Hypervolume reference point is {1}'.format(gen, reference_point))
            hv = hypervolume(pop, ref=reference_point)
            hypervolume_log.append(hv)
            print('Generation: {0}. Hypervolume of the generation  {1}'.format(gen, hypervolume_log[-1]))
            
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            print(logbook.stream)

            # print('Generation: {0}. Performing local search...'.format(str(gen)))
            # Perform local search
            # pop = local_search_internal(
            #     evaluate_func=evaluate,
            #     scalar_func=scalarization,
            #     pop=pop,
            #     reference_point=REFPOINT,
            #     bounds=BOUNDS, maxf=MAXF,
            #     n_local=NLOCAL, cluster_labels=None
            # )

            print('Generation: {0}. Checkng termination criteria...'.format(gen))
            # Check termination criteria
            termination_criteria = False
            if termination_criteria:
                return pop, logbook, hypervolume_log
        
        return pop, logbook, hypervolume_log
    
    async def evaluate_async(self, loop, individual, gen_id, ind_id):

        request_data_copy = copy.deepcopy(self.request_data)
        individual = np.array(individual)
        unique_objects = np.unique(self.objects_map)

        for idx in unique_objects:
            individual_idx = individual[self.objects_map == idx]
            request_data_copy = self.objects[idx].update_data(request_data_copy, individual_idx)
        
        request_data_copy['gen_id'] = gen_id
        request_data_copy['ind_id'] = ind_id

        print(" [x] Requesting fitness for individual {}".format(individual))
        client = self.evaluation_rcp_client(loop)

        rpc = await client.connect()
        response = await rpc.call(request_data_copy)
        response = json.loads(response.decode())

        print(" [.] Received status code: {}, fitness: {}".format(response["status_code"], response["fitness"]))

        return tuple(response["fitness"])

    # def evaluate(self, individual):
    #     request_data_copy = copy.deepcopy(self.request_data)
    #     individual = np.array(individual)
    #     unique_objects = np.unique(self.objects_map)

    #     for idx in unique_objects:
    #         individual_idx = individual[self.objects_map == idx]
    #         self.opt_objects[idx].update_packages(request_data_copy, individual_idx)

    #     optimization_rpc = self.evaluation_rcp_client_class()
    #     response = self.evaluation_rcp_client_object().call(request_data_copy)
    #     response = json.loads(response)
    #     fitness = response["fitness"]
        
    #     return tuple(fitness)

    # def evaluate_pop(self, individuals):
    #     request_data_copy = copy.deepcopy(self.request_data)
    #     unique_objects = np.unique(self.objects_map)
    #     requests = []

    #     for ind in individuals:
    #         individual = np.array(ind)

    #         for idx in unique_objects:
    #             individual_idx = individual[self.objects_map == idx]
    #             self.opt_objects[idx].update_packages(request_data_copy, individual_idx)

    #         optimization_rpc = self.evaluation_rcp_client_class()
    #         response = self.evaluation_rcp_client_object().call(request_data_copy)
    #         response = json.loads(response)
    #         fitness = response["fitness"]
        
    #     return tuple(fitness)

    @staticmethod
    def read_optimitation_data(request_data):

        objects = {}
        objects_map = []
        bounds = []

        for obj in request_data['objects']:
            for key, value in obj.items():
                if key == 'position':
                    for k, v in value.items():
                        if k != 'multiplier':
                            if v[0] != v[1]:
                                bounds.append(
                                    (v[0], v[1])
                                )
                                objects_map.append(obj['id'])

                elif key == 'flux':
                    for k, v in value.items():
                        if k != 'multiplier':
                            if v[0] != v[1]:
                                bounds.append(
                                    (v[0], v[1])
                                )
                                objects_map.append(obj['id'])
                    
                elif key == 'concentration':
                    for k, v in value.items():
                        if k != 'multiplier':
                            for i in v:
                                if i[0] != i[1]:
                                    bounds.append(
                                        (i[0], i[1])
                                    )
                                    objects_map.append(obj['id'])

            if obj['type'] == 'well':
                objects[obj['id']] = OptWell(obj)

        return objects, objects_map, bounds

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
    def local_search_internal(evaluate_func, scalar_func, pop, reference_point, bounds, maxf, n_local=1, cluster_labels=None):
        # Local search algorithm SLSQP with Achievement Based Sclarization
        fitness_array = np.array([i.fitness.values for i in pop])
        z_max = np.max(fitness_array, 0)
        z_min = np.min(fitness_array, 0)

        def evaluate_func_scalar(individual, evaluate_func=evaluate_func, scalar_func=scalar_func, reference_point=reference_point, z_max=z_max, z_min=z_min):
            fitness = evaluate_func(individual)
            scalar_fitness = scalar_func(fitness, reference_point, z_max, z_min)
            print('Individual: ')
            print(str(individual))
            print('Scalar fitness: ' + str(scalar_fitness))

            return scalar_fitness

        for _ in range(n_local):
            random_individual = random.choice(pop)
            initial_guess = random_individual[:]
            print('Local Optimization: ')
            print('Randomly selected individual: ' + str(random_individual))
            print('Initial fitness: ' + str(random_individual.fitness.values))

            stepmon = Monitor()
            evalmon = Monitor()
            solver = NelderMeadSimplexSolver(len(initial_guess))
            solver.SetInitialPoints(initial_guess)
            solver.SetEvaluationMonitor(evalmon)
            solver.SetGenerationMonitor(stepmon)
            solver.SetStrictRanges([i[0] for i in bounds], [i[1] for i in bounds])
            solver.SetEvaluationLimits(evaluations=maxf)
            solver.SetGenerationMonitor(stepmon)
            solver.enable_signal_handler()
            solver.SetTermination(CRT())
            solver.enable_signal_handler()
            solver.Solve(evaluate_func_scalar)
            solution = solver.Solution()
            print('Local Solution:')
            print(solution)
            # result = scipy.optimize.minimize(
            #     fun=evaluate_func_scalar,
            #     x0=initial_guess,
            #     args=(evaluate_func, scalar_func, reference_point, z_max, z_min),
            #     method='SLSQP',
            #     bounds=bounds,
            #     options={'disp': True, 'maxiter': 7, 'eps': 5}
            # )

            # result = scipy.optimize.minimize(
            #     fun=evaluate_func_scalar,
            #     x0=initial_guess,
            #     args=(evaluate_func, scalar_func, reference_point, z_max, z_min),
            #     method='L-BFGS-B',
            #     bounds=bounds,
            #     options={'disp': True, 'maxfun': maxf, 'eps': 1}
            # )
            # result = scipy.optimize.minimize(
            #     fun=evaluate_func_scalar,
            #     x0=initial_guess,
            #     args=(evaluate_func, scalar_func, reference_point, z_max, z_min),
            #     method='Nelder-Mead',
            #     options={'disp': True, 'maxfev': maxf}
            # )
            # results = [float(i) for i in result.x]
            # results_corrected = []
            # for res, bound in zip(results, bounds):
            #     if res > bound[1]:
            #         results_corrected.append(bound[1])
            #     elif res < bound[0]:
            #         results_corrected.append(bound[0])
            #     else:
            #         results_corrected.append(res)

            random_individual[:] = solution
            random_individual.fitness.values = evaluate_func(random_individual)

            print('Locally optimized individual: ' + str(random_individual))
            print('Locally optimized fitness: ' + str(random_individual.fitness.values))

        return pop

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