"""
monsters.py - Enemy and boss management for FateQuest.
Handles monster templates, spawning, and related utilities.
"""
import os
import json
import random
import uuid

class MonsterManager:
    """
    Manages monster data, including loading definitions and generating encounters.
    """
    def __init__(self, data_dir="data"):
        """
        Initialise en chargeant tous les monstres et données associées.
        """
        self.data_dir = data_dir
        self.monsters = []
        self.monsters_by_id = {}
        # Charger données auxiliaires
        self.factions = {}
        self.abilities = {}
        self.behaviors = {}
        self.load_monster_data()
    
    def load_monster_data(self):
        """
        Charge les JSON de monstres et descripteurs (factions, abilities, behaviors).
        """
        # Charger factions, capacités, comportements
        try:
            with open(os.path.join(self.data_dir, "monsters", "factions.json"), 'r', encoding='utf-8') as f:
                self.factions = json.load(f)
        except:
            self.factions = {}
        try:
            with open(os.path.join(self.data_dir, "monsters", "abilities.json"), 'r', encoding='utf-8') as f:
                self.abilities = json.load(f)
        except:
            self.abilities = {}
        try:
            with open(os.path.join(self.data_dir, "monsters", "behaviors.json"), 'r', encoding='utf-8') as f:
                self.behaviors = json.load(f)
        except:
            self.behaviors = {}

        # Fichiers de monstres groupés par rareté
        monster_files = [
            ("common.json", "common"),
            ("uncommon.json", "uncommon"),
            ("rare.json", "rare"),
            ("elite.json", "elite"),
            ("bosses.json", "boss")
        ]
        for file_name, rarity in monster_files:
            path = os.path.join(self.data_dir, "monsters", file_name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
            # Normaliser en liste
            if isinstance(data, dict):
                monsters_list = []
                for mon_id, mon_data in data.items():
                    mon_data["id"] = mon_id
                    monsters_list.append(mon_data)
            elif isinstance(data, list):
                monsters_list = data
            else:
                continue

            for monster in monsters_list:
                monster.setdefault("rarity", rarity)
                monster.setdefault("faction", None)
                # Remplacer IDs d'abilities par les données réelles si disponible
                if "abilities" in monster and isinstance(monster["abilities"], list):
                    monster["abilities"] = [
                        self.abilities.get(ab_id, ab_id) for ab_id in monster["abilities"]
                    ]
                # Ajouter comportement si défini
                if monster["id"] in self.behaviors:
                    monster["behavior"] = self.behaviors[monster["id"]]
                self.monsters.append(monster)
                self.monsters_by_id[monster["id"]] = monster

    def get_monster_by_id(self, monster_id):
        """Retourne un monstre par son ID."""
        return self.monsters_by_id.get(monster_id)

    # Pour la compatibilité avec le code existant :
    get_enemy = get_monster_by_id  # Alias si nécessaire
    
    def create_template_files(self, monster_type: str, file_path: str):
        """
        Create a template JSON file for a new monster type.
        """
        template = {
            "id": "",
            "name": "",
            "type": monster_type,
            "level": 1,
            "hp": 10,
            "attack": 1,
            "defense": 0,
            "abilities": [],
            "weaknesses": [],
            "resistances": [],
            "loot_table": []
        }
        with open(file_path, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"Monster template created at {file_path}.")
    
    def get_enemy(self, monster_id=None, location=None, level=None):
        """
        Retrieve a specific or random enemy. If monster_id is given, return that monster.
        Otherwise, choose a random monster matching location or level.
        """
        if monster_id:
            monster = self.get_monster_by_id(monster_id)
            if monster:
                return self._apply_variation_to_monster(monster.copy(), level or monster.get('level', 1))
        # Random selection
        candidates = []
        for monster in self.monsters.values():
            if location and monster.get('location') != location:
                continue
            if level and monster.get('level') != level:
                continue
            candidates.append(monster)
        if not candidates:
            # fallback to any monster
            candidates = list(self.monsters.values())
        base = random.choice(candidates)
        return self._apply_variation_to_monster(base.copy(), level or base.get('level', 1))
    
    def get_boss(self, boss_id=None, difficulty=1):
        """
        Get a boss by ID and apply difficulty scaling.
        """
        if boss_id and boss_id in self.monsters:
            boss = self.monsters[boss_id].copy()
        else:
            # Choose a random monster as boss if none specified
            boss = random.choice(list(self.monsters.values())).copy()
        boss = self._apply_variation_to_monster(boss, boss.get('level', 1) * difficulty, is_boss=True)
        return boss
    
    def get_enemies_for_location(self, location, level, count=3):
        """
        Generate a list of enemies suitable for the given location and level.
        """
        enemies = []
        for _ in range(count):
            enemy = self.get_enemy(location=location, level=level)
            if enemy:
                enemies.append(enemy)
        return enemies
    
    def get_random_monster(self, level=1, type_filter=None, faction_filter=None):
        """
        Get a random monster with optional type or faction filters.
        """
        candidates = []
        for monster in self.monsters.values():
            if type_filter and monster.get('type') != type_filter:
                continue
            if faction_filter and monster.get('faction') != faction_filter:
                continue
            if 'level' in monster and monster['level'] == level:
                candidates.append(monster)
        if not candidates:
            candidates = list(self.monsters.values())
        base = random.choice(candidates)
        return self._apply_variation_to_monster(base.copy(), level)
    
    def _apply_variation_to_monster(self, base_monster, level, is_boss=False):
        """
        Apply statistical variations to a monster based on its level or boss status.
        """
        monster = base_monster
        monster['level'] = level
        # Scale HP and attack by level
        monster['hp'] = monster.get('hp', 10) + (level - 1) * 5
        monster['attack'] = monster.get('attack', 1) + (level - 1) * 1
        if is_boss:
            # Bosses are tougher
            monster['hp'] *= 2
            monster['attack'] *= 2
        monster['current_hp'] = monster['hp']
        return monster
    
    def _generate_unique_monster_id(self):
        """
        Generate a unique ID for a newly created monster instance.
        """
        return str(uuid.uuid4())
    
    def get_monster_by_id(self, monster_id):
        """
        Get a monster template by ID.
        """
        return self.monsters.get(monster_id)
    
    def search_monsters(self, criteria: dict):
        """
        Search for monsters by criteria (e.g., type, level).
        """
        results = []
        for m in self.monsters:
            if all(m.get(k) == v for k, v in criteria.items()):
                results.append(m)
        return results
    
    def calculate_monster_exp_reward(self, monster, player_level):
        """
        Calculate the experience reward for defeating a monster.
        """
        base_exp = monster.get('level', 1) * 10
        level_diff = monster.get('level', 1) - player_level
        exp = base_exp + max(level_diff * 5, 0)
        return max(exp, 1)
    
    def calculate_monster_loot_table(self, monster, player_luck=1):
        """
        Calculate loot items dropped by a monster.
        """
        loot = []
        for drop in monster.get('loot_table', []):
            chance = drop.get('chance', 100)
            roll = random.randint(1, 100)
            if roll <= chance * player_luck:
                loot.append(drop.get('item_id'))
        return loot
    
    def get_monster_abilities(self, monster):
        """
        Return the abilities of a monster.
        """
        return monster.get('abilities', [])
    
    def get_monster_weakness(self, monster):
        """
        Return the weaknesses of a monster (e.g., elemental).
        """
        return monster.get('weaknesses', [])
    
    def get_monster_resistance(self, monster):
        """
        Return the resistances of a monster (e.g., elemental).
        """
        return monster.get('resistances', [])
    
    def check_monster_faction_relations(self, monster_id, target_faction):
        """
        Check relations between monster's faction and target faction.
        """
        monster = self.get_monster_by_id(monster_id)
        if not monster:
            return None
        faction = monster.get('faction')
        if faction == target_faction:
            return 'ally'
        return 'enemy'
    
    def get_monster_description(self, monster, player_knowledge=0):
        """
        Generate a description of the monster, varying by player's knowledge.
        """
        name = monster.get('name', 'Unknown')
        lvl = monster.get('level', 1)
        desc = f"A level {lvl} {name}."
        if player_knowledge > 0:
            desc += f" It has {monster.get('hp')} HP and deals {monster.get('attack')} damage."
        return desc
    
    def get_monster_behavior(self, monster_id, combat_state):
        """
        Determine monster behavior in combat (e.g., aggressive, cautious).
        """
        # Placeholder: random or simple AI traits
        return random.choice(['aggressive', 'defensive', 'cautious'])
    
    def update_monster_population(self, location, monster_type, killed=False):
        """
        Update the population or spawn rate of monsters in a location.
        """
        # Placeholder: could spawn more if killed=False, or reduce if killed
        pass
