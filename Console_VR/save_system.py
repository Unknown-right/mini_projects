"""
save_system.py - Game save/load management for FateQuest.
Handles JSON-based save files, slots, backups, and game state serialization.
"""

import os
import json
import shutil
import zlib
from datetime import datetime

class SaveSystem:
    """
    Manages game saving and loading to JSON files with support for multiple slots.
    """
    def __init__(self, save_dir='saves'):
        """
        Initialize the SaveSystem and ensure the save directory exists.
        """
        self.save_dir = save_dir
        self.create_save_directory()
    
    def save_game(self, game_state: dict, slot=1):
        """
        Save the given game state to a save slot in JSON format.
        """
        path = self.get_save_path(slot)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(game_state, f, indent=2)
        except IOError as e:
            print(f"Erreur : impossible de sauvegarder la partie : {e}")
        print(f"Game saved to slot {slot}.")
    
    def load_game(self, slot=1):
        """
        Load the game state from a save slot.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        if not os.path.exists(filepath):
            print(f"No save file in slot {slot}.")
            return None
        with open(filepath, 'r') as f:
            data = json.load(f)
        # Validate data
        if not self.validate_save_data(data):
            print("Save data is corrupted or invalid.")
            return None
        return data
    
    def get_save_slots(self):
        """
        List available save slots by number.
        """
        slots = []
        for fname in os.listdir(self.save_dir):
            if fname.startswith("save_slot") and fname.endswith(".json"):
                num = fname[len("save_slot"):-len(".json")]
                if num.isdigit():
                    slots.append(int(num))
        return sorted(slots)
    
    def delete_save(self, slot):
        """
        Delete a save file and its backup for a given slot.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        backup = os.path.join(self.save_dir, f"save_slot{slot}.bak")
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(backup):
            os.remove(backup)
        print(f"Save slot {slot} deleted.")
    
    def create_save_directory(self):
        """
        Create the save directory if it does not exist.
        """
        try:
            if not os.path.isdir(self.save_dir):
                os.makedirs(self.save_dir, exist_ok=True)
        except OSError as e:
            print(f"Erreur création du dossier de sauvegarde : {e}")
    
    def get_save_path(self, slot):
        return os.path.join(self.save_dir, f"save_slot{slot}.json")
    
    def save_exists(self, slot):
        """
        Check if a save exists for the given slot.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        return os.path.exists(filepath)
    
    def get_save_metadata(self, slot):
        """
        Retrieve metadata (player name, level, timestamp) from a save file.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r') as f:
            data = json.load(f)
        meta = {}
        player = data.get('player')
        if player:
            meta['player_name'] = player.get('name')
            meta['player_level'] = player.get('level')
        if 'saved_on' in data:
            meta['saved_on'] = data.get('saved_on')
        return meta
    
    def format_metadata(self, metadata: dict):
        """
        Format save metadata into a readable string.
        """
        parts = []
        if 'player_name' in metadata:
            parts.append(f"Player: {metadata['player_name']}")
        if 'player_level' in metadata:
            parts.append(f"Level: {metadata['player_level']}")
        if 'saved_on' in metadata:
            parts.append(f"Saved: {metadata['saved_on']}")
        return " | ".join(parts)
    
    def create_backup(self, slot):
        """
        Create a backup of the save file for a given slot.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        backup = os.path.join(self.save_dir, f"save_slot{slot}.bak")
        if os.path.exists(filepath):
            shutil.copyfile(filepath, backup)
            print(f"Backup created for slot {slot}.")
    
    def restore_backup(self, slot):
        """
        Restore a save slot from its backup file.
        """
        filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
        backup = os.path.join(self.save_dir, f"save_slot{slot}.bak")
        if os.path.exists(backup):
            shutil.copyfile(backup, filepath)
            print(f"Backup restored for slot {slot}.")
    
    def get_latest_save(self):
        """
        Return the slot number of the most recent save by modification time.
        """
        latest_slot = None
        latest_time = None
        for slot in self.get_save_slots():
            filepath = os.path.join(self.save_dir, f"save_slot{slot}.json")
            mtime = os.path.getmtime(filepath)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_slot = slot
        return latest_slot
    
    def serialize_game_state(self, game_state: dict):
        """
        Convert game state dict to JSON string.
        """
        return json.dumps(game_state)
    
    def deserialize_game_state(self, data_str: str):
        """
        Convert JSON string back to game state dict.
        """
        return json.loads(data_str)
    
    def validate_save_data(self, data):
        """
        Validate the structure of save data.
        """
        # Basic validation: check required keys
        required = ['player', 'world']
        for key in required:
            if key not in data:
                return False
        return True
    
    def compress_save_data(self, data):
        """
        Compress save data (JSON string) using zlib.
        """
        json_str = json.dumps(data)
        compressed = zlib.compress(json_str.encode('utf-8'))
        return compressed
