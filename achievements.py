"""
achievements.py - Implicit achievements detection and tracking for FateQuest.
Handles achievements, progress, unlocking, and awarding titles.
"""
import os
import json
from termcolor import colored

class AchievementSystem:
    """
    Tracks and unlocks achievements based on player actions.
    """
    def __init__(self, player, data_dir="data"):
        """
        Initialize the AchievementSystem for the given player.
        """
        self.player = player
        self.data_dir = data_dir
        self.achievements = {}  # id -> achievement data
        self.titles = {}
        self.recent_unlocks = []
        self.load_achievements_data()
        self.load_titles()
    
    def load_achievements_data(self):
        categories = {
            "combat": "achievements/combat.json",
            "exploration": "achievements/exploration.json",
            "collection": "achievements/collection.json",
            "progression": "achievements/progression.json"
        }
        for cat, rel in categories.items():
            path = os.path.join(self.data_dir, rel)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                continue
            for aid, ad in data.items():
                ad["id"] = aid
                ad["category"] = cat
                self.achievements[aid] = ad
        # initialise les sets dans le player s’ils n’existent pas
        self.player.unlocked_achievements = getattr(self.player, "unlocked_achievements", set())
        self.player.achievement_progress = getattr(self.player, "achievement_progress", {})
    
    def load_titles(self):
        """
        Charge les titres depuis titles/titles.json.
        """
        path = os.path.join(self.data_dir, "titles", "titles.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        for title_id, title_data in data.items():
            self.titles[title_id] = dict(title_data)
    
    def create_template_file(self, file_path):
        """
        Create a template JSON file for achievements.
        """
        template = [{
            "id": "achv_001",
            "name": "Example Achievement",
            "category": "kill",
            "action": "orc",
            "threshold": 100,
            "description": "Kill 100 orcs"
        }]
        with open(file_path, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"Achievements template created at {file_path}.")
    
    def check_and_unlock(self, category, action, value=1):
        """
        Update achievements of a category with the given action and value, unlocking if threshold met.
        """
        for ach in self.achievements.values():
            if ach.get('category') == category and ach.get('action') == action:
                ach_id = ach['id']
                self.update_progress(ach_id, value)
                if self.get_progress(ach_id) >= ach.get('threshold', 0):
                    self.unlock(ach_id)
    
    def unlock(self, achievement_id):
        if achievement_id not in self.achievements:
            return
        if achievement_id in self.player.unlocked_achievements:
            return
        self.player.unlocked_achievements.add(achievement_id)
        self.recent_unlocks.append(achievement_id)
        if len(self.recent_unlocks) > 10:
            self.recent_unlocks.pop(0)
        ach = self.achievements[achievement_id]
        print(colored(f"Accomplissement débloqué : {ach.get('name')}", "green"))
        title_id = ach.get('title_id')
        if title_id:
            self.award_title(title_id)
    
    def get_recent_unlocks(self):
        """Retourne la liste des derniers accomplissements débloqués."""
        return [self.achievements[aid] for aid in self.recent_unlocks]

    def check_and_unlock(self, category, action, value=1):
        """
        Exemple de logique : pour chaque accomplissement de cette catégorie,
        si son trigger correspond à action et que la valeur atteint son goal,
        on le débloque.
        """
        for ach in self.achievements.values():
            if ach["category"] != category:
                continue
            if ach.get("trigger") != action:
                continue
            prog = self.player.achievement_progress.get(ach["id"], 0) + value
            self.player.achievement_progress[ach["id"]] = prog
            if prog >= ach.get("goal", float('inf')):
                self.unlock(ach["id"])

    def get_achievement_by_id(self, achievement_id):
        """
        Retrieve an achievement by its ID.
        """
        return self.achievements.get(achievement_id)
    
    def get_achievements_by_category(self, category):
        """
        List achievements in a given category.
        """
        return [ach for ach in self.achievements.values() if ach.get('category') == category]
    
    def get_unlocked_achievements(self):
        """
        Return a list of unlocked achievement objects.
        """
        return [self.achievements[aid] for aid in self.player.unlocked_achievements]
    
    def get_progress(self, achievement_id):
        """
        Get the current progress for an achievement.
        """
        return self.player.achievement_progress.get(achievement_id, 0)
    
    def update_progress(self, ach_id, value):
        """
        Met à jour la progression de l'accomplissement.
        Si l'objectif est atteint, passe l'accomplissement en débloqué.
        """
        if ach_id not in self.player.achievement_progress:
            return
        self.player.achievement_progress[ach_id] += value
        ach = self.achievements.get(ach_id)
        if not ach:
            return
        goal = ach.get("goal", None)
        if goal is not None and self.player.achievement_progress[ach_id] >= goal and ach_id not in self.player.unlocked_achievements:
            # Débloquer l'accomplissement
            self.player.unlocked_achievements.add(ach_id)
            # Éventuellement, notifier le joueur ou lui attribuer des récompenses
    
    def display_achievements(self, category=None):
        """
        Display all achievements or those in a category, marking unlocked ones.
        """
        for ach in self.achievements.values():
            if category and ach.get('category') != category:
                continue
            status = "Unlocked" if ach['id'] in self.player.unlocked_achievements else "Locked"
            print(f"{ach.get('name')}: {status} (Progress: {self.get_progress(ach['id'])}/{ach.get('threshold')})")
    
    def display_recent_unlocks(self):
        """
        Display recently unlocked achievements.
        """
        print("Recent Achievements Unlocked:")
        for aid in self.recent_unlocks:
            ach = self.achievements.get(aid)
            print(f"- {ach.get('name')}")
        self.recent_unlocks.clear()
    
    def check_kill_achievements(self, monster_type, monster_level):
        """
        Check achievements related to killing monsters.
        """
        self.check_and_unlock('kill', monster_type, 1)
    
    def check_exploration_achievements(self, location_type):
        """
        Check achievements related to exploration.
        """
        self.check_and_unlock('exploration', location_type, 1)
    
    def check_item_achievements(self, item_type, rarity):
        """
        Check achievements related to item usage or collection.
        """
        key = f"{item_type}_{rarity}"
        self.check_and_unlock('item', key, 1)
    
    def check_skill_achievements(self, skill_name, skill_level):
        """
        Check achievements related to skill usage.
        """
        key = f"{skill_name}_{skill_level}"
        self.check_and_unlock('skill', key, 1)
    
    def check_quest_achievements(self, quest_id):
        """
        Check achievements related to quests.
        """
        self.check_and_unlock('quest', quest_id, 1)
    
    def check_combat_achievements(self, combat_stats: dict):
        """
        Check achievements related to combat performance (e.g., fast wins, combos).
        """
        # Example: if combat finished in few turns
        turns = combat_stats.get('turns', 0)
        if turns <= 3:
            self.check_and_unlock('combat', 'quick_win', 1)
        damage = combat_stats.get('damage_dealt', 0)
        if damage >= 100:
            self.check_and_unlock('combat', 'high_damage', damage)
    
    def check_title_unlock_conditions(self):
        """
        Check global conditions for title unlocks (not tied to specific achievements).
        """
        # Placeholder: check player's stats or achievements to award titles
        if self.player.level >= 50 and 'Veteran' not in self.player.titles:
            self.player.titles.append('Veteran')
            print("Title awarded: Veteran")
    
    def award_title(self, title_id):
        """
        Award a title to the player.
        """
        # Title_id maps to a title name in some title list; simplified here
        title_name = title_id  # Assuming title_id is title name
        if title_name not in self.player.titles:
            self.player.titles.append(title_name)
            print(f"Title unlocked: {title_name}")
    
    def detect_playstyle(self):
        """
        Detect player's preferred playstyle based on achievements or actions.
        """
        # Placeholder: simple heuristic
        combat_count = sum(1 for ach in self.get_unlocked_achievements() if ach.get('category') == 'kill')
        exploration_count = sum(1 for ach in self.get_unlocked_achievements() if ach.get('category') == 'exploration')
        if combat_count > exploration_count:
            return 'Warrior'
        else:
            return 'Explorer'
    
    def generate_personal_challenge(self):
        """
        Generate a personal challenge based on playstyle or achievement gaps.
        """
        style = self.detect_playstyle()
        if style == 'Warrior':
            challenge = "Defeat 50 elite monsters"
        else:
            challenge = "Discover 10 new locations"
        return challenge
    
    def serialize(self):
        """
        Convert the achievement system state to savable format.
        """
        return {
            'unlocked': list(self.player.unlocked_achievements),
            'progress': self.player.achievement_progress
        }
    
    def deserialize(self, data):
        """
        Load the achievement system state from saved data.
        """
        self.player.unlocked_achievements = set(data.get('unlocked', []))
        self.player.achievement_progress = data.get('progress', {})
