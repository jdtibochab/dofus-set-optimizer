import pandas as pd
from functools import reduce
import json
import random
from tqdm import tqdm
import pygad
import numpy as np
from copy import copy
# https://chat.cborg.lbl.gov/c/14738910-0178-4da7-be92-69a815a9736c

elements = [
    36, # Agility,
    22, # Chance
    13, # Intelligence
    45, # Strength
    9, # Vitality
    10, # Wisdom
]

# TODO: Implement damage in best element flag (248)
damage_mapper = {
        # Damage
            189 : 36, # Air,
            214 : 22, # Water
            198 : 13, # Fire
            194 : 45, # Earth
            195 : 45, # Neutral (by earth)
        # Steal
            224 : 36, # Air,
            203 : 22, # Water
            193 : 13, # Fire
            221 : 45, # Earth
            223 : 45, # Neutral
        }
bonus_damage_mapper = {
        # Damage
            189 : 47, # Air,
            214 : 27, # Water
            198 : 61, # Fire
            194 : 48, # Earth
            195 : 49, # Neutral
        # Steal
            224 : 47, # Air,
            203 : 27, # Water
            193 : 61, # Fire
            221 : 48, # Earth
            223 : 49, # Neutral
    }

default_soft_caps = {
    9: [0,None, 0, 0, 0, 0], # Vitality
    10: [0, 0, 0, None, 0, 0], # Wisdom
    45: [0, 100, 200, 300, None, 0], # Strength
    13: [0, 100, 200, 300, None, 0], # Intelligence
    22: [0, 100, 200, 300, None, 0], # Chance
    36: [0, 100, 200, 300, None, 0]  # Agility
}

# Filters
def get_item_contribution(item):
    # Get the effects of the item
    item_effects = item["effects"]
    if not item_effects:
        return {}
    contributions = {}
    for d in item_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
    if item["type"]["superTypeId"] == 27: # Weapon
        contributions[212] = 1
    return contributions

def get_set_contribution(item_set,overlap):
    set_effects = item_set["effects"][str(overlap)]
    contributions = {}
    for d in set_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
    # Add to set bonus
    contributions[72] = overlap - 1
    return contributions

def get_weapon_damage(weapon):
    if not weapon["effects"]:
        return {}
    damage_effects = [d for d in weapon["effects"] if d["active"]]
    if not damage_effects:
        return {}
    contributions = {}
    for d in damage_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
    return contributions

def get_item_set(item, item_sets):
    if not item["hasParentSet"]:
        return None
    return item_sets[item["parentSet"]["id"]]

class Character(object):
    """
    Character class to represent a Dofus character with stats and level.
    This class is used to initialize the character's stats based on the level and
    distribute points across different elements.
    It also allows for the distribution of points based on a configuration dictionary.
    """
    def __init__(self, level, **config):
        self.stats = {}
        self.level = level
        self.scrolled = config.get("scrolled", False)
        self.exo = config.get("exo", {})
        self.elements = config.get("elements", elements[:4])
        if config.get("distributed_points"):
            for k,v in config["distributed_points"].items():
                self._distribute_points(k, v)
        else:
            self._auto_distribute_points()
        self._update_stats()

    def _distribute_points(self, element_id, points):
        if element_id not in self.stats:
            self.stats[element_id] = 0
        soft_cap = default_soft_caps.get(element_id, [None] * 5)
        for i in range(len(soft_cap)):
            if points < 1:
                # Not enough points to distribute
                break
            lower_bound, upper_bound = soft_cap[i],soft_cap[i+1]
            if upper_bound is None:
                upper_bound = float('inf')
            distribute = min((upper_bound - lower_bound), points)
            add = distribute // (i + 1)
            if add < 1:
                # Not enough points to distribute
                break
            self.stats[element_id] += add
            points -= distribute

    def _auto_distribute_points(self):
        points_to_distribute = (self.level - 1) * 5
        per_element = points_to_distribute // len(self.elements)
        # Distribute points based on soft caps
        for element_id in self.elements:
            per_element_residual = copy(per_element)
            self._distribute_points(element_id, per_element_residual)

    def _update_stats(self):
        if 9 not in self.stats:
            self.stats[9] = 0
        self.stats[9] += 55 + (self.level - 1) * 5
        self.stats[12] = 7 if self.level > 99 else 6
        self.stats[8] = 3
        self.stats[252] = 1 # Subscribed

        if self.scrolled:
            for i in elements:
                if i not in self.stats:
                    self.stats[i] = 100
                else:
                    self.stats[i] += 100
            
        for k,v in self.exo.items():
            if k not in self.stats:
                self.stats[k] = 0
            self.stats[k] += v
        pass

class Chromosome(object):
    """
    Chromosome class to represent a set of items for a Dofus character.
    This class is used to calculate the fitness of a chromosome based on
    the character's stats, item contributions, and set contributions.
    It also checks if the conditions for items and sets are met, and
    calculates the totals, final elemental damage, and final weapon damage.
    """
    def __init__(self,
                 chromosome, 
                 optimizer):
        
        # Initialize the chromosome with a character, items, item sets and a chromosome
        self.chromosome = chromosome
        self.optimizer = optimizer
        self.character = optimizer.character
        self.preferences = optimizer.config["preferences"]
        self.elements = optimizer.config["elements"]
        self.objective = optimizer.config["objective"]
        self.viable = True
        self.penalized = False

        # Get the items and item sets of the chromosome
        self.items = [optimizer.items[i] for i in self.chromosome]
        self.item_sets = [v for k,v in optimizer.item_sets.items() \
                    if set(v["items"]) & set([i["ankama_id"] for i in self.items])] # Filter item sets to only include valid items

        # Get the item contributions
        self.item_contributions = self.get_item_contributions()
        # Get the set contributions
        self.set_contributions = self.get_set_contributions()

        # Get the weapon
        self.weapon = self.get_weapon()

        # Get the totals, damage and fitness
        self.totals = self.get_totals()
        self.fitness = self.get_fitness()

    def get_weapon(self):
        """
        Get the weapon from the chromosome.
        """
        return next(i for i in self.items if i["type"]["superTypeId"] == 2)
    
    def get_item_contributions(self):
        """
        Get the contributions of the items in the chromosome.
        
        The contributions are calculated based on the effects of the items.
        
        Each item contributes to the totals based on its effects.
        """
        # Item contributions
        lst = [get_item_contribution(item) for item in self.items]
        return pd.DataFrame(lst).sum(axis=0).to_dict()
    
    def get_set_contributions(self):
        """
        Get the contributions of the item sets in the chromosome.
        
        The contributions are calculated based on the overlap of items 
        in the item sets.
        
        Each item set contributes to the totals based on the number of 
        items it has in the chromosome.
        
        The contributions are returned as a dictionary."""
        # Set effects contributions
        lst = []
        seen_sets = set()
        for item_set in self.item_sets:
            if item_set["ankama_id"] in seen_sets:
                continue
            seen_sets.add(item_set["ankama_id"])
            overlap = len(set([i["ankama_id"] for i in self.items]) & set(item_set["items"]))
            lst.append(get_set_contribution(item_set, overlap))
        return pd.DataFrame(lst).sum(axis=0).to_dict()

    def is_condition_met(self, condition):
        """
        Check if a condition is met based on the character's totals.
        """
        total_value = self.totals.get(condition["element_id"], 0)
        condition_value = condition["value"]
        operator = condition["operator"]
        if operator == "<":
            return total_value < condition_value
        elif operator == ">":
            return total_value > condition_value
        elif operator == "=":
            return total_value == condition_value
        else:
            # return NotImplementedError(f"Unknown operator: {operator}")
            return True
        
    def are_nested_conditions_met(self, conditions):
        """
        Check if nested conditions are met based on the character's totals.
        """
        if conditions["children"] is None:
            flag = self.is_condition_met(conditions["value"])
            return flag
        else:
            flags = []
            for condition in conditions["children"]:
                flags.append(self.are_nested_conditions_met(condition))
            if conditions["relation"] == "and":
                return all(flags)
            elif conditions["relation"] == "or":
                return any(flags)
            else:
                raise NotImplementedError(f"Unknown relation: {conditions['relation']}")

    def are_item_conditions_met(self, item):
        """
        Check if the item conditions are met based on the character's totals.
        """
        conditions = item["conditions"]
        if not conditions:
            return True  # No conditions, always met
        if not conditions["children"]:
            condition = conditions["value"]
            return self.is_condition_met(condition)
        else:
            return self.are_nested_conditions_met(conditions)
    
    def get_totals(self):
        """
        Get the totals of the chromosome based on the character's stats, item contributions, and set contributions.
        
        The totals are calculated by summing the character's stats, item contributions, and set contributions.
        
        The totals are returned as a dictionary."""
        # Get the character stats
        character_contributions = self.character.stats.copy()
        return pd.DataFrame(
            [character_contributions,
              self.item_contributions,
                self.set_contributions]).sum(axis=0).to_dict()

    def get_final_elemental_damage(self):
        """
        Calculate the final elemental damage based on the character's totals and item contributions.
        
        The damage is calculated based on the character's stats, item contributions,
        and the expected critical hit bonus and probability.
        
        The damage is calculated for each element in the damage mapper.
        """
        power = self.totals.get(32,0)
        base_crit_chance = self.totals.get(29,0)
        base_crit_added_damage = self.totals.get(38,0)
        spell_damage = 20 # Default spell damage
        crit_bonus = 5 # Default crit bonus
        spell_crit_chance = 25 # Default spell crit chance
        
        # Critical hit logic
        if 29 in self.optimizer.config.get("preferences",{"lower":{}}).get("lower"):
            crit_chance = max(min(spell_crit_chance + base_crit_chance,100), 0)  # Ensure crit_chance is between 0 and 100
        else:
            # Do not use crit to prioritize items
            crit_chance = 0
        expected_crit_bonus = max(crit_bonus * crit_chance/100, 0) # Expected value of distribution
        expected_crit_added_damage = max(base_crit_added_damage * crit_chance/100, 0) # Expected value of distribution

        # Calculate total damage
        damage = 0
        seen_stats = []
        for element_id, stat in damage_mapper.items():
            if stat in seen_stats:
                # Skip stats that have already been processed
                continue
            seen_stats.append(stat)
            if stat not in self.elements:
                continue
            # Get the stat and base damage
            stat_base = self.totals.get(stat,0)

            # Get the added bonus damage from the stat
            bonus_damage_id = bonus_damage_mapper[element_id]
            added_bonus = self.totals.get(bonus_damage_id, 0)
            # TODO: Set a default damage value per class, spell average?
            damage += (spell_damage + expected_crit_bonus)*(1+(stat_base + power)/100) + expected_crit_added_damage + added_bonus
        return damage

    def get_final_weapon_damage(self):
        """
        Calculate the final weapon damage based on the character's totals and weapon stats.
        
        The damage is calculated based on the weapon's base damage, critical hit bonus,
        critical hit probability, and the character's stats.
        
        The damage is calculated for each element in the weapon's damage effects.
        
        The final damage is the sum of the damage for each element.
        """
        # totals = self.get_totals(chromosome)
        # Character stats
        power = self.totals.get(32,0)
        base_crit_chance = self.totals.get(29,0)
        base_crit_added_damage = self.totals.get(38,0)
        weapon_damage = get_weapon_damage(self.weapon)

        # Critical hit logic
        crit_bonus = self.weapon["criticalHitBonus"] \
            if not pd.isna(self.weapon["criticalHitBonus"]) else 0
        weapon_crit_chance = self.weapon["criticalHitProbability"] \
            if not pd.isna(self.weapon["criticalHitProbability"]) else 0
        crit_chance = max(min(weapon_crit_chance + base_crit_chance,100), 0)  # Ensure crit_chance is between 0 and 100
        expected_crit_bonus = max(crit_bonus * crit_chance/100, 0) # Expected value of distribution
        expected_crit_added_damage = max(base_crit_added_damage * crit_chance/100, 0) # Expected value of distribution

        # Calculate total damage
        damage = 0
        for element_id,weapon_base_damage in weapon_damage.items():
            # Get the stat and base damage
            if element_id not in damage_mapper:
                continue
            stat = damage_mapper[element_id]
            if stat not in self.elements:
                # Skip elements not in the selected elements
                continue
            stat_base = self.totals.get(stat,0)

            # Get the added bonus damage from the stat
            bonus_damage_id = bonus_damage_mapper[element_id]
            added_bonus = self.totals.get(bonus_damage_id, 0)
            damage += (weapon_base_damage + expected_crit_bonus) * (1+(stat_base+power)/100) + expected_crit_added_damage + added_bonus
        return damage
    
    def _get_offset(self, element, preference, bound_type):
        """
        Calculate the offset for a given element based on the preference and bound type.
        """
        target = preference["target"]
        current = self.totals.get(element, 0)
        if bound_type == "lower":
            return max(target - current, 0)/target
        else:
            return max(current - target, 0)/target

    def _get_preference_penalty(self, preferences):
        """
        Enforce the preferences on the fitness value.
        """
        penalty = 1
        for bound_type, type_preferences in preferences.items():
            for element, preference in type_preferences.items():
                strength = preference["strength"]
                offset = self._get_offset(element, preference, bound_type)
                if offset:
                    # Penalize and also continuously reduce the fitness
                    penalty *= (1 - strength) * (1 - offset)
                    self.penalized = True
        return penalty
        
    def penalize(self, fitness):
        """
        Penalize the fitness value based on the chromosome's viability and preferences.
        
        The fitness is penalized if the chromosome is not viable or if the preferences are not met.
        
        The penalties are applied as follows:
        - If the chromosome is not viable, the fitness is multiplied by 0.1.
        - If there are duplicated dofus or trophies, the fitness is multiplied by 0.1.
        - If there are duplicated rings, the fitness is multiplied by 0.1.
        - If any item does not meet its conditions, the fitness is multiplied by 0.1.
        - The preferences are applied as a penalty factor, which is multiplied to the fitness.
        """
        # Duplicated dofus and trophies
        duplicates = len(self.chromosome[-6:]) - len(set(self.chromosome[-6:]))
        for _ in range(duplicates):
            # Penalty per duplicated dofus or trophy
            fitness *= 0.1
            # Mark as non-viable
            self.viable = False
            self.penalized = True

        if len(set(self.chromosome[2:4])) < 2:
            # Arbitrary penalty for duplicated rings
            fitness *= 0.1
            # Mark as non-viable
            self.viable = False
            self.penalized = True

        for item in self.items:
            if not self.are_item_conditions_met(item):
                # Penalize for items that do not meet the conditions
                fitness *= 0.1
                # Mark as non-viable
                self.viable = False
                self.penalized = True
                
        # Penalizations for preferences
        penalty = self._get_preference_penalty(self.preferences)
        return fitness * penalty

    def get_fitness(self):
        """
        Get the fitness of the chromosome based on the objective.
        The fitness is calculated based on the objective type, which
        can be either "weapon" or "elements".
        """
        type = self.objective
        if type == "weapon":
            fitness = self.get_final_weapon_damage()
        elif type == "elements":
            fitness = self.get_final_elemental_damage()
        return self.penalize(fitness)
    
    def totals_summary(self,item_descriptions={}):
        """
        Get a summary of the totals of the chromosome.

        The summary includes the item type, description, and value.
        """
        language = self.optimizer.config.get("language", "en")
        dct = {}
        for k,v in self.totals.items():
            if k not in item_descriptions:
                description = None
            else:
                description = item_descriptions[k][language]
            dct[k] = {
                "description": description,
                "value": v
            }
        return pd.DataFrame.from_dict(dct, orient='index').sort_index()
    
    def set_summary(self):
        """
        Get a summary of the items in the chromosome.
        
        The summary includes the item type, description, level, and set name.

        The set name is only included if the item belongs to a set.

        The summary is returned as a pandas DataFrame.
        """

        language = self.optimizer.config.get("language", "en")
        dct = {}
        for item in self.items:
            item_set = get_item_set(item, {k["ankama_id"]: k for k in self.item_sets})
            dct[item["ankama_id"]] = {
                "type_id": item["type"]["superTypeId"],
                "type": item["type"]["name"][language],
                "description": item["name"][language],
                "level": item["level"],
                "set": item_set["name"][language] if item_set else None,
            }
        return pd.DataFrame.from_dict(dct, orient='index').sort_index()

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
        # Initialize pools of items by type
        self._initialize_pools()
        # Initialize the population
        self._initialize_population_from_sets()
        print(f"Total items: {len(self.items)}")
        print(f"Total item sets: {len(self.item_sets)}")
        print(f"Total pools:\n   {len(self.pools)} with sizes {[len(pool) for pool in self.pools]}")
        print(f"Total combinations: 10^{np.log10(float(reduce(lambda x,y: x*y, [len(pool) for pool in self.pools]))):.2f}")
        # Initialize the genetic algorithm instance
        self.initialize()

    def _initialize_pools(self):
        """
        Initialize the mapping of slots to pool types.
        """
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
        #TODO: Make sure that the set chromosomes are valid
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
        self.initial_population = initial_population
    
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
            keep_elitism=1,
            initial_population=self.initial_population,
        )

    def optimize(self):
        """
        Run the genetic algorithm to optimize the item combinations.

        The optimization process involves running the genetic algorithm instance,
        which will evolve the population over the specified number of generations.
        After the optimization, the best solution is extracted from the genetic algorithm instance,
        and a Chromosome instance is created with the best solution.

        The best solution contains the items and item sets that yield the highest fitness value."""
        # Run the GA
        self.ga_instance.run()
        
        # Get the best solution
        best_solution, best_solution_fitness, _ = self.ga_instance.best_solution()
        self.solution = Chromosome(
                          best_solution,
                          optimizer=self)