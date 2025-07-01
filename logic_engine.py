"""
logic_engine.py - Adaptive AI and content generation for FateQuest.
Analyzes player behavior, adjusts difficulty, and generates dynamic content.
"""
import os
import random
import json

class LogicEngine:
    """
    Adaptive logic engine tracking player actions to influence game experience.
    """
    def __init__(self, player, world, monster_manager, achievement_system, data_dir='data'):
        """
        Initialize the logic engine with references to game components.
        """
        self.data_dir = data_dir
        self.player = player
        self.world = world
        self.monster_manager = monster_manager
        self.achievement_system = achievement_system
        self.action_log = []  # list of (action_type, context) tuples
        # Charger configs système
        self.rarity_config = self.load_system_config("system/rarity_config.json")
        self.difficulty_scales = self.load_system_config("system/difficulty_scales.json")
        self.analysis_data = {}
        self._difficulty_level = 1
        self.difficulty_modifier= self.get_difficulty_modifier()
    
    def load_system_config(self, rel_path):
        path = os.path.join(self.data_dir, rel_path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def analyze_player_behavior(self):
        """
        Analyze logged actions to adjust difficulty and content.
        """
        patterns = {
            'skill': self.detect_skill_usage_pattern(),
            'exploration': self.detect_exploration_pattern(),
            'combat': self.detect_combat_pattern(),
            'inventory': self.detect_inventory_management_pattern()
        }
        playstyle = self.identify_preferred_playstyle()
        return patterns, playstyle
    
    def identify_preferred_playstyle(self):
        """
        Identify the player's preferred playstyle (e.g., "Combat", "Explorer").
        """
        counts = {}
        for action, ctx in self.action_log:
            counts[action] = counts.get(action, 0) + 1
        if counts.get('combat', 0) > counts.get('explore', 0):
            return 'Combat-Oriented'
        else:
            return 'Exploration-Oriented'
    
    def adjust_difficulty(self):
        """
        Adjust the difficulty modifier based on player performance.
        """
        # Simple: if player has high experience and few deaths, raise difficulty
        exp = getattr(self.player, 'experience', 0)
        level = getattr(self.player, 'level', 1)
        wins = getattr(self.player, 'wins', 0)
        deaths = getattr(self.player, 'deaths', 0)
        if wins > deaths:
            self.difficulty_modifier = min(self.difficulty_modifier + 0.1, 2.0)
        else:
            self.difficulty_modifier = max(self.difficulty_modifier - 0.1, 0.5)
    
    def get_difficulty_modifier(self):
        """
        Return the current difficulty modifier.
        """
        scales = self.difficulty_scales or {}
        key = str(self._difficulty_level)
        if key in scales:
            return scales[key]
        # fallback : palier inférieur le plus proche
        levels = sorted(int(k) for k in scales.keys())
        for lvl in reversed(levels):
            if lvl <= self._difficulty_level:
                return scales[str(lvl)]
        return 1.0  # valeur par défaut
    
    def suggest_content(self):
        """
        Suggest new content (quests, challenges) based on player patterns.
        """
        playstyle = self.identify_preferred_playstyle()
        if playstyle == 'Combat-Oriented':
            return "Consider taking on the Dragon's Den quest for a challenge."
        else:
            return "Explore the Mystic Forest to uncover hidden secrets."
    
    def track_action(self, action_type, context=None):
        """
        Track a player's action with optional context for pattern analysis.
        """
        self.action_log.append((action_type, context))
    
    def calculate_action_patterns(self):
        """
        Calculate and return patterns from the action log.
        """
        pattern_counts = {}
        for action, context in self.action_log:
            pattern_counts[action] = pattern_counts.get(action, 0) + 1
        return pattern_counts
    
    def detect_skill_usage_pattern(self):
        """
        Detect pattern in skill usage (e.g., frequent skill usage).
        """
        skill_actions = [ctx for act, ctx in self.action_log if act == 'skill']
        if len(skill_actions) > 10:
            return "High skill usage"
        return "Normal skill usage"
    
    def detect_exploration_pattern(self):
        """
        Detect pattern in exploration (e.g., new areas vs revisits).
        """
        explore_actions = [ctx for act, ctx in self.action_log if act == 'explore']
        unique_places = set(explore_actions)
        if len(unique_places) > 5:
            return "Curious explorer"
        return "Standard exploration"
    
    def detect_combat_pattern(self):
        """
        Detect combat pattern (aggressive or defensive).
        """
        combat_actions = [ctx for act, ctx in self.action_log if act == 'combat']
        if len(combat_actions) > 20:
            return "Battler"
        return "Balanced combat"
    
    def detect_inventory_management_pattern(self):
        """
        Detect inventory management patterns (e.g., hoarder vs spender).
        """
        inv_actions = [ctx for act, ctx in self.action_log if act == 'inventory']
        if len(inv_actions) > 15:
            return "Collector"
        return "Minimalist"
    
    def unlock_hidden_content(self, content_type):
        """
        Unlock hidden or secret content for the player.
        """
        print(f"Hidden content unlocked: {content_type}")
    
    def check_class_upgrade_eligibility(self):
        """
        Check if player qualifies for advanced classes.
        """
        if self.player.level >= 30:
            print("You qualify for a class upgrade quest!")
    
    def check_secret_quest_trigger(self):
        """
        Check if conditions are met to trigger a secret quest.
        """
        patterns, playstyle = self.analyze_player_behavior()
        if patterns['combat'] == "Battler" and 'Dragon' not in self.player.quests:
            return "Dragon Slayer Quest"
        return None
    
    def generate_adaptive_quest(self):
        """
        Generate a quest tailored to the player's style and progress.
        """
        style = self.identify_preferred_playstyle()
        if style == 'Combat-Oriented':
            quest = {"name": "Arena Champion", "difficulty": int(10 * self.difficulty_modifier)}
        else:
            quest = {"name": "Herbalist Path", "difficulty": int(5 * self.difficulty_modifier)}
        return quest
    
    def update_world_reaction(self):
        """
        Update world state based on player's actions (e.g., NPC reputation).
        """
        # Placeholder: reduce NPC friendliness if player has attacked innocents
        if getattr(self.player, 'notoriety', 0) > 5:
            print("NPCs view you as dangerous.")
    
    def calculate_challenge_rating(self, threat_level=1, complexity=1):
        """
        Calculate a challenge rating for content.
        """
        return int(threat_level * complexity * self.difficulty_modifier)
    
    def check_special_encounter_conditions(self):
        """
        Check if special encounters (e.g., mini-boss, event) should occur.
        """
        if len(self.player.inventory) > 20 and random.random() < 0.1:
            return "Bandit Ambush"
        return None
    
    def generate_unique_encounter(self):
        """
        Generate a unique encounter or event for the player.
        """
        encounter = {"type": "mystic_event", "reward": int(100 * self.difficulty_modifier)}
        return encounter
    
    def adapt_npc_interactions(self, npc_id):
        """
        Adapt NPC interactions based on player's reputation or choices.
        """
        rep = self.world.get_npc_reputation(npc_id, self.player)
        if rep < 0:
            return "Hostile"
        return "Friendly"
    
    def update_threat_level(self, region):
        """
        Update global or regional threat levels based on game events.
        """
        # Placeholder: increase threat over time
        self.world.threat_level = getattr(self.world, 'threat_level', 0) + 1
    
    def detect_combat_prowess(self):
        """
        Evaluate player's combat ability.
        """
        wins = getattr(self.player, 'wins', 0)
        losses = getattr(self.player, 'deaths', 0)
        if wins + losses == 0:
            return 0
        return wins / (wins + losses)
    
    def calibrate_rewards(self):
        """
        Adjust reward values for loot and XP based on player performance.
        """
        if self.player.level < 10:
            return 1.0
        return 1.0 / self.difficulty_modifier
    
    def serialize_analysis_data(self):
        """
        Serialize analysis data to JSON.
        """
        data = {
            'action_log': self.action_log,
            'difficulty_modifier': self.difficulty_modifier
        }
        return json.dumps(data)
    
    def deserialize_analysis_data(self, data):
        """
        Load analysis data from JSON.
        """
        loaded = json.loads(data)
        self.action_log = loaded.get('action_log', [])
        self.difficulty_modifier = loaded.get('difficulty_modifier', 1.0)
