from utils import elements, default_soft_caps, damage_mapper, bonus_damage_mapper
from copy import copy

class Character(object):
    """
    Character class to represent a Dofus character with stats and level.
    This class is used to initialize the character's stats based on the level and
    distribute points across different elements.
    It also allows for the distribution of points based on a configuration dictionary.
    """
    def __init__(self, level, **config):
        self.config = config
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
        # Characteristic points invested, before base stats, scrolls and exos
        self.allocated = dict(self.stats)
        self._update_stats()

    def _distribute_points(self, element_id, points):
        if element_id not in default_soft_caps:
            raise ValueError(f"Characteristic points can only go to vit, wis, str, int, cha or agi, not stat {element_id}")
        value = self.stats.get(element_id, 0)
        for upper_bound, cost in default_soft_caps[element_id]:
            room = float('inf') if upper_bound is None else max(upper_bound - value, 0)
            add = int(min(room, points // cost))
            value += add
            points -= add * cost
            if add < room:
                # Not enough points left to fill this tier
                break
        self.stats[element_id] = value

    def _auto_distribute_points(self):
        #TODO: Allow the optimizer to distribute points unevenly
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
