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
        self._name = name
        self.data_dir = data_dir

        # Charger définitions de classes
        self.base_classes = Player.base_classes
        self.adv_classes  = Player.adv_classes

        # Charger skills
        self.class_skills   = Player.class_skills
        self.passive_skills = Player.passive_skills
        self.combo_skills   = Player.combo_skills

        self.current_class = starting_class
        self._level = 1
        self._xp = 0
        # Initialize stats from class
        self._stats = self.base_classes.get(starting_class, {}).copy()
        # Set current and max HP/MP from base stats
        self._max_hp = self._stats.get('max_hp', 0)
        self._current_hp = self._max_hp
        self._max_mp = self._stats.get('max_mp', 0)
        self._current_mp = self._max_mp
        # Skills: name -> {'level': int, 'xp': int}
        self._skills = {}
        self.load_starting_skills()
        # Inventory and equipment
        self._inventory = []  # list of item objects
        self._equipment = {}  # slot name -> item object
        # Titles and quests
        self._titles = []
        self._active_title = None
        self._quests = {}  # quest_id -> quest progress data
        self._completed_quests = []
        # Counters for kills and actions
        self._kill_counter = {}
        self._action_counter = {}
        # Knowledge
        self._race_knowledge = {}
        self._enemy_knowledge = {}
        # Status effects (temporary stats)
        self._status_effects = []
        # Death flag
        self._is_dead = False

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
        cls_sk = self.class_skills.get(self.current_class, [])
        for sk in cls_sk:
            self.skills[sk["id"]] = sk.copy()
        # Compétences passives communes
        for sk in self.passive_skills.get("all", []):
            self.skills[sk["id"]] = sk.copy()

    def display_status(self):
        """Display current status (HP, MP, stats, level, etc.)."""
        print(f"Name: {self._name}    Class: {self._class}    Level: {self._level}    XP: {self._xp}")
        print(f"HP: {self._current_hp}/{self._max_hp}    MP: {self._current_mp}/{self._max_mp}")
        print("Stats:")
        for stat, value in self._stats.items():
            if stat not in ('max_hp', 'max_mp'):
                print(f"  {stat.capitalize()}: {value}")
        if self._active_title:
            print(f"Active Title: {self._active_title}")
        print(f"Location: {getattr(self, '_location', 'Unknown')}")
        print()

    def display_inventory(self):
        """Display the items in the player's inventory."""
        if not self._inventory:
            print("Inventory is empty.")
            return
        print("Inventory:")
        for item in self._inventory:
            color = self.get_rarity_color(getattr(item, 'rarity', 'Common'))
            name = getattr(item, 'name', 'Unknown')
            print(f"  {color}{name}\033[0m (ID: {getattr(item, 'id', 'N/A')})")

    def display_equipment(self):
        """Display the currently equipped items."""
        if not self._equipment:
            print("No equipment.")
            return
        print("Equipment:")
        for slot, item in self._equipment.items():
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
        self._inventory.append(item)
        print(f"Added {getattr(item, 'name', 'an item')} to inventory.")

    def remove_item(self, item_id):
        """Remove an item (by id) from the inventory."""
        for idx, item in enumerate(self._inventory):
            if getattr(item, 'id', None) == item_id:
                removed = self._inventory.pop(idx)
                print(f"Removed {getattr(removed, 'name', 'an item')} from inventory.")
                return removed
        print(f"Item with ID {item_id} not found in inventory.")
        return None

    def find_item_by_name(self, name):
        """Find and return an item in inventory by name."""
        for item in self._inventory:
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
        if slot in self._equipment and self._equipment[slot]:
            old_item = self._equipment[slot]
            print(f"Unequipped {getattr(old_item, 'name', 'an item')} from {slot} slot.")
            self._inventory.append(old_item)
        # Equip new item
        self._equipment[slot] = item
        self._inventory.remove(item)
        print(f"Equipped {getattr(item, 'name', 'an item')} to {slot} slot.")

    def unequip_item(self, slot):
        """Unequip the item currently in the given equipment slot."""
        if slot not in self._equipment or not self._equipment[slot]:
            print(f"No item equipped in slot '{slot}'.")
            return
        item = self._equipment.pop(slot)
        self._inventory.append(item)
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
        self._inventory.remove(item)
        print(f"Dropped {item.name} (ID: {getattr(item, 'id', 'N/A')}).")

    def sort_inventory(self, sort_type):
        """Sort inventory by name, rarity, or type."""
        if sort_type == 'name':
            self._inventory.sort(key=lambda x: getattr(x, 'name', ''))
        elif sort_type == 'rarity':
            rarity_order = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary']
            self._inventory.sort(key=lambda x: rarity_order.index(getattr(x, 'rarity', 'Common')))
        elif sort_type == 'type':
            self._inventory.sort(key=lambda x: getattr(x, 'type', ''))
        else:
            print(f"Unknown sort type '{sort_type}'. Sorting by name.")
            self._inventory.sort(key=lambda x: getattr(x, 'name', ''))
        print(f"Inventory sorted by {sort_type}.")

    def display_usable_items(self):
        """Display only the usable (consumable) items in the inventory."""
        usable = [item for item in self._inventory if 'potion' in getattr(item, 'name', '').lower() or getattr(item, 'consumable', False)]
        if not usable:
            print("No usable (consumable) items in inventory.")
            return
        print("Usable Items:")
        for item in usable:
            color = self.get_rarity_color(getattr(item, 'rarity', 'Common'))
            print(f"  {color}{item.name}\033[0m (ID: {getattr(item, 'id', 'N/A')})")

    def get_total_stat(self, stat):
        """Calculate the total value of a stat including base, equipment, and effects."""
        base_value = self._stats.get(stat, 0)
        total = base_value
        # Add equipment bonuses
        for item in self._equipment.values():
            if not item:
                continue
            bonuses = getattr(item, 'stat_bonuses', {})
            total += bonuses.get(stat, 0)
        # Add temporary status effect bonuses
        for effect in self._status_effects:
            if effect.get('stat') == stat:
                total += effect.get('value', 0)
        return total

    def heal(self, amount):
        """Heal the player by the given amount (up to max HP)."""
        if self._current_hp <= 0:
            print("Cannot heal. Player is dead.")
            return
        self._current_hp = min(self._current_hp + amount, self._max_hp)
        print(f"Player healed by {amount}. Current HP: {self._current_hp}/{self._max_hp}")

    def restore_mp(self, amount):
        """Restore the player's MP by the given amount (up to max MP)."""
        self._current_mp = min(self._current_mp + amount, self._max_mp)
        print(f"MP restored by {amount}. Current MP: {self._current_mp}/{self._max_mp}")

    def take_damage(self, amount):
        """Inflict damage to the player, reducing HP."""
        self._current_hp -= amount
        print(f"Player took {amount} damage. Current HP: {self._current_hp}/{self._max_hp}")
        if self._current_hp <= 0:
            self.on_death()

    def on_death(self):
        """Handle player death."""
        self._is_dead = True
        print("You have died. Game over.")

    def use_mp(self, amount):
        """Use mana points; reduce MP if enough available."""
        if amount > self._current_mp:
            print("Not enough MP!")
            return False
        self._current_mp -= amount
        print(f"Used {amount} MP. Current MP: {self._current_mp}/{self._max_mp}")
        return True

    def gain_exp(self, amount):
        """Gain experience points and handle leveling up."""
        self._xp += amount
        print(f"Gained {amount} experience points.")
        # Assume XP needed per level: 100 * current level
        xp_needed = 100 * self._level
        while self._xp >= xp_needed:
            self._xp -= xp_needed
            self.level_up()
            xp_needed = 100 * self._level

    def level_up(self):
        """Handle leveling up: increase level and improve stats."""
        self._level += 1
        # Increase stats on level up
        self._stats['max_hp'] = self._stats.get('max_hp', 0) + 10
        self._stats['max_mp'] = self._stats.get('max_mp', 0) + 5
        self._stats['strength'] = self._stats.get('strength', 0) + 1
        self._stats['defense'] = self._stats.get('defense', 0) + 1
        self._stats['agility'] = self._stats.get('agility', 0) + 1
        self._stats['intelligence'] = self._stats.get('intelligence', 0) + 1
        # Heal to full on level up
        self._current_hp = self._stats.get('max_hp', self._current_hp)
        self._current_mp = self._stats.get('max_mp', self._current_mp)
        print(f"Congratulations! {self._name} has reached level {self._level}.")

    def can_upgrade_class(self):
        """Check if player is eligible to change to an advanced class."""
        # Example condition: reach level 10
        cond = self.adv_classes.get(self.current_class, {})
        # ex. cond = {"required_level": 20, "to": "Knight"}
        req = cond.get("required_level", 999)
        return getattr(self, "level", 1) >= req

    def upgrade_class(self):
        """Upgrade player to a new advanced class if eligible."""
        cond = self.adv_classes.get(self.current_class, {})
        new_cls = cond.get("to")
        if new_cls:
            self.current_class = new_cls
            # Appliquer nouveaux stats de base
            self.stats.update(self.base_classes.get(new_cls, {}))
            print(f"Vous êtes maintenant {new_cls} !")
            self.load_starting_skills()
        return True

    def add_skill_exp(self, skill_name, exp_amount):
        """Add experience to a specific skill."""
        skill = self._skills.get(skill_name)
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
        skill = self._skills.get(skill_name)
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
        if not self._skills:
            print("No skills learned yet.")
            return
        print("Skills:")
        for skill, data in self._skills.items():
            print(f"  {skill} - Level {data['level']} (XP: {data['xp']})")

    def learn_skill(self, skill_id):
        """Permet d’ajouter une compétence (ex. issue d’un secret)."""
        # Cherche dans combo_skills si présent
        sk = self.combo_skills.get(skill_id)
        if sk and skill_id not in self.skills:
            self.skills[skill_id] = sk.copy()

    def add_title(self, title):
        """Add a title to the player's collection."""
        if title in self._titles:
            return
        self._titles.append(title)
        print(f"New title earned: '{title}'")

    def set_active_title(self, title_name):
        """Set one of the player's titles as active."""
        if title_name not in self._titles:
            print(f"Title '{title_name}' not owned.")
            return
        self._active_title = title_name
        print(f"Title '{title_name}' is now active.")

    def display_titles(self):
        """Display all titles and highlight the active one."""
        if not self._titles:
            print("No titles earned yet.")
            return
        print("Titles:")
        for t in self._titles:
            if t == self._active_title:
                print(f"  * {t} (Active)")
            else:
                print(f"  - {t}")

    def apply_title_effects(self, title):
        """Apply effects associated with the given title."""
        if title not in self._titles:
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
        self._quests[quest_id] = {'quest': quest, 'objectives': objectives_data}
        print(f"Quest '{getattr(quest, 'title', quest_id)}' added to log.")

    def update_quest_progress(self, quest_id, objective_id, progress):
        """Update progress of a quest objective."""
        if quest_id not in self._quests:
            print(f"Quest ID {quest_id} not found.")
            return
        quest_data = self._quests[quest_id]
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
        if quest_id not in self._quests:
            print(f"Quest ID {quest_id} not found.")
            return
        quest = self._quests.pop(quest_id)['quest']
        self._completed_quests.append(quest)
        print(f"Quest '{getattr(quest, 'title', quest_id)}' completed!")
        # Placeholder for rewards (XP, items, etc.)

    def display_quests(self):
        """Display all active quests and their progress."""
        if not self._quests:
            print("No active quests.")
            return
        print("Active Quests:")
        for quest_id, data in self._quests.items():
            quest = data.get('quest')
            title = getattr(quest, 'title', quest_id)
            print(f"  {title}:")
            for obj_id, obj_data in data['objectives'].items():
                progress = obj_data['progress']
                target = obj_data['target']
                print(f"    Objective {obj_id}: {progress}/{target}")

    def increment_kill_counter(self, monster_type):
        """Increment kill count for a monster type and check milestones."""
        self._kill_counter[monster_type] = self._kill_counter.get(monster_type, 0) + 1
        count = self._kill_counter[monster_type]
        # Example milestone: every 100 kills grant a title
        if count % 100 == 0:
            title = f"{monster_type} Slayer"
            self.add_title(title)

    def increment_action_counter(self, action_type):
        """Increment action usage count and check milestones."""
        self._action_counter[action_type] = self._action_counter.get(action_type, 0) + 1
        self.check_action_milestone(action_type)

    def check_action_milestone(self, action_type):
        """Check if an action usage has reached a milestone."""
        count = self._action_counter.get(action_type, 0)
        if count and count % 50 == 0:
            title = f"Seasoned {action_type.capitalize()}"
            self.add_title(title)

    def race_knowledge(self, race):
        """Return or initialize the player's knowledge level of a monster race."""
        if race not in self._race_knowledge:
            self._race_knowledge[race] = 0
        return self._race_knowledge[race]

    def enemy_knowledge(self, enemy_id):
        """Return or initialize knowledge of a specific enemy."""
        if enemy_id not in self._enemy_knowledge:
            self._enemy_knowledge[enemy_id] = 0
        return self._enemy_knowledge[enemy_id]

    def add_temporary_stat(self, stat, value, duration):
        """Add a temporary stat modifier for a duration."""
        import uuid
        effect_id = str(uuid.uuid4())
        self._status_effects.append({'id': effect_id, 'stat': stat, 'value': value, 'duration': duration})
        print(f"Temporary effect added: {stat} +{value} for {duration} turns (ID: {effect_id}).")
        return effect_id

    def remove_status_effect(self, effect_id):
        """Remove a status effect by its ID."""
        for i, eff in enumerate(self._status_effects):
            if eff.get('id') == effect_id:
                removed = self._status_effects.pop(i)
                print(f"Removed status effect {effect_id} ({removed['stat']} +{removed['value']}).")
                return
        print(f"Status effect ID {effect_id} not found.")

    def to_dict(self):
        """Convert player data to a dict for saving to JSON."""
        data = {
            'name': self._name,
            'class': self._class,
            'level': self._level,
            'xp': self._xp,
            'stats': self._stats.copy(),
            'current_hp': self._current_hp,
            'current_mp': self._current_mp,
            'skills': {sk: {'level': dat['level'], 'xp': dat['xp']} for sk, dat in self._skills.items()},
            'inventory': [getattr(item, 'id', None) for item in self._inventory],
            'equipment': {slot: getattr(item, 'id', None) for slot, item in self._equipment.items()},
            'titles': list(self._titles),
            'active_title': self._active_title,
            'quests': {},
            'kill_counter': self._kill_counter.copy(),
            'action_counter': self._action_counter.copy(),
            'race_knowledge': self._race_knowledge.copy(),
            'enemy_knowledge': self._enemy_knowledge.copy(),
            'status_effects': list(self._status_effects)
        }
        # Save quest progress
        for quest_id, qdata in self._quests.items():
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
        player._level = data.get('level', player._level)
        player._xp = data.get('xp', player._xp)
        # Restore stats and HP/MP
        stats = data.get('stats', {})
        player._stats = stats.copy()
        player._max_hp = stats.get('max_hp', player._max_hp)
        player._current_hp = data.get('current_hp', player._current_hp)
        player._max_mp = stats.get('max_mp', player._max_mp)
        player._current_mp = data.get('current_mp', player._current_mp)
        # Restore skills
        player._skills = {sk: {'level': dat['level'], 'xp': dat['xp']} for sk, dat in data.get('skills', {}).items()}
        # Restore inventory (using item_manager)
        player._inventory = []
        for item_id in data.get('inventory', []):
            item = item_manager.get_item_by_id(item_id)
            if item:
                player._inventory.append(item)
        # Restore equipment
        player._equipment = {}
        for slot, item_id in data.get('equipment', {}).items():
            item = item_manager.get_item_by_id(item_id)
            if item:
                player._equipment[slot] = item
        # Titles
        player._titles = list(data.get('titles', []))
        player._active_title = data.get('active_title')
        # Quests
        player._quests = {}
        for quest_id, qdata in data.get('quests', {}).items():
            # Minimal quest object with title and id
            quest = type('Quest', (), {})()
            setattr(quest, 'title', qdata.get('title'))
            setattr(quest, 'id', quest_id)
            objectives = {}
            for obj_id, obj in qdata.get('objectives', {}).items():
                objectives[obj_id] = {'progress': obj.get('progress'), 'target': obj.get('target')}
            player._quests[quest_id] = {'quest': quest, 'objectives': objectives}
        # Completed quests
        player._completed_quests = []
        # Counters and knowledge
        player._kill_counter = data.get('kill_counter', {}).copy()
        player._action_counter = data.get('action_counter', {}).copy()
        player._race_knowledge = data.get('race_knowledge', {}).copy()
        player._enemy_knowledge = data.get('enemy_knowledge', {}).copy()
        # Status effects
        player._status_effects = data.get('status_effects', []).copy()
        return player
