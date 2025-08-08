from functools import reduce
import random
import pygad
import numpy as np
from chromosome import Chromosome

# https://chat.cborg.lbl.gov/c/14738910-0178-4da7-be92-69a815a9736c

class Optimizer(object):
    """
    Optimizer class to manage the genetic algorithm for optimizing item 
    combinations for a Dofus character.
    This class initializes the character, items, item sets, and pools of 
    items by type.
    It also initializes the genetic algorithm instance and provides methods 
    to optimize the item combinations.
    """
    def __init__(self,
                  character,
                    items,
                      item_sets, 
                      **config):
        self.config = config
        self.character = character
        # Load data from CSV files        
        self.items = {k:v for k,v in items.items() if self._is_item_valid(v)}
        self.item_sets = {k:v for k,v in item_sets.items() \
                          if set(v["items"]) & set(self.items.keys())}  # Filter item sets to only include valid items

        # Create pools of items by type
        # Pools of items by type
        self.pool_types = [
            (1, 1),
            (2, 1),
            (3, 2), # Ring
            (4, 1),
            (5, 1),
            (7, 1),
            (10,1),
            (11, 1),
            ([12,27], 1), # Pet/Mount
            (13, 6), # Dofus
        ]
        self.initial_population = None
        # Initialize pools of items by type
        self._initialize_pools()
        print(f"Total items: {len(self.items)}")
        print(f"Total item sets: {len(self.item_sets)}")
        print(f"Total pools:\n   {len(self.pools)} with sizes {[len(pool) for pool in self.pools]}")
        print(f"Total combinations: 10^{np.log10(float(reduce(lambda x,y: x*y, [len(pool) for pool in self.pools]))):.2f}")

    def _initialize_pools(self):
        """
        Initialize the mapping of slots to pool types.
        """
        # TODO: Allow addition of one defined chromosome (e.g. current set)
        self.slot_to_pool_type = {}
        self.pools = []
        inclusions = self.config.get("inclusions", {}).get("items", [])[:]
        slot = 0
        self.forced_slots = {}
        for t,count in self.pool_types:
            if not isinstance(t, list):
                t = [t]
            for _ in range(count):
                pool = [id for id in self.items if self.items[id]["type"]["superTypeId"] in t]
                pool_inclusions = set(pool) & set(inclusions)
                if pool_inclusions:
                    # If there are inclusions, add one
                    inclusion = next(iter(pool_inclusions), None)
                    assert inclusion is not None, "Inclusion cannot be None"
                    pool = [inclusion]
                    # Remove the inclusion from the list
                    inclusions.remove(inclusion)
                    self.forced_slots[slot] = inclusion
                self.pools.append(pool)
                slot += 1
                self.slot_to_pool_type[len(self.slot_to_pool_type)] = t
        self.NUM_TYPES = len(self.pools)

    def _initialize_population_from_sets(self):
        """
        Initialize the population from item sets.
        Each item set will be represented by a chromosome that contains items from the set.
        The chromosome will be filled with items from the pools based on the item set's items.
        If an item from the set is not available in the pools, a random item from the pool will be used.
        This ensures that the initial population is diverse and contains valid item combinations.
        """
        #TODO: Make sure that the set chromosomes are valid.
        #NOTE: Creating a chromosome to check penalties is super slow, something quicker?
        initial_population = []
        for s in self.item_sets.values():
            chromosome = [None] * len(self.pools)
            seen_items = set()
            for slot, types in self.slot_to_pool_type.items():
                if slot in self.forced_slots:
                    # If the slot is forced, use the forced item
                    set_item = self.forced_slots[slot]
                else:
                    # Otherwise, try to find an item from the set that matches the slot type
                    if not isinstance(types, list):
                        types = [types]
                    # Filter items in the set that match the slot type
                    iterator = iter(i for i in s["items"] \
                                    if i in self.items \
                                    and self.items[i]["type"]["superTypeId"] in types \
                                    and i not in seen_items)
                    set_item = next(iterator, None)
                seen_items.add(set_item)
                if not set_item:
                    set_item = random.choice(self.pools[slot])
                chromosome[slot] = set_item
                    
            initial_population.append(chromosome)

        while len(initial_population) < self.config["population_size"]:
            chrom = [random.choice(self.pools[i]) for i in range(len(self.pools))]
            initial_population.append(chrom)
        return initial_population
    
    def _is_item_valid(self, item):
        """
        Check if an item is valid based on the character's level and exclusions.

        An item is valid if:
        - It is not in the exclusions list.
        - Its level is less than or equal to the character's level.
        - If it is a pet, dofus, or mount, it can be low level
        - If it is not a pet, dofus, or mount, its level plus the level 
        offset is less than or equal to the character's level.
        """
        if item["ankama_id"] in self.config["exclusions"]["items"]:
            return False
        if item["level"] > self.character.level:
            return False
        if "type" in item and \
            item["type"]["superTypeId"] in [12, 13, 27]: # Pet, Dofus, Mount
            # Only pets can be low level
            return True
        if item["level"] + self.config["level_offset"] < self.character.level:
            # Item is too low level for the character
            return False
        return True
    
    def fitness(self,ga_instance,chromosome,chromosome_idx):
        """
        Fitness function for the genetic algorithm.

        It calculates the fitness of a chromosome based on the character's totals and preferences.
        The fitness is calculated by creating a Chromosome instance with the given chromosome,
        and then calling its fitness method.

        The fitness function returns the fitness value of the chromosome.
        If the chromosome is not viable, it returns a very low fitness value to penalize it
        """
        return Chromosome(chromosome,
                          self).fitness

    def initialize(self):
        """
        Initialize the genetic algorithm instance with the given configuration.
        The configuration includes the number of generations, population size,
        number of parents mating, parent selection type, crossover rate, mutation rate,
        and tournament size.

        The genetic algorithm instance is created using the pygad library."""
        # Initialize the population
        initial_population = self._initialize_population_from_sets()
        self.ga_instance = pygad.GA(
            num_generations=self.config["num_generations"],
            num_parents_mating=self.config["num_parents_mating"],
            sol_per_pop=self.config["population_size"],
            num_genes=len(self.pools),
            fitness_func=self.fitness,
            gene_type=int,
            gene_space=self.pools,
            parent_selection_type=self.config["parent_selection_type"],
            K_tournament=self.config.get("tournament_size", 3),
            crossover_probability=self.config["crossover_rate"],
            mutation_probability=self.config["mutation_rate"],
            keep_elitism=2,
            initial_population=initial_population,
        )

    def run_ga(self, island=None):
        # Initialize the genetic algorithm instance
        self.initialize()
        
        # Run the GA
        self.ga_instance.run()
        
        # Get the best solution
        best_solution, best_solution_fitness, _ = self.ga_instance.best_solution()

        solution = Chromosome(
                          best_solution,
                          optimizer=self)
        solution.best_solutions_fitness = self.ga_instance.best_solutions_fitness
        solution.best_solutions = self.ga_instance.best_solutions
        return solution

    def optimize(self, islands = None, max_workers = 1):
        # TODO: Implement island optimization
        """
        Run the genetic algorithm to optimize the item combinations.

        The optimization process involves running the genetic algorithm instance,
        which will evolve the population over the specified number of generations.
        After the optimization, the best solution is extracted from the genetic algorithm instance,
        and a Chromosome instance is created with the best solution.

        The best solution contains the items and item sets that yield the highest fitness value."""

        if islands:
            # TODO: Implement island optimization
            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(self.run_ga, range(islands)))
                return results
        return self.run_ga()

