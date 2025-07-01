import json
import os

class Player:
    """
    Class representing the player character in FateQuest game.
    Manages player stats, inventory, skills, titles, quests, etc.
    """
    # Attributs de classe — chargés une seule fois
    @staticmethod
    def load_json(path):
        full_path = os.path.join("data", path)
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    base_classes = load_json.__func__("classes\\base_classes.json")
    adv_classes  = load_json.__func__("classes\\advanced_classes.json")
    class_skills   = load_json.__func__("skills\\class_skills.json")
    passive_skills = load_json.__func__("skills\\passive_skills.json")
    combo_skills   = load_json.__func__("skills\\combo_skills.json")
    def __init__(self, name, starting_class , data_dir="data"):
        """Initialize a new player with name and class."""
        # Player identity
        self.name = name
        self.data_dir = data_dir

        # Charger définitions de classes
        self.base_classes = Player.base_classes
        self.adv_classes  = Player.adv_classes

        # Charger skills
        self.classe_skills   = Player.class_skills
        self.passive_skills = Player.passive_skills
        self.combo_skills   = Player.combo_skills

        self.current_class = starting_class
        self.level = 1
        self.xp = 0
        # Initialize stats from class
        self.stats = self.base_classes[starting_class]["base_stats"].copy()
        self.stat_growth = self.base_classes[starting_class]["stat_growth"].copy()
        # Set current and max HP/MP from base stats
        self.max_hp = self.stats.get('hp_base', 0)
        self.hp = self.max_hp
        self.max_mp = self.stats.get('mp_base', 0)
        self.mp = self.max_mp
        # Skills: name -> {'level': int, 'xp': int}
        self.skills = {}
        self.load_starting_skills()
        # Inventory and equipment
        self.inventory = []  # list of item objects
        self.equipment = {}  # slot name -> item object
        # Titles and quests
        self.titles = []
        self.active_title = None
        self.quests = {}  # quest_id -> quest progress data
        self.completed_quests = []
        # Counters for kills and actions
        self.kill_counter = {}
        self.action_counter = {}
        # Knowledge
        self.race_knowledge = {}
        self.enemy_knowledge = {}
        # Status effects (temporary stats)
        self.status_effects = []
        # Death flag
        self.is_dead = False

    def load_json(self, rel_path):
        """Charge un fichier JSON de data/ et renvoie le dict, ou {}."""
        path = os.path.join(self.data_dir, rel_path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def load_starting_skills(self):
        """Populate self.skills depuis class_skills + passive_skills."""
        # Compétences de classe
        cls_sk = self.classe_skills.get(self.current_class, [])
        for sk in cls_sk:
            self.skills[sk["id"]] = sk.copy()
        # Compétences passives communes
        for sk in self.passive_skills.get("all", []):
            self.skills[sk["id"]] = sk.copy()

    def display_status(self):
        """Display current status (HP, MP, stats, level, etc.)."""
        print(f"Name: {self.name}    Class: {self.classe}    Level: {self.level}    XP: {self.xp}")
        print(f"HP: {self.hp}/{self.max_hp}    MP: {self.mp}/{self.max_mp}")
        print("Stats:")
        for stat, value in self.stats.items():
            if stat not in ('hp_base', 'mp_base'):
                print(f"  {stat.capitalize()}: {value}")
        if self.active_title:
            print(f"Active Title: {self.active_title}")
        print(f"Location: {getattr(self, '_location', 'Unknown')}")
        print()

    def display_inventory(self):
        """Display the items in the player's inventory."""
        if not self.inventory:
            print("Inventory is empty.")
            return
        print("Inventory:")
        for item in self.inventory:
            color = self.get_rarity_color(getattr(item, 'rarity', 'Common'))
            name = getattr(item, 'name', 'Unknown')
            print(f"  {color}{name}\033[0m (ID: {getattr(item, 'id', 'N/A')})")

    def display_equipment(self):
        """Display the currently equipped items."""
        if not self.equipment:
            print("No equipment.")
            return
        print("Equipment:")
        for slot, item in self.equipment.items():
            color = self.get_rarity_color(getattr(item, 'rarity', 'Common'))
            name = getattr(item, 'name', 'Unknown')
            print(f"  {slot.capitalize()}: {color}{name}\033[0m (ID: {getattr(item, 'id', 'N/A')})")

    def get_rarity_color(self, rarity):
        """Return a console ANSI color code based on item rarity."""
        colors = {
            'Common': '\033[0m',    # Default
            'Uncommon': '\033[92m', # Green
            'Rare': '\033[94m',     # Blue
            'Epic': '\033[95m',     # Magenta
            'Legendary': '\033[93m' # Yellow
        }
        return colors.get(rarity, '\033[0m')

    def add_item(self, item):
        """Add an item object to the inventory."""
        self.inventory.append(item)
        print(f"Added {getattr(item, 'name', 'an item')} to inventory.")

    def remove_item(self, item_id):
        """Remove an item (by id) from the inventory."""
        for idx, item in enumerate(self.inventory):
            if getattr(item, 'id', None) == item_id:
                removed = self.inventory.pop(idx)
                print(f"Removed {getattr(removed, 'name', 'an item')} from inventory.")
                return removed
        print(f"Item with ID {item_id} not found in inventory.")
        return None

    def find_item_by_name(self, name):
        """Find and return an item in inventory by name."""
        for item in self.inventory:
            if getattr(item, 'name', '').lower() == name.lower():
                return item
        return None

    def examine_item(self, item_name):
        """Examine an item to get its description or stats."""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"No item named '{item_name}' in inventory.")
            return
        name = getattr(item, 'name', 'Unknown')
        desc = getattr(item, 'description', 'No description.')
        rarity = getattr(item, 'rarity', 'Common')
        color = self.get_rarity_color(rarity)
        print(f"Examining {color}{name}\033[0m - Rarity: {rarity}")
        print(f"{desc}")
        bonuses = getattr(item, 'stat_bonuses', {})
        if bonuses:
            print("Stat Bonuses:")
            for stat, val in bonuses.items():
                print(f"  {stat}: {val}")
        # If consumable, maybe show effect
        if getattr(item, 'consumable', False):
            effect = getattr(item, 'effect', None)
            if effect:
                print(f"Effect: {effect}")

    def equip_item(self, item_name):
        """Equip an item (weapon/armor) from the inventory."""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"No item named '{item_name}' to equip.")
            return
        slot = getattr(item, 'slot', None)
        if not slot:
            print(f"Item '{item_name}' cannot be equipped (no slot defined).")
            return
        # Unequip existing item in that slot
        if slot in self.equipment and self.equipment[slot]:
            old_item = self.equipment[slot]
            print(f"Unequipped {getattr(old_item, 'name', 'an item')} from {slot} slot.")
            self.inventory.append(old_item)
        # Equip new item
        self.equipment[slot] = item
        self.inventory.remove(item)
        print(f"Equipped {getattr(item, 'name', 'an item')} to {slot} slot.")

    def unequip_item(self, slot):
        """Unequip the item currently in the given equipment slot."""
        if slot not in self.equipment or not self.equipment[slot]:
            print(f"No item equipped in slot '{slot}'.")
            return
        item = self.equipment.pop(slot)
        self.inventory.append(item)
        print(f"Unequipped {getattr(item, 'name', 'an item')} from {slot} slot.")

    def use_item(self, item_name):
        """Use a consumable item from the inventory."""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"No item named '{item_name}' to use.")
            return
        name_lower = item.name.lower()
        if 'potion' in name_lower or getattr(item, 'consumable', False):
            # Apply effect
            if 'health' in name_lower or 'heal' in name_lower:
                heal_amount = getattr(item, 'heal_amount', 50)
                self.heal(heal_amount)
                print(f"Used {item.name}, healed {heal_amount} HP.")
            elif 'mana' in name_lower:
                restore_amount = getattr(item, 'mp_restore', 30)
                self.restore_mp(restore_amount)
                print(f"Used {item.name}, restored {restore_amount} MP.")
            else:
                effect = getattr(item, 'effect', None)
                if effect:
                    print(f"Used {item.name}: {effect}")
            # Remove item from inventory after use
            self.remove_item(getattr(item, 'id', None))
        else:
            print(f"Item '{item_name}' is not usable (consumable) or has no immediate effect.")

    def drop_item(self, item_name):
        """Drop an item from the inventory."""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"No item named '{item_name}' to drop.")
            return
        self.inventory.remove(item)
        print(f"Dropped {item.name} (ID: {getattr(item, 'id', 'N/A')}).")

    def sort_inventory(self, sort_type):
        """Sort inventory by name, rarity, or type."""
        if sort_type == 'name':
            self.inventory.sort(key=lambda x: getattr(x, 'name', ''))
        elif sort_type == 'rarity':
            rarity_order = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary']
            self.inventory.sort(key=lambda x: rarity_order.index(getattr(x, 'rarity', 'Common')))
        elif sort_type == 'type':
            self.inventory.sort(key=lambda x: getattr(x, 'type', ''))
        else:
            print(f"Unknown sort type '{sort_type}'. Sorting by name.")
            self.inventory.sort(key=lambda x: getattr(x, 'name', ''))
        print(f"Inventory sorted by {sort_type}.")

    def display_usable_items(self):
        """Display only the usable (consumable) items in the inventory."""
        usable = [item for item in self.inventory if 'potion' in getattr(item, 'name', '').lower() or getattr(item, 'consumable', False)]
        if not usable:
            print("No usable (consumable) items in inventory.")
            return
        print("Usable Items:")
        for item in usable:
            color = self.get_rarity_color(getattr(item, 'rarity', 'Common'))
            print(f"  {color}{item.name}\033[0m (ID: {getattr(item, 'id', 'N/A')})")

    def get_total_stat(self, stat):
        """Calculate the total value of a stat including base, equipment, and effects."""
        base_value = self.stats.get(stat, 0)
        total = base_value
        # Add equipment bonuses
        for item in self.equipment.values():
            if not item:
                continue
            bonuses = getattr(item, 'stat_bonuses', {})
            total += bonuses.get(stat, 0)
        # Add temporary status effect bonuses
        for effect in self.status_effects:
            if effect.get('stat') == stat:
                total += effect.get('value', 0)
        return total

    def heal(self, amount):
        """Heal the player by the given amount (up to max HP)."""
        if self.hp <= 0:
            print("Cannot heal. Player is dead.")
            return
        self.hp = min(self.hp + amount, self.max_hp)
        print(f"Player healed by {amount}. Current HP: {self.hp}/{self.max_hp}")

    def restore_mp(self, amount):
        """Restore the player's MP by the given amount (up to max MP)."""
        self.mp = min(self.mp + amount, self.max_mp)
        print(f"MP restored by {amount}. Current MP: {self.mp}/{self.max_mp}")

    def take_damage(self, amount):
        """Inflict damage to the player, reducing HP."""
        self.hp -= amount
        print(f"Player took {amount} damage. Current HP: {self.hp}/{self.max_hp}")
        if self.hp <= 0:
            self.on_death()

    def on_death(self):
        """Handle player death."""
        self.is_dead = True
        print("You have died. Game over.")

    def use_mp(self, amount):
        """Use mana points; reduce MP if enough available."""
        if amount > self.mp:
            print("Not enough MP!")
            return False
        self.mp -= amount
        print(f"Used {amount} MP. Current MP: {self.mp}/{self.max_mp}")
        return True

    def gain_exp(self, amount):
        """Gain experience points and handle leveling up."""
        self.xp += amount
        print(f"Gained {amount} experience points.")
        # Assume XP needed per level: 100 * current level
        xp_needed = 100 * self.level
        while self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level_up()
            xp_needed = 100 * self.level

    def level_up(self):
        """Level up the player, increasing stats and resetting HP/MP."""
        self.level += 1
        for stat, growth in self.stat_growth.items():
            self.stats[stat] = self.stats.get(stat, 0) + growth
        print(f"Congratulations! {self._name} has reached level {self.level}.")
        # HP/MP reset si besoin
        self.hp = self.stats.get("hp_base", self.hp)
        self.mp = self.stats.get("mp_base", self.mp)

    def can_upgrade_class(self, target_class_id):
        adv = self.adv_classes.get(target_class_id)
        if not adv:
            return False
        cond = adv.get("unlock_conditions", {})
        # Vérifier toutes les conditions ici
        if self.level < cond.get("level", 0):
            return False
        for stat, value in cond.get("stats", {}).items():
            if self.stats.get(stat, 0) < value:
                return False
        # ...vérifier kills, achievements, etc.
        return True

    def upgrade_class(self, target_class_id):
        adv = self.adv_classes.get(target_class_id)
        if not adv:
            print("Classe avancée non trouvée.")
            return False
        # Appliquer les modificateurs à stat_growth
        modifiers = adv.get("stat_modifiers", {})
        for stat, mult in modifiers.items():
            if stat in self.stat_growth:
                self.stat_growth[stat] *= mult
        self.current_class = target_class_id
        print(f"Vous êtes maintenant {adv['name']}!")
        # Ajouter les compétences spéciales si désiré
        # self._skills.update(...)
        return True

    def add_skill_exp(self, skill_name, exp_amount):
        """Add experience to a specific skill."""
        skill = self.skills.get(skill_name)
        if not skill:
            print(f"Skill '{skill_name}' not known.")
            return
        skill['xp'] += exp_amount
        print(f"Gained {exp_amount} XP in skill '{skill_name}'.")
        # Check for skill level up
        xp_needed = self.calculate_skill_exp_for_level(skill['level'])
        if skill['xp'] >= xp_needed:
            self.level_up_skill(skill_name)

    def calculate_skill_exp_for_level(self, level):
        """Calculate required XP for a skill to reach given level."""
        # Example formula: 100 * level
        return 100 * level

    def level_up_skill(self, skill_name):
        """Level up the given skill if enough experience."""
        skill = self.skills.get(skill_name)
        if not skill:
            print(f"Skill '{skill_name}' not known.")
            return
        xp_needed = self.calculate_skill_exp_for_level(skill['level'])
        if skill['xp'] >= xp_needed:
            skill['xp'] -= xp_needed
            skill['level'] += 1
            print(f"Skill '{skill_name}' leveled up to {skill['level']}.")
        else:
            print(f"Not enough XP to level up skill '{skill_name}'.")

    def display_skills(self):
        """Display the player's skills and their levels."""
        if not self.skills:
            print("No skills learned yet.")
            return
        print("Skills:")
        for skill, data in self.skills.items():
            print(f"  {skill} - Level {data['level']} (XP: {data['xp']})")

    def learn_skill(self, skill_id):
        """Permet d’ajouter une compétence (ex. issue d’un secret)."""
        # Cherche dans combo_skills si présent
        sk = self.combo_skills.get(skill_id)
        if sk and skill_id not in self.skills:
            self.skills[skill_id] = sk.copy()

    def add_title(self, title):
        """Add a title to the player's collection."""
        if title in self.titles:
            return
        self.titles.append(title)
        print(f"New title earned: '{title}'")

    def set_active_title(self, title_name):
        """Set one of the player's titles as active."""
        if title_name not in self.titles:
            print(f"Title '{title_name}' not owned.")
            return
        self.active_title = title_name
        print(f"Title '{title_name}' is now active.")

    def display_titles(self):
        """Display all titles and highlight the active one."""
        if not self.titles:
            print("No titles earned yet.")
            return
        print("Titles:")
        for t in self.titles:
            if t == self.active_title:
                print(f"  * {t} (Active)")
            else:
                print(f"  - {t}")

    def apply_title_effects(self, title):
        """Apply effects associated with the given title."""
        if title not in self.titles:
            print(f"Title '{title}' not owned.")
            return
        # Placeholder for actual title effects
        print(f"Applied effects of title '{title}' (if any).")

    def add_quest(self, quest):
        """Add a new quest to the player's active quests."""
        quest_id = getattr(quest, 'id', None)
        if quest_id is None:
            print("Invalid quest.")
            return
        # Initialize quest progress structure
        objectives_data = {}
        for obj in getattr(quest, 'objectives', []):
            obj_id = obj.get('id')
            target = obj.get('target', 0)
            objectives_data[obj_id] = {'progress': 0, 'target': target}
        self.quests[quest_id] = {'quest': quest, 'objectives': objectives_data}
        print(f"Quest '{getattr(quest, 'title', quest_id)}' added to log.")

    def update_quest_progress(self, quest_id, objective_id, progress):
        """Update progress of a quest objective."""
        if quest_id not in self.quests:
            print(f"Quest ID {quest_id} not found.")
            return
        quest_data = self.quests[quest_id]
        if objective_id not in quest_data['objectives']:
            print(f"Objective ID {objective_id} not found in quest {quest_id}.")
            return
        obj = quest_data['objectives'][objective_id]
        obj['progress'] += progress
        if obj['progress'] >= obj['target']:
            obj['progress'] = obj['target']
            print(f"Objective {objective_id} completed for quest {quest_id}.")
        # Check if all objectives are complete
        if all(o['progress'] >= o['target'] for o in quest_data['objectives'].values()):
            self.complete_quest(quest_id)

    def complete_quest(self, quest_id):
        """Mark a quest as complete and handle rewards."""
        if quest_id not in self.quests:
            print(f"Quest ID {quest_id} not found.")
            return
        quest = self.quests.pop(quest_id)['quest']
        self.completed_quests.append(quest)
        print(f"Quest '{getattr(quest, 'title', quest_id)}' completed!")
        # Placeholder for rewards (XP, items, etc.)

    def display_quests(self):
        """Display all active quests and their progress."""
        if not self.quests:
            print("No active quests.")
            return
        print("Active Quests:")
        for quest_id, data in self.quests.items():
            quest = data.get('quest')
            title = getattr(quest, 'title', quest_id)
            print(f"  {title}:")
            for obj_id, obj_data in data['objectives'].items():
                progress = obj_data['progress']
                target = obj_data['target']
                print(f"    Objective {obj_id}: {progress}/{target}")

    def increment_kill_counter(self, monster_type):
        """Increment kill count for a monster type and check milestones."""
        self.kill_counter[monster_type] = self.kill_counter.get(monster_type, 0) + 1
        count = self.kill_counter[monster_type]
        # Example milestone: every 100 kills grant a title
        if count % 100 == 0:
            title = f"{monster_type} Slayer"
            self.add_title(title)

    def increment_action_counter(self, action_type):
        """Increment action usage count and check milestones."""
        self.action_counter[action_type] = self.action_counter.get(action_type, 0) + 1
        self.check_action_milestone(action_type)

    def check_action_milestone(self, action_type):
        """Check if an action usage has reached a milestone."""
        count = self.action_counter.get(action_type, 0)
        if count and count % 50 == 0:
            title = f"Seasoned {action_type.capitalize()}"
            self.add_title(title)

    def race_knowledge(self, race):
        """Return or initialize the player's knowledge level of a monster race."""
        if race not in self.race_knowledge:
            self.race_knowledge[race] = 0
        return self.race_knowledge[race]

    def enemy_knowledge(self, enemy_id):
        """Return or initialize knowledge of a specific enemy."""
        if enemy_id not in self.enemy_knowledge:
            self.enemy_knowledge[enemy_id] = 0
        return self.enemy_knowledge[enemy_id]

    def add_temporary_stat(self, stat, value, duration):
        """Add a temporary stat modifier for a duration."""
        import uuid
        effect_id = str(uuid.uuid4())
        self.status_effects.append({'id': effect_id, 'stat': stat, 'value': value, 'duration': duration})
        print(f"Temporary effect added: {stat} +{value} for {duration} turns (ID: {effect_id}).")
        return effect_id

    def remove_status_effect(self, effect_id):
        """Remove a status effect by its ID."""
        for i, eff in enumerate(self.status_effects):
            if eff.get('id') == effect_id:
                removed = self.status_effects.pop(i)
                print(f"Removed status effect {effect_id} ({removed['stat']} +{removed['value']}).")
                return
        print(f"Status effect ID {effect_id} not found.")

    def to_dict(self):
        """Convert player data to a dict for saving to JSON."""
        data = {
            'name': self.name,
            'class': self.classe,
            'level': self.level,
            'xp': self.xp,
            'stats': self.stats.copy(),
            'current_hp': self.hp,
            'current_mp': self.mp,
            'skills': {sk: {'level': dat['level'], 'xp': dat['xp']} for sk, dat in self.skills.items()},
            'inventory': [getattr(item, 'id', None) for item in self.inventory],
            'equipment': {slot: getattr(item, 'id', None) for slot, item in self.equipment.items()},
            'titles': list(self.titles),
            'active_title': self.active_title,
            'quests': {},
            'kill_counter': self.kill_counter.copy(),
            'action_counter': self.action_counter.copy(),
            'race_knowledge': self.race_knowledge.copy(),
            'enemy_knowledge': self.enemy_knowledge.copy(),
            'status_effects': list(self.status_effects)
        }
        # Save quest progress
        for quest_id, qdata in self.quests.items():
            quest_obj = qdata.get('quest')
            objectives = qdata.get('objectives', {})
            data_obj = {'title': getattr(quest_obj, 'title', quest_id), 'objectives': {}}
            for obj_id, obj in objectives.items():
                data_obj['objectives'][obj_id] = {
                    'progress': obj.get('progress'),
                    'target': obj.get('target')
                }
            data['quests'][quest_id] = data_obj
        return data

    @classmethod
    def load_from_data(cls, data, item_manager):
        """Create a Player instance from saved data using item_manager for items."""
        name = data.get('name')
        starting_class = data.get('class')
        player = cls(name, starting_class)
        # Restore level and xp
        player.level = data.get('level', player.level)
        player.xp = data.get('xp', player.xp)
        # Restore stats and HP/MP
        stats = data.get('stats', {})
        player.stats = stats.copy()
        player.max_hp = stats.get('hp_base', player.max_hp)
        player.hp = data.get('current_hp', player.hp)
        player.max_mp = stats.get('mp_base', player.max_mp)
        player.mp = data.get('current_mp', player.mp)
        # Restore skills
        player.skills = {sk: {'level': dat['level'], 'xp': dat['xp']} for sk, dat in data.get('skills', {}).items()}
        # Restore inventory (using item_manager)
        player.inventory = []
        for item_id in data.get('inventory', []):
            item = item_manager.get_item_by_id(item_id)
            if item:
                player.inventory.append(item)
        # Restore equipment
        player.equipment = {}
        for slot, item_id in data.get('equipment', {}).items():
            item = item_manager.get_item_by_id(item_id)
            if item:
                player.equipment[slot] = item
        # Titles
        player.titles = list(data.get('titles', []))
        player.active_title = data.get('active_title')
        # Quests
        player.quests = {}
        for quest_id, qdata in data.get('quests', {}).items():
            # Minimal quest object with title and id
            quest = type('Quest', (), {})()
            setattr(quest, 'title', qdata.get('title'))
            setattr(quest, 'id', quest_id)
            objectives = {}
            for obj_id, obj in qdata.get('objectives', {}).items():
                objectives[obj_id] = {'progress': obj.get('progress'), 'target': obj.get('target')}
            player.quests[quest_id] = {'quest': quest, 'objectives': objectives}
        # Completed quests
        player.completed_quests = []
        # Counters and knowledge
        player.kill_counter = data.get('kill_counter', {}).copy()
        player.action_counter = data.get('action_counter', {}).copy()
        player.race_knowledge = data.get('race_knowledge', {}).copy()
        player.enemy_knowledge = data.get('enemy_knowledge', {}).copy()
        # Status effects
        player.status_effects = data.get('status_effects', []).copy()
        return player
