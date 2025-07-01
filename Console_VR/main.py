#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Boucle principale et gestion des états pour FateQuest
"""

import sys
import time
import os 
from colorama import init, Fore, Back, Style
from player import Player
from world import World
from combat import Combat
from items import ItemManager
from monsters import MonsterManager
from achievements import AchievementSystem
from logic_engine import LogicEngine
from save_system import SaveSystem

class Game:
    def __init__(self):
        """Initialise tous les systèmes du jeu sans charger de partie."""
        self.player = None
        self.world = None
        self.combat = None
        self.item_manager = ItemManager()
        self.monster_manager = MonsterManager()
        self.achievement_system = None
        self.logic_engine = None
        self.save_system = SaveSystem()
        self.handle_state_transition('menu')  # modes: menu, game, combat, inventory, shop, dialogue, crafting
        self.running = True
        self.current_save_slot = 1
    
    def initialize_game(self, new_game: bool):
        """Configure tous les systèmes après création ou chargement du joueur."""
        if new_game:
            self.player = self.create_new_player()
        else:
            data = self.save_system.load_game(self.current_save_slot)
            if not data:
                print("Échec du chargement, nouvelle partie lancée.")
                self.player = self.create_new_player()
            else:
                # reconstruire Player
                self.player = Player.load_from_data(data['player'], self.item_manager)
                # restaurer achievements
                self.achievement_system = AchievementSystem(self.player)
                self.achievement_system.deserialize(data.get('achievements', {}))
                # restaurer logique adaptative
                self.logic_engine = LogicEngine(self.player, None, self.monster_manager, self.achievement_system)
                self.logic_engine.deserialize_analysis_data(data.get('analysis', '{}'))
        # instancie les systèmes dépendants du joueur
        if not self.achievement_system:
            self.achievement_system = AchievementSystem(self.player)
        if not self.logic_engine:
            self.logic_engine = LogicEngine(self.player, None, self.monster_manager, self.achievement_system)
        # créer le monde et le combat
        self.world = World(self.player, self.monster_manager, self.item_manager)
        # passer le monde au logic_engine
        self.logic_engine.world = self.world
        self.combat = Combat(self.player, self.monster_manager, self.item_manager, self.achievement_system)
        self.handle_state_transition('game')
    
    def create_new_player(self) -> Player:
        """Interface console pour créer un nouveau personnage."""
        name = input("Entrez le nom de votre héro: ").strip()
        print("Choisissez une classe: ")
        for cls in Player.base_classes:
            print(f" - {cls}")
        choice = input("Classe: ").strip().title()
        if choice not in Player.base_classes:
            print("Classe inconnue, Guerrier sélectionné par défaut.")
            choice = 'Warrior'
        player = Player(name, choice)
        print(f"Bienvenue {name} le {choice}!")
        return player
    
    def print_welcome(self):
        """Display the welcome screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        ascii_logo = """
    ███████╗ █████╗ ████████╗███████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗
    ██╔════╝██╔══██╗╚══██╔══╝██╔════╝██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
    █████╗  ███████║   ██║   █████╗  ██║   ██║██║   ██║█████╗  ███████╗   ██║   
    ██╔══╝  ██╔══██║   ██║   ██╔══╝  ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   
    ██║     ██║  ██║   ██║   ███████╗╚██████╔╝╚██████╔╝███████╗███████║   ██║   
    ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   
        """
        
        print(Fore.CYAN + ascii_logo)
        print(Fore.YELLOW + "=" * 75)
        print(Fore.YELLOW + "Welcome to the world of FateQuest - A text-based RPG adventure!")
        print(Fore.YELLOW + "Your destiny awaits as you forge your path in this magical realm.")
        print(Fore.YELLOW + "=" * 75 + "\n")
        print("1. Nouvelle partie")
        print("2. Charger partie")
        print("3. Quitter")
    
    def main_menu(self):
        """Gère le menu principal avant le lancement du jeu."""
        while self.state == 'menu':
            self.print_welcome()
            choice = input("> ").strip()
            if choice == '1':
                self.initialize_game(new_game=True)
            elif choice == '2':
                slot = input("Numéro de slot à charger: ").strip()
                if slot.isdigit():
                    self.current_save_slot = int(slot)
                self.initialize_game(new_game=False)
            elif choice == '3':
                self.running = False
                return
            else:
                print("Choix invalide.")
    
    def run(self):
        """Boucle principale du jeu."""
        while self.running:
            if self.state == 'menu':
                self.main_menu()
                continue
            elif self.state == 'game':
                cmd = input("(exploration) > ").strip().lower()
                self.logic_engine.track_action('explore', cmd)
                self.process_game_command(cmd)
            elif self.state == 'combat':
                cmd = input("(combat) > ").strip().lower()
                self.logic_engine.track_action('combat', cmd)
                self.process_combat_command(cmd)
            elif self.state == 'inventory':
                cmd = input("(inventaire) > ").strip().lower()
                self.logic_engine.track_action('inventory', cmd)
                self.process_inventory_command(cmd)
            elif self.state == 'shop':
                cmd = input("(boutique) > ").strip().lower()
                self.logic_engine.track_action('shop', cmd)
                self.process_shop_command(cmd)
            elif self.state == 'dialogue':
                cmd = input("(dialogue) > ").strip().lower()
                self.logic_engine.track_action('dialogue', cmd)
                self.process_dialogue_command(cmd)
            elif self.state == 'crafting':
                cmd = input("(artisanat) > ").strip().lower()
                self.logic_engine.track_action('crafting', cmd)
                self.process_crafting_command(cmd)
            # Après chaque interaction, ajuster la difficulté et afficher une suggestion
            self.logic_engine.adjust_difficulty()
            suggestion = self.logic_engine.suggest_content()
            print(f"[Suggestion] {suggestion}")
    
    def process_game_command(self, command: str):
        """Traite les commandes en mode exploration."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd in ('aller', 'move'):
            if args:
                if self.world.move_to(args[0]):
                    pass
            else:
                print("Usage: aller <direction>")
        elif cmd in ('examiner', 'examine'):
            if args:
                self.world.interact_with_object(' '.join(args))
            else:
                print("Usage: examiner <objet>")
        elif cmd in ('inventaire', 'inv'):
            self.handle_state_transition('inventory')
        elif cmd in ('parler', 'talk'):
            if args:
                self.world.talk_to_npc(' '.join(args))
                self.handle_state_transition('dialogue')
            else:
                print("Usage: parler <nom_pnj>")
        elif cmd in ('boutique', 'shop'):
            if args:
                self.world.open_shop(' '.join(args))
                self.handle_state_transition('shop')
            else:
                print("Usage: boutique <nom_pnj>")
        elif cmd in ('combattre', 'fight'):
            if self.world.current_enemies:
                enemy = self.world.current_enemies[0]
                self.start_combat(enemy)
            else:
                print("Aucun ennemi ici.")
        elif cmd in ('artisanat', 'craft'):
            self.handle_state_transition('crafting')
        elif cmd in ('quitter', 'quit'):
            self.confirm_quit()
        elif cmd in ('event', 'hasard'):
            self.trigger_random_event()
        elif cmd in ('aide', 'help'):
            self.show_help()
        elif cmd in ('examiner_cible', 'inspecter') and args:
            self.examine_target(' '.join(args))

        else:
            print("Commande inconnue en exploration. Tapez 'aide' pour lister les commandes.")
    
    def process_combat_command(self, command: str):
        """Traite les commandes en mode combat."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        self.combat.process_command(cmd, args)
        if not self.combat.combat_active:
            self.handle_state_transition('game')
    
    def process_inventory_command(self, command: str):
        """Traite les commandes en mode inventaire."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd == 'voir':
            self.player.display_inventory()
        elif cmd == 'utiliser' and args:
            self.player.use_item(' '.join(args))
        elif cmd == 'équiper' and args:
            self.player.equip_item(' '.join(args))
        elif cmd == 'déséquiper' and args:
            self.player.unequip_item(args[0])
        elif cmd in ('retour', 'back'):
            self.handle_state_transition('game')
        else:
            print("Commande inconnue en inventaire.")
    
    def process_shop_command(self, command: str):
        """Traite les commandes en mode boutique."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd in ('acheter', 'buy') and args:
            idx = int(args[0])
            # on suppose qu'on a gardé le dernier NPC consulté
            self.world.buy_item(self.world.current_npcs[0]['name'], idx)
        elif cmd in ('vendre', 'sell') and args:
            self.world.sell_item(self.world.current_npcs[0]['name'], ' '.join(args))
        elif cmd in ('retour', 'back'):
            self.handle_state_transition('game')
        else:
            print("Commande inconnue en boutique.")
    
    def process_dialogue_command(self, command: str):
        """Traite les commandes en mode dialogue."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd in ('sujets', 'topics'):
            self.world.discuss_topic(self.world.current_npcs[0]['name'], ' '.join(args))
        elif cmd in ('discuter', 'talk'):
            if args:
                self.world.talk_to_npc(' '.join(args))
            else:
                print("Usage: discuter <sujet>")
        elif cmd in ('accepter', 'accept'):
            self.world.accept_quest(self.world.current_npcs[0]['name'])
        elif cmd in ('retour', 'back'):
            self.handle_state_transition('game')
        else:
            print("Commande inconnue en dialogue.")
    
    def process_crafting_command(self, command: str):
        """Traite les commandes en mode artisanat."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd in ('creer', 'craft') and args:
            self.item_manager.craft_item(args[0], self.player)
        elif cmd in ('démanteler', 'dismantle') and args:
            item = self.player.find_item_by_name(' '.join(args))
            if item:
                self.item_manager.dismantle_item(item, self.player)
        elif cmd in ('retour', 'back'):
            self.handle_state_transition('game')
        else:
            print("Commande inconnue en artisanat.")
    
    def confirm_quit(self):
        """Demande confirmation avant de quitter et sauvegarde."""
        ans = input("Voulez-vous sauvegarder avant de quitter ? (o/n) ").lower()
        if ans == 'o':
            self.save_game()
        print("Au revoir !")
        self.running = False
    
    def save_game(self):
        """Sauvegarde l'état actuel du jeu."""
        state = {
            'player': self.player.to_dict(),
            'achievements': self.achievement_system.serialize(),
            'analysis': self.logic_engine.serialize_analysis_data(),
            # tu peux ajouter world, NPC states, day_count, etc.
        }
        self.save_system.save_game(state, self.current_save_slot)
    
    def start_combat(self, enemy):
        """Transition vers le mode combat."""
        self.handle_state_transition('combat')
        self.combat.start_combat(enemy)
    
    def end_combat(self, fled=False):
        """Traite la fin du combat."""
        self.combat.end_combat(fled)
        self.handle_state_transition('game')

    def trigger_random_event(self):
        """Déclenche un événement aléatoire dans le monde."""
        print("[Système] Tentative de déclenchement d’un événement aléatoire...")
        self.world.random_event()

    def show_help(self):
        """Affiche les commandes disponibles selon l’état actuel."""
        print("=== Aide - Commandes disponibles ===")
        if self.state == 'game':
            print(" - aller <direction>")
            print(" - examiner <objet>")
            print(" - parler <pnj>")
            print(" - boutique <pnj>")
            print(" - combattre")
            print(" - inventaire")
            print(" - artisanat")
            print(" - aide")
            print(" - quitter")
        elif self.state == 'combat':
            print(" - attaque")
            print(" - compétence <nom>")
            print(" - objet <nom>")
            print(" - fuir")
        elif self.state == 'inventory':
            print(" - voir")
            print(" - utiliser <objet>")
            print(" - équiper <objet>")
            print(" - déséquiper <emplacement>")
            print(" - retour")
        elif self.state == 'shop':
            print(" - acheter <num>")
            print(" - vendre <objet>")
            print(" - retour")
        elif self.state == 'dialogue':
            print(" - discuter <sujet>")
            print(" - accepter (quête)")
            print(" - retour")
        elif self.state == 'crafting':
            print(" - creer <recette>")
            print(" - démanteler <objet>")
            print(" - retour")
        print("="*30)

    def examine_target(self, target_name: str):
        """Examine un ennemi, objet ou PNJ dans la zone actuelle."""
        # Ennemis
        for enemy in self.world.current_enemies:
            if enemy["name"].lower() == target_name.lower():
                print(f"{enemy['name']} - Niveau {enemy['level']}")
                print(enemy.get("description", "Aucune description disponible."))
                return
        
        # Objets
        for obj in self.world.interactive_objects:
            if obj["name"].lower() == target_name.lower():
                print(f"{obj['name']} : {obj['description']}")
                return
        
        # PNJ
        for npc in self.world.current_npcs:
            if npc["name"].lower() == target_name.lower():
                print(f"{npc['name']} : {npc['description']}")
                return

        print(f"Impossible d’examiner {target_name}. Aucun élément correspondant ici.")

    def handle_state_transition(self, new_state: str):
        """Gère les changements d’état avec vérifications éventuelles."""
        valid_states = ['menu', 'game', 'combat', 'inventory', 'dialogue', 'shop', 'crafting']
        if new_state not in valid_states:
            print(f"État invalide: {new_state}")
            return
        print(f"[Transition] Passage à l’état: {new_state}")
        self.state = new_state

    
if __name__ == "__main__":
    game = Game()
    game.run()
  

"""This `main.py` :

- Initialise tous les managers (`ItemManager`, `MonsterManager`, `AchievementSystem`, `LogicEngine`, `SaveSystem`), le `World` et le `Combat`.
- Gère les états : exploration, combat, inventaire, boutique, dialogue, artisanat.
- Intègre le tracking d’actions et l’ajustement adaptatif de la difficulté via `LogicEngine`.
- Propose des suggestions dynamiques après chaque commande.
- Offre un workflow de sauvegarde/chargement complet.
- Permet l’ajout automatique de titres et récompenses via les modules correspondants.
"""
