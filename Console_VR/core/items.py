"""
items.py - Item and equipment management for FateQuest.
Handles item creation, search, usage, crafting, and shop inventories.
"""

import json
import random
import os
import uuid

class ItemManager:
    """
    Manages item data, including loading definitions and handling item operations.
    """
    def __init__(self , data_dir="data"):
        """
        Initialize the ItemManager and load item data from JSON.
        """
        self.data_dir = data_dir
        self.items = {}  # id -> item template
        self.items_by_id = {}
        self.load_items_data()
        self.identified_items = set()
    
    def load_items_data(self):
        """
        Charge les données des items depuis les fichiers JSON dans data/items/.
        """
        item_files = [
            "weapons.json", "armor.json", "consumables.json",
            "quest_items.json", "legendary.json",
            "crafting_materials.json", "enchantments.json"
        ]
        for file_name in item_files:
            file_path = os.path.join(self.data_dir, "items", file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)  # Lecture et désérialisation
            except (FileNotFoundError, json.JSONDecodeError):
                continue  # Fichier absent ou corrompu -> passer au suivant

            # Normaliser en liste d'objets
            if isinstance(data, dict):
                items_list = []
                for item_id, item_data in data.items():
                    item_data["id"] = item_id
                    items_list.append(item_data)
            elif isinstance(data, list):
                items_list = data
            else:
                continue

            type_key = os.path.splitext(file_name)[0]  # ex: "weapons"
            for item in items_list:
                # Ajouter le type (singulier)
                if "type" not in item:
                    item["type"] = type_key.rstrip('s')
                self.items[item["id"]] = item
                self.items_by_id[item["id"]] = item
    
    def create_template_file(self, item_type: str, file_path: str):
        """
        Create a template JSON file for a new item type.
        """
        template = {
            "id": "",
            "name": "",
            "type": item_type,
            "rarity": 1,
            "value": 0,
            "level": 1,
            "stats": {}
        }
        with open(file_path, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"Template for {item_type} created at {file_path}.")
    
    def get_item_by_id(self, item_id):
        """
        Retrieve an item template by its ID.
        """
        return self.items_by_id.get(item_id)
    
    def get_item_by_name(self, item_name):
        """Récupère le premier objet dont le nom correspond (insensible à la casse)."""
        for item in self.items:
            if item.get("name", "").lower() == item_name.lower():
                return item
        return None
    
    def get_all_items_of_type(self, item_type):
        """
        Get all items matching a given type (e.g., 'weapon', 'potion').
        """
        return [item for item in self.items.values() if item.get('type').lower() == item_type.lower()]
    
    def search_items(self, keyword):
        """
        Recherche basique d'objets contenant le mot-clé dans le nom ou la description.
        Le critère peut être une chaîne; on renvoie les objets correspondants.
        """
        keyword = keyword.lower()
        results = []
        for item in self.items.values():
            name = item.get("name", "").lower()
            desc = item.get("description", "").lower()
            if keyword in name or keyword in desc:
                results.append(item)
        return results
    
    def get_random_item(self, level=1, type_filter=None, rarity_filter=None):
        """
        Get a random item, optionally filtered by type, rarity, and approximate level.
        """
        candidates = []
        for item in self.items.values():
            if type_filter and item.get('type') != type_filter:
                continue
            if rarity_filter and item.get('rarity') != rarity_filter:
                continue
            if 'level' in item and abs(item['level'] - level) <= 1:
                candidates.append(item)
            elif 'level' not in item:
                candidates.append(item)
        if not candidates:
            return None
        base_item = random.choice(candidates)
        # Apply variations to create a unique instance
        return self._apply_variation_to_item(base_item.copy(), base_item.get('rarity', 1), level)
    
    def _apply_variation_to_item(self, base_item, rarity, level):
        """
        Apply random variations to an item based on its rarity and desired level.
        """
        item = base_item
        item['level'] = level
        # Increase value by rarity factor
        item['value'] = item.get('value', 0) * (1 + 0.1 * rarity)
        # Example: add random bonus stat for rare items
        if rarity >= 4:
            item['unique_bonus'] = f"+{rarity*2} to critical strike"
        return item
    
    def create_quest_item(self, quest_id, item_template: dict):
        """
        Generate a quest-specific item based on a template.
        """
        quest_item = item_template.copy()
        quest_item['id'] = f"quest_{quest_id}_{uuid.uuid4()}"
        quest_item['quest_id'] = quest_id
        return quest_item
    
    def get_boss_drop(self, boss_id, level):
        """
        Get items dropped by a boss of given ID and level.
        """
        # Placeholder: simulate boss drops as random items
        drops = []
        for i in range(random.randint(1, 3)):
            item = self.get_random_item(level)
            if item:
                drops.append(item)
        return drops
    
    def use_item(self, item, player):
        """
        Use/consume an item, applying its effects to the player.
        """
        item_type = item.get('type')
        if item_type == 'potion':
            heal = item.get('heal', 0)
            player.hp = min(player.hp + heal, player.max_hp)
            print(f"Used {item.get('name')} to heal {heal} HP.")
        elif item_type == 'buff':
            stat = item.get('stat')
            amount = item.get('amount', 0)
            duration = item.get('duration', 3)
            player.status_effects.append({'stat': stat, 'amount': amount, 'duration': duration})
            print(f"Used {item.get('name')} to buff {stat} by {amount} for {duration} turns.")
        else:
            print(f"{item.get('name')} cannot be used directly.")
    
    def equip_item(self, item, player):
        """
        Equip an item onto the player.
        """
        # Delegate equipping logic to player
        success = player.equip_item(item.get('name'))
        if success:
            print(f"{player.name} equipped {item.get('name')}.")
        else:
            print(f"Failed to equip {item.get('name')}.")
    
    def get_shop_inventory(self, shop_id, player_level):
        """
        Generate or retrieve the inventory for a shop based on player level.
        """
        # For simplicity, pick a few random items appropriate for level
        inventory = []
        for _ in range(5):
            item = self.get_random_item(player_level)
            if item:
                inventory.append(item)
        return inventory
    
    def get_item_value(self, item, is_selling=False):
        """
        Calculate the buy/sell value of an item.
        """
        base = item.get('value', 0)
        if is_selling:
            return int(base * 0.5)
        else:
            return base
    
    def repair_item(self, item, player, full_repair=False):
        """
        Repair an item's durability. Reduces player's gold by cost.
        """
        cost = item.get('repair_cost', 0)
        if full_repair:
            cost *= 2
        if player.gold >= cost:
            player.gold -= cost
            item['durability'] = item.get('max_durability', 100)
            print(f"Repaired {item.get('name')} for {cost} gold.")
        else:
            print("Not enough gold to repair.")
    
    def enhance_item(self, item, player):
        """
        Enhance an item, increasing its stats at some cost.
        """
        cost = item.get('enhance_cost', 0)
        if player.gold >= cost:
            player.gold -= cost
            item['level'] = item.get('level', 1) + 1
            print(f"Enhanced {item.get('name')} to level {item['level']}.")
        else:
            print("Not enough gold to enhance.")
    
    def identify_item(self, item, player):
        """
        Identify a mysterious item, revealing its properties.
        """
        if not item.get('identified', False):
            item['identified'] = True
            self.identified_items.add(item['id'])
            print(f"You identified the item: {item.get('name')}. It is {item.get('rarity')} rarity.")
        else:
            print("Item is already identified.")
    
    def craft_item(self, recipe_id, player):
        """
        Craft an item using a recipe and player's materials.
        """
        # Placeholder: assume recipe exists in items with negative id or in a separate structure
        print(f"Crafting recipe {recipe_id} is not implemented.")
    
    def dismantle_item(self, item, player):
        """
        Dismantle an item into base materials.
        """
        # Placeholder: refund some materials
        print(f"Dismantling {item.get('name')} yields base materials.")
        return []
    
    def enchant_item(self, item, enchantment_id, player):
        """
        Apply an enchantment to an item.
        """
        # Placeholder: apply random enchantment
        enchantment = {'id': enchantment_id, 'effect': 'fiery'}
        item['enchantment'] = enchantment
        print(f"{item.get('name')} is now enchanted with {enchantment['effect']}.")
    
    def check_legendary_unlock_conditions(self, item_id, player):
        """
        Check if conditions to unlock a legendary item are met.
        """
        # Placeholder: always return False
        return False
    
    def generate_unique_property(self, item, player_level):
        """
        Generate a unique property for an item.
        """
        bonus = random.choice(['Fire Resist', 'Water Breath', 'Health Regen'])
        item['unique_property'] = bonus
        print(f"Item {item.get('name')} gains unique property: {bonus}.")
        return bonus
    
    def get_item_evolution_path(self, item_id):
        """
        Get the evolution path (upgrades) for an item.
        """
        # Placeholder: return empty list
        return []
    
    def evolve_item(self, item, player):
        """
        Evolve an item to its next tier.
        """
        item['level'] = item.get('level', 1) + 1
        print(f"{item.get('name')} has evolved to level {item['level']}.")
        return item
    
    def get_set_bonus(self, equipped_items):
        """
        Calculate set bonuses for equipped items sharing a set.
        """
        set_counts = {}
        for item in equipped_items:
            set_name = item.get('set_name')
            if set_name:
                set_counts.setdefault(set_name, []).append(item)
        bonuses = {}
        for set_name, items in set_counts.items():
            if len(items) > 1:
                bonus = len(items) * 5
                bonuses[set_name] = f"+{bonus} to set bonus stat"
        return bonuses
