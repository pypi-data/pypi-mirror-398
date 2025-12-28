from typing import List, Dict, Optional
import math

class PartsVector:
    INDEXS = {
        'MOVE': 0,
        'CARRY': 1,
        'WORK': 2,
        'ATTACK': 3,
        'RANGED_ATTACK': 4,
        'HEAL': 5,
        'TOUGH': 6
    }

    VALUES = {
        0: 'MOVE',
        1: 'CARRY',
        2: 'WORK',
        3: 'ATTACK',
        4: 'RANGED_ATTACK',
        5: 'HEAL',
        6: 'TOUGH'
    }

    SCORE_TABLE = {
        'ATTACK': 10,
        'RANGED_ATTACK': 15,
        'HEAL': 15,
        'TOUGH': 1,
        'MOVE': 2,
        'CARRY': 2,
        'WORK': 5,
    }

    PARTS_COST = {
        'MOVE': 50,
        'WORK': 100,
        'CARRY': 50,
        'ATTACK': 80,
        'RANGED_ATTACK': 150,
        'HEAL': 250,
        'TOUGH': 10,
    }

    COLORS = {
        'MOVE': '#a5b7c6',
        'CARRY': '#5c6e74',
        'WORK': '#ffdb5b',
        'ATTACK': '#f92c2e',
        'RANGED_ATTACK': '#1e90ff',
        'HEAL': '#65d833',
        'TOUGH': '#FFFAFA'
    }

    def __init__(self, recipe: List[str]):
        self.recipe = recipe
        self.vec7 = [0] * 7

        for part in self.recipe:
            if part in self.INDEXS:
                self.vec7[self.INDEXS[part]] += 1

        # non-move non-carry count
        self.nmCount = self.vec7[2] + self.vec7[3] + self.vec7[4] + self.vec7[5] + self.vec7[6]
        # total count
        self.bodyCount = len(self.recipe)

    @property
    def others(self):
        return self.nmCount

    @property
    def moves(self):
        return self.vec7[0]

    @property
    def carries(self):
        return self.vec7[1]

    @property
    def works(self):
        return self.vec7[2]

    @property
    def melees(self):
        return self.vec7[3]

    @property
    def ranges(self):
        return self.vec7[4]

    @property
    def heals(self):
        return self.vec7[5]

    @property
    def toughs(self):
        return self.vec7[6]

    @property
    def total(self):
        return self.bodyCount

    def add(self, other: 'PartsVector'):
        for i in range(len(self.vec7)):
            self.vec7[i] += other.vec7[i]
        self.bodyCount += other.bodyCount
        self.nmCount = self.vec7[2] + self.vec7[3] + self.vec7[4] + self.vec7[5] + self.vec7[6]

    def sub(self, other: 'PartsVector'):
        for i in range(len(self.vec7)):
            self.vec7[i] = max(0, self.vec7[i] - other.vec7[i])
        self.bodyCount = sum(self.vec7)
        self.nmCount = self.vec7[2] + self.vec7[3] + self.vec7[4] + self.vec7[5] + self.vec7[6]

    @staticmethod
    def similarity(a: 'PartsVector', b: 'PartsVector') -> float:
        if not a or not b:
            raise ValueError("PartsVector instances cannot be None")

        a_vec7 = a.vec7
        b_vec7 = b.vec7

        if len(a_vec7) != len(b_vec7):
            raise ValueError(f"Vectors must be of the same length, but: {len(a_vec7)} and {len(b_vec7)}")

        dot_product = 0
        norm_a = 0
        norm_b = 0

        for i in range(len(a_vec7)):
            dot_product += a_vec7[i] * b_vec7[i]
            norm_a += a_vec7[i] ** 2
            norm_b += b_vec7[i] ** 2

        norm_a = math.sqrt(norm_a)
        norm_b = math.sqrt(norm_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    @staticmethod
    def parts_grade(recipe: List[str]) -> int:
        carries = 0
        moves = 0
        score = 0
        prt_length = len(recipe)
        usage = 0
        for i, prt in enumerate(recipe):
            if prt == 'ATTACK':
                score += 10 + i / 5
                usage += 8
            elif prt == 'RANGED_ATTACK':
                score += 15 + i / 4
                usage += 5
            elif prt == 'HEAL':
                score += 15 + i
                usage += 5
            elif prt == 'TOUGH':
                score += 5 - i / (1+ 0.05 * prt_length)
                usage -= 1
            else:
                score += 1
                usage += 1
                if prt == 'MOVE':
                    moves += 1
                elif prt == 'CARRY':
                    carries += 1

        usage_coef = 1 if usage > 0 else 0.5
        length = (len(recipe) - carries) - moves
        movements = moves * 2
        swamp_ratio = 0.3  # Default value
        move_cost = length * swamp_ratio * 20
        
        if length == 0:
            coef = 0
        elif movements > move_cost:
            coef = 2
        else:
            coef = (2 * movements) / move_cost
            
        final_coef = (1 + coef) / 2 * usage_coef
        return math.floor(score * final_coef)

    @staticmethod
    def parts_cost(recipe: List[str]) -> int:
        cost = 0
        for part in recipe:
            cost += PartsVector.PARTS_COST.get(part, 0)
        return cost

    @staticmethod
    def parts_optimise(parts: List[str]) -> List[str]:
        if len(parts) <= 1:
            return parts
        
        # Step 1: Put all TOUGH parts at the front
        tough_head = [part for part in parts if part == 'TOUGH']
        rest_parts = [part for part in parts if part != 'TOUGH']
        
        # Step 2: Create order
        order = list(reversed(list(dict.fromkeys(reversed(rest_parts)))))
        
        # Step 3: Count each kind
        each_count = {}
        for kind in order:
            each_count[kind] = rest_parts.count(kind)
        
        # Step 4: Find minimum count kind
        min_count = float('inf')
        min_kind = None
        for kind in order:
            if each_count[kind] < min_count:
                min_count = each_count[kind]
                min_kind = kind
        
        # Step 5: Create unit_count and other_count
        unit_count = {}
        other_count = {}
        for kind in order:
            unit_count[kind] = each_count[kind] // min_count
            other_count[kind] = each_count[kind] % min_count
        
        # Step 6: Create group pattern
        group_pattern = []
        while True:
            flag = False
            for kind in order:
                if unit_count[kind] > 0:
                    group_pattern.append(kind)
                    unit_count[kind] -= 1
                    flag = True
            if not flag:
                break
        group_pattern = list(reversed(group_pattern))
        
        # Step 7: Create others sequence
        others_sequence = []
        while True:
            flag = False
            for kind in order:
                if other_count[kind] > 0:
                    others_sequence.append(kind)
                    other_count[kind] -= 1
                    flag = True
            if not flag:
                break
        
        # Step 8: Split others into min_count lists
        def split_others(min_count, others_sequence):
            if min_count <= 1:
                return [others_sequence]
            total = (min_count + 1) * min_count / 2
            last_idx = 0
            cur_idx = 0
            res = []
            for i in range(min_count, 0, -1):
                cur_idx = last_idx + (i / total) * len(others_sequence)
                last_idx = math.ceil(last_idx)
                cur_idx = math.ceil(cur_idx)
                res.append(others_sequence[last_idx:cur_idx])
                last_idx = cur_idx
            return res
        
        others_splits = split_others(min_count, others_sequence)
        
        # Step 9: Special optimize
        tails = []
        move_count = each_count.get('MOVE', 0)
        not_move_count = 0
        for kind in order:
            if kind == 'MOVE' or kind == 'CARRY':
                continue
            not_move_count += each_count.get(kind, 0)
        
        if (move_count * 2) < (not_move_count * 5):
            # Move all MOVE parts from others_splits[0] to tails
            moves = [part for part in others_splits[0] if part == 'MOVE']
            tails.extend(moves)
            others_splits[0] = [part for part in others_splits[0] if part != 'MOVE']
        elif move_count < not_move_count * 5:
            # Move half of MOVE parts from others_splits[0] to tails
            moves = [part for part in others_splits[0] if part == 'MOVE']
            move_count_to_move = math.ceil(len(moves) / 2)
            tails.extend(moves[:move_count_to_move])
            for _ in range(move_count_to_move):
                if 'MOVE' in others_splits[0]:
                    others_splits[0].remove('MOVE')
        
        # Step 10: Merge all parts
        res = []
        res.extend(tough_head)
        for i in range(min_count):
            res.extend(others_splits[i])
            res.extend(group_pattern)
        res.extend(tails)
        
        # Step 11: Optimize HEAL parts
        heals = [part for part in res if part == 'HEAL']
        for heal in heals:
            res.remove(heal)
        res.extend(heals)
        
        return res

class NamedRecipe:
    def __init__(self, name: str, recipe: List[str]):
        self.name = name
        self.recipe = recipe
        self.vector = PartsVector(recipe)

class CreepInfo:
    def __init__(self, recipe: List[str], named_recipe: Optional[NamedRecipe] = None):
        self.recipe = recipe
        self.named_recipe = named_recipe
        self.vector = PartsVector(recipe)
        self.dynamic_vector = PartsVector(recipe)  # Same as vector initially
        
    @property
    def cost(self) -> int:
        return PartsVector.parts_cost(self.recipe)
    
    @property
    def grade(self) -> int:
        return PartsVector.parts_grade(self.recipe)
    
    @property
    def effect(self) -> float:
        # Simplified effect calculation
        return self.grade / max(1, self.cost / 100)
    
    @property
    def melee(self) -> bool:
        return self.vector.melees > 0
    
    @property
    def ranged(self) -> bool:
        return self.vector.ranges > 0
    
    @property
    def heal(self) -> bool:
        return self.vector.heals > 0
    
    @property
    def work(self) -> bool:
        return self.vector.works > 0
    
    @property
    def storable(self) -> bool:
        return self.vector.carries > 0
    
    @property
    def attack_power(self) -> int:
        return self.vector.melees * 30 + self.vector.ranges * 10
    
    @property
    def melee_power(self) -> int:
        return self.vector.melees * 30
    
    @property
    def ranged_power(self) -> int:
        return self.vector.ranges * 10
    
    @property
    def heal_power(self) -> int:
        return self.vector.heals * 12
    
    @property
    def motion_ability(self) -> float:
        if self.vector.others == 0:
            return 0.0
        move_ratio = self.vector.moves * 2 / (self.vector.others * 10)
        return move_ratio
    
    @property
    def armor_ratio(self) -> float:
        if self.vector.total == 0:
            return 0.0
        tough_ratio = self.vector.toughs / self.vector.total
        return tough_ratio * 0.5
    
    @property
    def melee_ratio(self) -> float:
        # Simplified calculation
        return self.vector.total * self.attack_power
    
    def get_recipe_string(self) -> str:
        """Generate short string representation like W3M3"""
        counts = {}
        for part in self.recipe:
            counts[part] = counts.get(part, 0) + 1
        
        # Sort by priority
        priority = ['WORK', 'ATTACK', 'RANGED_ATTACK', 'HEAL', 'TOUGH', 'CARRY', 'MOVE']
        sorted_parts = sorted(counts.items(), key=lambda x: priority.index(x[0]) if x[0] in priority else len(priority))
        
        result = []
        for part, count in sorted_parts:
            # Get first letter and add count
            result.append(f"{part[0]}{count}")
        
        return ''.join(result)

class RecipeModel:
    def __init__(self):
        self.recipe = []
        self.optimise = True
        
    def update_recipe(self, new_recipe: List[str]):
        self.recipe = new_recipe
        
    def set_optimise(self, optimise: bool):
        self.optimise = optimise
        
    def get_final_recipe(self) -> List[str]:
        """Get final recipe with optimisation only (no multiplier applied to entire recipe)"""
        if self.optimise:
            return PartsVector.parts_optimise(self.recipe)
        return self.recipe
        
    def get_creep_info(self) -> CreepInfo:
        final_recipe = self.get_final_recipe()
        return CreepInfo(final_recipe)
        
    def get_preview(self) -> str:
        final_recipe = self.get_final_recipe()
        return str(final_recipe).replace("'", "\"").replace('"', "'").replace("\", '")
        
    def get_string_representation(self) -> str:
        creep_info = self.get_creep_info()
        return creep_info.get_recipe_string()
