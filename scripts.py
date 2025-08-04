import pandas as pd
from functools import reduce
import json
import random
from tqdm import tqdm
import pygad
import numpy as np

# https://chat.cborg.lbl.gov/c/14738910-0178-4da7-be92-69a815a9736c

elements = [
    36, # Agility,
    22, # Chance
    13, # Intelligence
    45, # Strength
    9, # Vitality
    10, # Wisdom
]

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

conditions_mapper = {}

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
    return contributions

def get_set_contribution(item_set,overlap):
    set_effects = item_set["effects"][str(overlap)]
    contributions = {}
    for d in set_effects:
        field = "max" if d["min_max_irrelevant"] == 0 else "min"
        contributions[d["element_id"]] = d[field]
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
    def __init__(self, level, **config):
        self.stats = {}
        self.level = level
        self.scrolled = config.get("scrolled", False)
        self.exo = config.get("exo", {})
        
        self._update_stats()

    def _update_stats(self):
        self.stats[12] = 7 if self.level > 99 else 6
        self.stats[8] = 3

        if self.scrolled:
            self.stats.update({i:100 for i in elements})
        for k,v in self.exo.items():
            if k not in self.stats:
                self.stats[k] = 0
            self.stats[k] += v
        # TODO: Update character stats based on level and other factors
        pass

class Chromosome(object):
    def __init__(self, 
                 character, 
                 items, item_sets, 
                 chromosome, 
                 preferences={}):
        # Initialize the chromosome with a character, items, item sets and a chromosome
        self.chromosome = chromosome
        self.character = character
        self.preferences = preferences

        # Get the items and item sets of the chromosome
        self.items = [items[i] for i in self.chromosome]
        self.item_sets = [get_item_set(i, item_sets) \
                          for i in self.items]
        self.item_sets = [i for i in self.item_sets if i]

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
        return next(i for i in self.items if i["type"]["superTypeId"] == 2)
    
    def get_item_contributions(self):
        # Item contributions
        lst = [get_item_contribution(item) for item in self.items]
        return pd.DataFrame(lst).sum(axis=0).to_dict()
    
    def get_set_contributions(self):
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
    
    def get_totals(self):
        # Get the character stats
        character_contributions = self.character.stats.copy()
        return pd.DataFrame(
            [character_contributions,
              self.item_contributions,
                self.set_contributions]).sum(axis=0).to_dict()

    def get_final_weapon_damage(self):
        # totals = self.get_totals(chromosome)
        # Character stats
        power = self.totals.get(32,0)
        base_crit_chance = self.totals.get(29,0)
        base_crit_added_damage = self.totals.get(38,0)

        # Critical hit logic
        crit_bonus = self.weapon["criticalHitBonus"] \
            if not pd.isna(self.weapon["criticalHitBonus"]) else 0
        weapon_crit_chance = self.weapon["criticalHitProbability"] \
            if not pd.isna(self.weapon["criticalHitProbability"]) else 0
        crit_chance = max(min(weapon_crit_chance + base_crit_chance,100), 0)  # Ensure crit_chance is between 0 and 100
        expected_crit_bonus = max(crit_bonus * crit_chance/100, 0) # Expected value of distribution
        expected_crit_added_damage = max(base_crit_added_damage * crit_chance/100, 0) # Expected value of distribution
        # max_crit_bonus = crit_bonus # Use this for maximum possible
        weapon_damage = get_weapon_damage(self.weapon)

        # Calculate total damage
        damage = 0
        for element_id,weapon_base_damage in weapon_damage.items():
            # Get the stat and base damage
            if element_id not in damage_mapper:
                continue
            stat = damage_mapper[element_id]
            stat_base = self.totals.get(stat,0)

            # Get the added bonus damage from the stat
            bonus_damage_id = bonus_damage_mapper[element_id]
            added_bonus = self.totals.get(bonus_damage_id, 0)
            damage += (weapon_base_damage + expected_crit_bonus) * (1+(stat_base+power)/100) + expected_crit_added_damage + added_bonus
        return damage
    
    def are_item_conditions_met(self,item):
        return True

    def are_conditions_met(self):
        for item in self.items:
            if not self.are_item_conditions_met(item):
                return False
        return True
    
    def penalize(self, fitness):
        # Penalizations
        # Duplicated dofus and trophies
        duplicates = len(self.chromosome[-6:]) - len(set(self.chromosome[-6:]))
        for _ in range(duplicates):
            # Penalty per duplicated dofus or trophy
            fitness *= 0.5

        if len(set(self.chromosome[2:4])) < 2:
            # Arbitrary penalty for duplicated rings
            fitness *= 0.5

        if not self.are_conditions_met():
            # Arbitrary penalty for not meeting item conditions
            fitness *= 0.5

        # Penalizations for preferences
        for element,value in self.preferences.get("lower", {}).items():
            offset = max(value - self.totals.get(element, 0), 0)/value
            # Penalize and also continuously reduce the fitness
            if offset:
                fitness *= 0.75 - offset
        for element,value in self.preferences.get("upper", {}).items():
            offset = max(self.totals.get(element, 0) - value, 0)/value
            if offset:
                fitness *= 0.75 - offset
        return fitness

    def get_fitness(self,type="weapon"):
        if type == "weapon":
            fitness = self.get_final_weapon_damage()
        elif type == "elements":
            fitness = self.get_final_elemental_damage()
        return self.penalize(fitness)
    
    def totals_summary(self,item_descriptions={}, language="en"):
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
    
    def set_summary(self, language="en"):
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
    def __init__(self,
                  character,
                    items,
                      item_sets, 
                      **config):
        self.character = character
        # Load data from CSV files        
        self.items = items
        self.item_sets = item_sets
        self.config = config

        # Filters
        items = {k:v for k,v in items.items() if self.is_item_valid(v)}

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
            (12, 1),
            (13, 6), # Dofus
        ]

        self.pools = []
        for t,count in self.pool_types:
            for _ in range(count):
                self.pools.append([id \
                                    for id in items if items[id]["type"]["superTypeId"] == t])
        self.NUM_TYPES = len(self.pools)
        print(f"Total pools: {len(self.pools)} with sizes {[len(pool) for pool in self.pools]}")
        print(f"Total combinations: 10^{np.log10(float(reduce(lambda x,y: x*y, [len(pool) for pool in self.pools]))):.2f}")
        # Initialize the genetic algorithm instance
        self.initialize()
    
    def is_item_valid(self, item):
        if item["ankama_id"] in self.config["exclusions"]["items"]:
            return False
        if item["level"] > self.character.level:
            return False
        if item["type"]["superTypeId"] not in [12, 13]: # Pet, Dofus
            # Only pets can be low level
            if item["level"] + self.config["level_offset"] < self.character.level:
                # Item is too low level for the character
                return False
        return True
    
    def fitness(self,ga_instance,chromosome,chromosome_idx):
        return Chromosome(self.character,
                        self.items,
                        self.item_sets,
                        chromosome,
                        preferences=self.config["preferences"]
                        ).fitness

    def initialize(self):
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
            keep_elitism=1
        )

    def optimize(self):
        # Run the GA
        self.ga_instance.run()
        
        # Get the best solution
        best_solution, best_solution_fitness, _ = self.ga_instance.best_solution()
        self.solution = Chromosome(self.character,
                          self.items,
                          self.item_sets,
                          best_solution,
                          preferences=self.config["preferences"])