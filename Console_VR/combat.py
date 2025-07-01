"""
combat.py - Advanced turn-based combat system for FateQuest.
Handles player vs enemy battles, skills, items, combos, statuses, and outcomes.
"""

import random
from typing import Optional, List

class Combat:
    """
    Combat system managing turn-based battles between the player and enemies.
    """
    def __init__(self, player, monster_manager, item_manager, achievement_system):
        """
        Initialize the combat system with references to player, monster manager,
        item manager, and achievement system.
        """
        self.player = player
        self.monster_manager = monster_manager
        self.item_manager = item_manager
        self.achievement_system = achievement_system
        
        self.enemy = None  # Current enemy object
        self.enemy_original = None  # Template for enemy
        self.combat_active = False
        self.player_turn = True
        self.turn_count = 0
        self.skill_history: List[str] = []  # For combo tracking
        self.status_effects = []  # Active status effects affecting combat
        self.environment_effects = []  # Environmental effects for the battle
        
        # Example combo definitions: sequences of skills leading to combo effects
        self.combos = {
            ('Power Strike', 'Flurry'): 'Thunderous Combo',
            ('Fireball', 'Ignite'): 'Firestorm',
        }
        
    def start_combat(self, enemy):
        """
        Initiate combat with a given enemy (id, template, or object).
        """
        # Prepare enemy data
        self.enemy = self._prepare_enemy(enemy)
        self.combat_active = True
        self.player_turn = True  # Player starts
        
        # Apply title effects or history modifications if any
        self._apply_title_effects()
        self._calculate_history_modifier()
        
        # Check for surprise attacks
        if self._check_surprise_attack():
            print(f"Surprise attack! {self.enemy['name']} strikes first!")
            self.player_turn = False
        
        # Combat loop: alternate turns until combat ends
        while self.combat_active:
            self.turn_count += 1
            # Player turn
            if self.player_turn:
                self._display_combat_status()
                # In actual game, user would input command; here assume higher-level calls
                # For demo, auto player attacks
                self._player_attack()
            else:
                # Enemy turn
                self._enemy_turn()
            
            # Update status effects after each full round
            self._update_status_effects()
            
            # Check end conditions
            if self.player.hp <= 0:
                self.combat_active = False
                print("Player has been defeated!")
                self.end_combat(fled=False)
                break
            if self.enemy and self.enemy['current_hp'] <= 0:
                self.combat_active = False
                print(f"{self.enemy['name']} defeated!")
                self._handle_drops()
                self._check_combat_achievements()
                self.end_combat(fled=False)
                break
            
            # Toggle turn
            self.player_turn = not self.player_turn
    
    def _prepare_enemy(self, enemy_template):
        """
        Prepare an enemy instance for combat from a template or ID.
        """
        if isinstance(enemy_template, dict):
            # Assume already a template; apply variations
            base_enemy = enemy_template.copy()
        else:
            # Could be an ID or key, use monster_manager to get template
            base_enemy = self.monster_manager.get_enemy(enemy_template)
        # Deep copy to not modify original data
        enemy = base_enemy.copy()
        # Initialize current HP and stats
        enemy['current_hp'] = enemy.get('hp', 0)
        enemy['level'] = enemy.get('level', 1)
        enemy['status_effects'] = []
        return enemy
    
    def _apply_title_effects(self):
        """
        Apply any combat modifiers based on player's titles.
        """
        # Example: if player has title 'Orc Slayer', increase damage vs orcs
        for title in self.player.titles:  # Assume player has list of titles
            if title == "Chasseur d'Orcs" and self.enemy.get('race') == 'Orc':
                print("Title effect: Extra damage to Orcs!")
                # e.g., boost player's damage stat temporarily
                self.player.attack += 5
    
    def _check_for_race_title(self, race: str) -> bool:
        """
        Check if player has a title related to the enemy's race.
        """
        return any(race in title for title in self.player.titles)
    
    def _calculate_history_modifier(self):
        """
        Calculate modifiers based on past encounters or history (e.g., repeated fights).
        """
        # Example: if player repeatedly fights same enemy type, minor stat changes
        pass  # Placeholder for history modifiers
    
    def _check_surprise_attack(self) -> bool:
        """
        Determine if a surprise attack occurs (enemy strikes first).
        """
        chance = 10  # 10% chance
        roll = random.randint(1, 100)
        return roll <= chance
    
    def process_command(self, command: str, args=None):
        """
        Process player command during combat.
        """
        if not self.combat_active:
            return
        cmd = command.lower()
        if cmd == "attack":
            self._player_attack()
        elif cmd == "defend":
            self._defend()
        elif cmd == "skill" and args:
            self._use_skill(args)
        elif cmd == "use" and args:
            self._use_item(args)
        elif cmd == "analyze":
            self._analyze_enemy()
        elif cmd == "escape":
            self._try_escape()
        else:
            print("Unknown command.")
    
    def _player_attack(self):
        """
        Player performs a basic attack on the enemy.
        """
        # Basic damage calculation: player's attack minus enemy defense
        atk = getattr(self.player, 'attack', 1)
        defense = self.enemy.get('defense', 0)
        damage = max(atk - defense, 1)
        self.enemy['current_hp'] -= damage
        print(f"You attack {self.enemy['name']} for {damage} damage.")
    
    def _use_skill(self, skill_name: str):
        """
        Player uses a skill by name.
        """
        skill = self.player.skills.get(skill_name)
        if not skill:
            print(f"You don't know skill '{skill_name}'.")
            return
        # Process based on skill type
        skill_type = skill.get('type')
        print(f"You use {skill_name}.")
        if skill_type == 'damage':
            self._process_damage_skill(skill)
        elif skill_type == 'heal':
            self._process_heal_skill(skill)
        elif skill_type == 'buff':
            self._process_buff_skill(skill)
        elif skill_type == 'debuff':
            self._process_debuff_skill(skill)
        elif skill_type == 'special':
            self._process_special_skill(skill)
        # Record skill use for combo detection
        self._record_skill_use(skill_name)
    
    def _process_damage_skill(self, skill_data: dict):
        """
        Handle a damage-dealing skill.
        """
        power = skill_data.get('power', 0)
        enemy_def = self.enemy.get('defense', 0)
        damage = max(power - enemy_def, 1)
        self.enemy['current_hp'] -= damage
        print(f"{self.enemy['name']} takes {damage} damage from skill.")
    
    def _process_heal_skill(self, skill_data: dict):
        """
        Handle a healing skill.
        """
        amount = skill_data.get('power', 0)
        self.player.hp = min(self.player.hp + amount, self.player.max_hp)
        print(f"You heal yourself for {amount} HP.")
    
    def _process_buff_skill(self, skill_data: dict):
        """
        Handle a buff skill (increases player stats temporarily).
        """
        stat = skill_data.get('stat')
        amount = skill_data.get('amount', 0)
        duration = skill_data.get('duration', 3)
        # Example buff effect
        self.status_effects.append({'target': 'player', 'stat': stat, 'amount': amount, 'duration': duration})
        print(f"You buff yourself: {stat} +{amount} for {duration} turns.")
    
    def _process_debuff_skill(self, skill_data: dict):
        """
        Handle a debuff skill (decreases enemy stats).
        """
        stat = skill_data.get('stat')
        amount = skill_data.get('amount', 0)
        duration = skill_data.get('duration', 3)
        self.enemy['status_effects'].append({'target': 'enemy', 'stat': stat, 'amount': -amount, 'duration': duration})
        print(f"{self.enemy['name']}'s {stat} decreased by {amount} for {duration} turns.")
    
    def _process_special_skill(self, skill_data: dict):
        """
        Handle a special skill with unique effects.
        """
        effect = skill_data.get('effect', 'none')
        # Placeholder for special effects
        print(f"Special effect '{effect}' activated!")
    
    def _use_item(self, item_name: str):
        """
        Player uses an item from inventory.
        """
        item = self.player.find_item_by_name(item_name)
        if not item:
            print(f"You don't have {item_name}.")
            return
        # Use the item (e.g. potion, scroll)
        self.item_manager.use_item(item, self.player)
        print(f"You use {item_name}.")
    
    def _defend(self):
        """
        Player defends, reducing incoming damage.
        """
        self.player.defending = True
        print("You brace for the next attack, reducing incoming damage.")
    
    def _analyze_enemy(self):
        """
        Player analyzes the enemy, revealing information.
        """
        desc = self.monster_manager.get_monster_description(self.enemy)
        print(desc)
    
    def _try_escape(self):
        """
        Player attempts to flee from combat.
        """
        chance = 50  # 50% base escape chance
        roll = random.randint(1, 100)
        if roll <= chance:
            print("You successfully escaped!")
            self.end_combat(fled=True)
        else:
            print("Escape failed!")
    
    def _display_combat_status(self):
        """
        Display current HP/status bars for player and enemy.
        """
        bar_width = 20
        def bar(current, maximum):
            filled = int(bar_width * current / maximum)
            return '[' + '#' * filled + ' ' * (bar_width - filled) + ']'
        print(f"Player HP: {bar(self.player.hp, self.player.max_hp)} {self.player.hp}/{self.player.max_hp}")
        print(f"{self.enemy['name']} HP: {bar(self.enemy['current_hp'], self.enemy['hp'])} {self.enemy['current_hp']}/{self.enemy['hp']}")
    
    def _create_bar(self, percent, width, char, color=None):
        """
        Create a textual bar (unused in this context, as we built one above).
        """
        filled = int(width * percent)
        return char * filled + '-' * (width - filled)
    
    def _show_available_skills(self):
        """
        List player's available skills during combat.
        """
        skills = ', '.join(self.player.skills.keys())
        print(f"Available skills: {skills}")
    
    def _enemy_turn(self):
        """
        Execute enemy actions on its turn.
        """
        if not self._check_enemy_can_act():
            print(f"{self.enemy['name']} is unable to act!")
            return
        action = self._decide_enemy_action()
        if action == 'attack':
            self._enemy_attack()
        elif action == 'skill':
            self._enemy_use_skill()
        elif action == 'heal':
            self._enemy_heal()
    
    def _update_status_effects(self):
        """
        Update or apply status effects each turn.
        """
        for effect in list(self.status_effects):
            # Example: buff on player
            target = effect['target']
            if target == 'player' and effect['duration'] > 0:
                setattr(self.player, effect['stat'], getattr(self.player, effect['stat'], 0) + effect['amount'])
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    self.status_effects.remove(effect)
        # Update enemy status effects
        for effect in list(self.enemy['status_effects']):
            if effect['duration'] > 0:
                setattr(self.enemy, effect['stat'], self.enemy.get(effect['stat'], 0) + effect['amount'])
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    self.enemy['status_effects'].remove(effect)
    
    def _check_enemy_can_act(self) -> bool:
        """
        Determine if the enemy is able to take an action (e.g., not stunned).
        """
        # If enemy has a 'stun' in status effects, cannot act
        for effect in self.enemy['status_effects']:
            if effect.get('stat') == 'stun' and effect.get('amount', 0) < 0:
                return False
        return True
    
    def _decide_enemy_action(self):
        """
        Decide the enemy's next action based on simple AI.
        """
        # Simple logic: if enemy HP low, try heal; else random between attack/skill
        hp_ratio = self.enemy['current_hp'] / self.enemy['hp']
        if hp_ratio < 0.3 and 'heal' in self.enemy.get('abilities', []):
            return 'heal'
        if random.random() < 0.7:
            return 'attack'
        elif 'abilities' in self.enemy and self.enemy['abilities']:
            return 'skill'
        else:
            return 'attack'
    
    def _enemy_attack(self):
        """
        Enemy performs a basic attack on the player.
        """
        atk = self.enemy.get('attack', 1)
        defense = getattr(self.player, 'defense', 0)
        damage = max(atk - defense, 1)
        # If player defended last turn, reduce damage
        if getattr(self.player, 'defending', False):
            damage = max(int(damage / 2), 1)
            self.player.defending = False
        self.player.hp -= damage
        print(f"{self.enemy['name']} attacks you for {damage} damage.")
    
    def _enemy_use_skill(self):
        """
        Enemy uses a special ability against the player.
        """
        abilities = self.enemy.get('abilities', [])
        if not abilities:
            self._enemy_attack()
            return
        skill = random.choice(abilities)
        # For simplicity, treat as damage skill
        power = skill.get('power', 0) if isinstance(skill, dict) else 5
        defense = getattr(self.player, 'defense', 0)
        damage = max(power - defense, 1)
        self.player.hp -= damage
        print(f"{self.enemy['name']} uses {skill.get('name', 'skill')} dealing {damage} damage.")
    
    def _enemy_heal(self):
        """
        Enemy attempts to heal itself.
        """
        amount = self.enemy.get('heal_power', 5)
        self.enemy['current_hp'] = min(self.enemy['current_hp'] + amount, self.enemy['hp'])
        print(f"{self.enemy['name']} heals for {amount} HP.")
    
    def end_combat(self, fled: bool=False):
        """
        Clean up after combat ends.
        """
        self.combat_active = False
        if fled:
            print("You fled the combat.")
        else:
            print("Combat has ended.")
        # Reset defending flag
        self.player.defending = False
    
    def _handle_drops(self):
        """
        Handle loot drops when an enemy is defeated.
        """
        loot = []
        if 'loot_table' in self.enemy:
            for item_info in self.enemy['loot_table']:
                chance = item_info.get('chance', 100)
                roll = random.randint(1, 100)
                if roll <= chance:
                    loot.append(item_info.get('item_id'))
        # Give loot to player
        for item_id in loot:
            item = self.item_manager.get_item_by_id(item_id)
            self.player.add_item(item)
            print(f"You obtained {item.get('name')} from the loot.")
    
    def _check_combat_achievements(self):
        """
        Check if any achievements are fulfilled by this combat.
        """
        stats = {'turns': self.turn_count, 'damage_dealt': None}  # Example stats
        self.achievement_system.check_combat_achievements(stats)
    
    def _check_skill_combos(self, skill_name: str) -> Optional[str]:
        """
        Check if using a skill finishes a special combo.
        """
        for combo_skills, combo_name in self.combos.items():
            if len(self.skill_history) >= len(combo_skills):
                # get last n skills
                if tuple(self.skill_history[-len(combo_skills):]) == combo_skills:
                    return combo_name
        return None
    
    def _apply_combo_effects(self, combo_name: str):
        """
        Apply special effects from a skill combo.
        """
        print(f"Combo {combo_name} activated! Extra effects apply.")
        # Example: double damage next attack
        if combo_name == 'Firestorm':
            # Increase next damage
            self.player.attack *= 2
    
    def _record_skill_use(self, skill_name: str):
        """
        Record a skill use for combo detection.
        """
        self.skill_history.append(skill_name)
        # Limit history length
        if len(self.skill_history) > 5:
            self.skill_history.pop(0)
        # Check for combos
        combo = self._check_skill_combos(skill_name)
        if combo:
            self._apply_combo_effects(combo)
    
    def _check_environmental_effects(self):
        """
        Apply any environmental effects in the battle.
        """
        for effect in self.environment_effects:
            print(f"Environmental effect: {effect}")
