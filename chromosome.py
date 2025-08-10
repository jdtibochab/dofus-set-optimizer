from utils import damage_mapper, bonus_damage_mapper
from utils import get_item_contribution, get_set_contribution, get_item_set
import pandas as pd

# TODO: Implement ranged/melee damage bonus

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
        self.elements = optimizer.character.config["elements"]
        self.objective = optimizer.config["objective"]
        self.viable = True
        self.penalized = False

        # Get the items and item sets of the chromosome
        self.items = [optimizer.items[i] for i in self.chromosome if i is not None]
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
        iterator = iter(i for i in self.items if i["type"]["superTypeId"] == 2)
        return next(iterator,None)
    
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
    
    def get_weapon_damage(self, weapon):
        if not weapon["effects"]:
            return {}
        damage_effects = [d for d in weapon["effects"] if d["active"]]
        if not damage_effects:
            return {}
        contributions = {}
        for d in damage_effects:
            field = "max" if d["min_max_irrelevant"] == 0 else "min"
            element_id = d["element_id"]
            if element_id == 248: # Best element flag
                stats = {i:v for i,v in self.totals.items() if i in damage_mapper.values()}
                best_stat = sorted(stats,key=lambda x: stats[x])[-1]
                # Get the element with highest stat
                element_id = next(d for d,s in damage_mapper.items() if s == best_stat)
            contributions[element_id] = d[field]
        return contributions

    def get_final_damage(self, type):
        """
        Calculate the final weapon damage based on the character's totals and weapon stats.
        
        The damage is calculated based on the weapon's base damage, critical hit bonus,
        critical hit probability, and the character's stats.
        
        The damage is calculated for each element in the weapon's damage effects.
        
        The final damage is the sum of the damage for each element.
        """
        # Character stats
        power = self.totals.get(32,0)
        base_crit_chance = self.totals.get(29,0)
        base_crit_added_damage = self.totals.get(38,0)

        if type == "weapon":
            if self.weapon is None:
                return 0
            dct_damage = self.get_weapon_damage(self.weapon)
            crit_bonus = self.weapon["criticalHitBonus"] \
                if not pd.isna(self.weapon["criticalHitBonus"]) else 0
            crit_chance = self.weapon["criticalHitProbability"] \
                if not pd.isna(self.weapon["criticalHitProbability"]) else 0
        elif type == "elements":
            spell_damage = 20 # Default spell damage
            crit_bonus = 5 # Default crit bonus
            crit_chance = 5 # Default spell crit chance

            dct_damage = {}
            seen_stats = []
            for element_id, stat in damage_mapper.items():
                if stat in seen_stats:
                    # Skip stats that have already been processed
                    continue
                seen_stats.append(stat)
                if stat not in self.elements:
                    continue
                dct_damage[element_id] = spell_damage

        # Critical hit logic
        if 29 in self.optimizer.config.get("preferences",{}).get("lower"):
            final_crit_chance = max(min(crit_chance + base_crit_chance,100), 0)  # Ensure crit_chance is between 0 and 100
        else:
            # If user did not care about crit, do not use crit to prioritize items
            final_crit_chance = 0

        # Calculate expected critical hit damage bonus
        expected_crit_bonus = max(crit_bonus * final_crit_chance/100, 0) # Expected value of distribution
        expected_crit_added_damage = max(base_crit_added_damage * final_crit_chance/100, 0) # Expected value of distribution

        # Calculate total damage
        damage = 0
        for element_id,weapon_base_damage in dct_damage.items():
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
            dmg = (weapon_base_damage + expected_crit_bonus) * (1+(stat_base+power)/100) + expected_crit_added_damage + added_bonus
            damage += dmg
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
        # TODO: Implement push damage
        fitness = self.get_final_damage(type=self.objective)
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
