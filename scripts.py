import pandas as pd
from functools import reduce
import json
import random
from tqdm import tqdm

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
    def __init__(self, level):
        self.stats = {}
        self.level = level
        self.scrolled = True
        self._update_stats()

    def _update_stats(self):
        self.stats[12] = 7 if self.level > 99 else 6
        self.stats[8] = 3

        if self.scrolled:
            self.stats.update({i:100 for i in elements})
        # TODO: Update character stats based on level and other factors
        pass

class Chromosome(object):
    def __init__(self, character, items, item_sets, chromosome):
        self.chromosome = chromosome
        self.character = character
        
        self.items = [items[i] for i in self.chromosome]
        self.item_sets = [get_item_set(i, item_sets) \
                          for i in self.items]
        self.item_sets = [i for i in self.item_sets if i]

        # Get the item contributions
        self.item_contributions = self.get_item_contributions()
        # Get the set contributions
        self.set_contributions = self.get_set_contributions()

        self.weapon = self.get_weapon()
        self.totals = self.get_totals()
        self.damage = self.get_damage()
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
    
    def get_damage(self):
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
        expected_crit_bonus = max(crit_bonus * crit_chance/100, 0) # Expected value of distributionß
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
    
    def are_item_conditions_met(self):
        # TODO: Code this
        return True
    
    def get_fitness(self):
        # Penalizations
        if len(set(self.chromosome[-6:])) < len(self.chromosome[-6:]):
            # Some dofus or trophies are duplicated
            return 0
        if len(set(self.chromosome[2:4])) < 2:
            # Some rings are duplicated
            return 0

        for item in self.items:
            if not self.are_item_conditions_met():
                return 0
        return self.damage

class Optimizer(object):
    def __init__(self, character, items, item_sets):
        self.character = character
        # Load data from CSV files        
        self.items = items
        self.item_sets = item_sets

        # Hyperparameters
        self.LANGUAGE = "es"
        self.POPULATION_SIZE = 150
        self.NUM_GENERATIONS = 200
        self.MUTATION_RATE = 0.05
        self.EXCLUSIONS = {
            "items" : [6894,6895,3080,9031]
        }
        self.LOWER_BOUNDS = {
            # "level" : 190
        }
        self.UPPER_BOUNDS = {}

        # Filters
        items = {k:v for k,v in items.items() if not k in self.EXCLUSIONS["items"]}

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

        self.population = [self.random_chromosome() for _ in range(self.POPULATION_SIZE)]

    @property
    def item_descriptions(self):
        item_descriptions = {}
        for _,item in self.items.items():
            if not item["effects"]:
                continue
            for effect in item["effects"]:
                item_descriptions[effect["element_id"]] = effect["type"][self.LANGUAGE]
        return item_descriptions

    # Genetic Algorithm Functions
    def random_chromosome(self):
        # Create a random chromosome sampling from each pool
        chromosome_ids = [random.choice(slot_pool) for slot_pool in self.pools]
        return Chromosome(self.character,
                          self.items,
                          self.item_sets,
                          chromosome_ids)
        # return [random.randint(0, len(slot_pool)-1) for slot_pool in self.pools]

    # Mutation
    def mutate(self,chromosome):
        # Create a new chromosome by mutating some slots
        new_chromosome = chromosome.chromosome[:]
        for i, slot_items in enumerate(self.pools):
            if random.random() < self.MUTATION_RATE:
                new_chromosome[i] = random.choice(slot_items)
        return Chromosome(self.character,
                          self.items,
                          self.item_sets,
                          new_chromosome)

    # Crossover
    def crossover(self, parent1, parent2):
        # Perform single-point crossover
        point = random.randint(1, self.NUM_TYPES-2)
        return Chromosome(self.character,
                          self.items,
                          self.item_sets,
                          parent1.chromosome[:point] + parent2.chromosome[point:])

    def fitness(chromosome):
        return chromosome.fitness
    
    def select(self, population, k=10):
        # Select top k chromosomes
        scored = sorted(population, key=self.fitness, reverse=True)
        return scored[:k]

    def optimize(self):
        for _ in tqdm(range(self.NUM_GENERATIONS), desc="Generations"):
            # Select best individuals
            selected = self.select(self.population, k=10)
            # Generate new population
            new_population = selected[:]
            while len(new_population) < self.POPULATION_SIZE:
                parent1, parent2 = random.sample(selected, 2)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)
            self.population = new_population
            # Print best fitness in this generation
            self.best = max(self.population, key=self.fitness)

            