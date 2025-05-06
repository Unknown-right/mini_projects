#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FateQuest - Un RPG console inspiré des VRMMO des mangas
Main game loop et gestion des commandes

Fonctionnalités:
- Interface console texte
- Menu principal (nouveau jeu/charger/quitter)
- Système de commandes (help, status, move, attack, etc)
- Boucle de jeu principale

"""
import os
import time
import json
import random
from termcolor import colored
from player import Player
from world import World
from combat import CombatSystem
from items import ItemManager
from monsters import MonsterManager
from achievements import AchievementSystem
from save_system import SaveSystem
from logic_engine import LogicEngine

class Game:
    def __init__(self):
        self.running = True
        self.current_state = "main_menu"  # main_menu, game, combat, inventory, etc.
        self.player = None
        self.world = None
        self.combat_system = None
        self.item_manager = None
        self.monster_manager = None
        self.achievement_system = None
        self.save_system = SaveSystem()
        self.logic_engine = None
        self.command_history = []
        self.version = "1.0.0"
        self.game_name = "FateQuest"
        
    def initialize_game(self, new_game=True, player_data=None):
        """Initialise tous les systèmes du jeu"""
        # Création/chargement de l'inventaire et des systèmes
        self.item_manager = ItemManager()
        self.monster_manager = MonsterManager()
        
        # Création/chargement du joueur
        if new_game:
            self.player = self.create_new_player()
        else:
            self.player = Player.load_from_data(player_data, self.item_manager)
            
        # Initialiser les systèmes qui dépendent du joueur
        self.world = World(self.player, self.monster_manager, self.item_manager)
        self.combat_system = CombatSystem(self.player, self.monster_manager, self.item_manager)
        self.achievement_system = AchievementSystem(self.player)
        self.logic_engine = LogicEngine(self.player, self.world, self.achievement_system, 
                                        self.monster_manager, self.item_manager)
        
        # Changer l'état du jeu
        self.current_state = "game"
        self.print_welcome()
    
    def create_new_player(self):
        """Crée un nouveau personnage via des questions"""
        cls()
        print(colored(f"\n=== CRÉATION DE PERSONNAGE ===\n", "cyan", attrs=["bold"]))
        name = input("Quel est votre nom? > ")
        
        print("\nChoisissez votre classe de départ:")
        print("1. Guerrier - Force et endurance")
        print("2. Mage - Intelligence et puissance magique")
        print("3. Voleur - Agilité et furtivité")
        print("4. Archer - Précision et vitesse")
        
        valid_choice = False
        while not valid_choice:
            choice = input("\nVotre choix (1-4): > ")
            if choice in ["1", "2", "3", "4"]:
                valid_choice = True
            else:
                print("Choix invalide. Veuillez choisir entre 1 et 4.")
        
        class_choices = {
            "1": "Guerrier",
            "2": "Mage",
            "3": "Voleur",
            "4": "Archer"
        }
        
        starting_class = class_choices[choice]
        return Player(name, starting_class)
    
    def print_welcome(self):
        """Affiche le message de bienvenue dans le jeu"""
        cls()
        print(colored(f"\n=== Bienvenue dans {self.game_name} ===\n", "cyan", attrs=["bold"]))
        print(f"Vous êtes {self.player.name}, un {self.player.current_class} de niveau {self.player.level}.")
        print(f"Vous vous trouvez à {self.world.current_location['name']}.\n")
        print("Tapez 'help' pour voir les commandes disponibles.\n")
    
    def main_menu(self):
        """Affiche et gère le menu principal"""
        cls()
        print(colored(f"\n=== {self.game_name} v{self.version} ===\n", "cyan", attrs=["bold"]))
        print("1. Nouvelle partie")
        print("2. Charger une partie")
        print("3. Quitter")
        
        choice = input("\nVotre choix: > ")
        
        if choice == "1":
            self.initialize_game(new_game=True)
        elif choice == "2":
            save_files = self.save_system.get_save_files()
            if not save_files:
                print("\nAucune sauvegarde trouvée.")
                input("Appuyez sur Entrée pour continuer...")
                return
            
            print("\nSauvegardes disponibles:")
            for i, save_file in enumerate(save_files, 1):
                print(f"{i}. {save_file}")
            
            save_choice = input("\nChoisissez une sauvegarde (ou 'r' pour retour): > ")
            if save_choice.lower() == 'r':
                return
            
            try:
                save_index = int(save_choice) - 1
                if 0 <= save_index < len(save_files):
                    player_data = self.save_system.load_game(save_files[save_index])
                    if player_data:
                        self.initialize_game(new_game=False, player_data=player_data)
                    else:
                        print("Erreur lors du chargement de la sauvegarde.")
                        input("Appuyez sur Entrée pour continuer...")
                else:
                    print("Choix invalide.")
                    input("Appuyez sur Entrée pour continuer...")
            except ValueError:
                print("Entrée invalide.")
                input("Appuyez sur Entrée pour continuer...")
        elif choice == "3":
            self.running = False
        else:
            print("\nChoix invalide. Veuillez choisir entre 1 et 3.")
            input("Appuyez sur Entrée pour continuer...")
    
    def process_command(self, command):
        """Traite les commandes entrées par le joueur"""
        # Ajouter à l'historique des commandes
        self.command_history.append(command)
        
        # Diviser la commande en parties
        parts = command.lower().split()
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1:]
        
        # Traitement selon l'état actuel du jeu
        if self.current_state == "game":
            self.process_game_command(cmd, args)
        elif self.current_state == "combat":
            self.process_combat_command(cmd, args)
        elif self.current_state == "inventory":
            self.process_inventory_command(cmd, args)
        # Ajouter d'autres états si nécessaire
    
    def process_game_command(self, cmd, args):
        """Traite les commandes en mode exploration"""
        if cmd == "help":
            self.show_help()
        elif cmd == "quit" or cmd == "exit":
            self.confirm_quit()
        elif cmd == "look" or cmd == "l":
            self.world.describe_location()
        elif cmd == "move" or cmd == "go":
            if not args:
                print("Où voulez-vous aller? (move <direction>)")
                return
            self.world.move_player(args[0])
            # Après chaque mouvement, vérifier pour des événements aléatoires
            self.logic_engine.check_for_random_events()
        elif cmd == "talk":
            if not args:
                print("À qui voulez-vous parler? (talk <npc>)")
                return
            npc_name = " ".join(args)
            self.world.talk_to_npc(npc_name)
        elif cmd == "status" or cmd == "stat":
            self.player.display_status()
        elif cmd == "inventory" or cmd == "inv":
            self.current_state = "inventory"
            self.player.display_inventory()
        elif cmd == "equip":
            if not args:
                print("Que voulez-vous équiper? (equip <item_name>)")
                return
            item_name = " ".join(args)
            self.player.equip_item(item_name)
        elif cmd == "use":
            if not args:
                print("Que voulez-vous utiliser? (use <item_name>)")
                return
            item_name = " ".join(args)
            self.player.use_item(item_name)
        elif cmd == "examine" or cmd == "exam":
            if not args:
                print("Que voulez-vous examiner? (examine <item/npc/object>)")
                return
            target = " ".join(args)
            self.examine_target(target)
        elif cmd == "quest" or cmd == "quests":
            self.player.display_quests()
        elif cmd == "skills":
            self.player.display_skills()
        elif cmd == "titles":
            self.player.display_titles()
        elif cmd == "save":
            save_name = f"{self.player.name}_lvl{self.player.level}"
            if self.save_system.save_game(self.player, save_name):
                print(f"Partie sauvegardée sous '{save_name}'.")
            else:
                print("Erreur lors de la sauvegarde.")
        elif cmd == "attack":
            target = " ".join(args) if args else None
            enemy = self.world.find_enemy(target)
            if enemy:
                self.start_combat(enemy)
            else:
                print("Aucun ennemi à attaquer ici." if not target else f"Ennemi '{target}' introuvable.")
        else:
            print(f"Commande '{cmd}' inconnue. Tapez 'help' pour voir les commandes disponibles.")
    
    def process_combat_command(self, cmd, args):
        """Traite les commandes en mode combat"""
        if cmd == "help":
            self.show_combat_help()
        elif cmd == "attack" or cmd == "a":
            self.combat_system.player_attack()
        elif cmd == "skill" or cmd == "s":
            if not args:
                self.combat_system.show_available_skills()
                return
            skill_name = " ".join(args)
            self.combat_system.use_skill(skill_name)
        elif cmd == "item" or cmd == "i":
            if not args:
                self.player.display_usable_items()
                return
            item_name = " ".join(args)
            used = self.player.use_item(item_name)
            if used:
                self.combat_system.enemy_turn()
        elif cmd == "flee" or cmd == "run":
            if self.combat_system.attempt_flee():
                self.end_combat(fled=True)
        elif cmd == "status":
            self.combat_system.show_combat_status()
        else:
            print(f"Commande '{cmd}' inconnue en combat. Tapez 'help' pour l'aide.")
    
    def process_inventory_command(self, cmd, args):
        """Traite les commandes en mode inventaire"""
        if cmd == "help":
            self.show_inventory_help()
        elif cmd == "back" or cmd == "exit":
            self.current_state = "game"
            print("Retour au jeu.")
        elif cmd == "examine" or cmd == "exam":
            if not args:
                print("Quel objet voulez-vous examiner? (examine <item_name>)")
                return
            item_name = " ".join(args)
            self.player.examine_item(item_name)
        elif cmd == "equip":
            if not args:
                print("Quel objet voulez-vous équiper? (equip <item_name>)")
                return
            item_name = " ".join(args)
            self.player.equip_item(item_name)
        elif cmd == "use":
            if not args:
                print("Quel objet voulez-vous utiliser? (use <item_name>)")
                return
            item_name = " ".join(args)
            self.player.use_item(item_name)
        elif cmd == "drop":
            if not args:
                print("Quel objet voulez-vous jeter? (drop <item_name>)")
                return
            item_name = " ".join(args)
            self.player.drop_item(item_name)
        elif cmd == "sort":
            sort_type = args[0] if args else "name"
            self.player.sort_inventory(sort_type)
            self.player.display_inventory()
        else:
            print(f"Commande '{cmd}' inconnue dans l'inventaire. Tapez 'help' pour l'aide.")
    
    def show_help(self):
        """Affiche l'aide des commandes disponibles"""
        print(colored("\n=== COMMANDES DISPONIBLES ===\n", "cyan", attrs=["bold"]))
        print("help            - Affiche cette aide")
        print("look (l)        - Examine les alentours")
        print("move <dir>      - Se déplace dans une direction (nord, sud, est, ouest)")
        print("talk <npc>      - Parle à un PNJ")
        print("attack <cible>  - Attaque un ennemi")
        print("examine <obj>   - Examine un objet, PNJ ou ennemi")
        print("status (stat)   - Affiche vos statistiques")
        print("inventory (inv) - Gère votre inventaire")
        print("equip <item>    - Équipe un objet")
        print("use <item>      - Utilise un objet")
        print("skills          - Affiche vos compétences")
        print("titles         - Affiche vos titres")
        print("quest(s)        - Affiche vos quêtes")
        print("save            - Sauvegarde la partie")
        print("quit/exit       - Quitte le jeu")
        print("")
    
    def show_combat_help(self):
        """Affiche l'aide des commandes de combat"""
        print(colored("\n=== COMMANDES DE COMBAT ===\n", "cyan", attrs=["bold"]))
        print("help           - Affiche cette aide")
        print("attack (a)     - Attaque basique")
        print("skill <nom> (s)- Utilise une compétence")
        print("item <nom> (i) - Utilise un objet")
        print("flee (run)     - Tente de fuir")
        print("status         - Affiche le statut du combat")
        print("")
    
    def show_inventory_help(self):
        """Affiche l'aide des commandes d'inventaire"""
        print(colored("\n=== COMMANDES D'INVENTAIRE ===\n", "cyan", attrs=["bold"]))
        print("help           - Affiche cette aide")
        print("examine <item> - Examine un objet")
        print("equip <item>   - Équipe un objet")
        print("use <item>     - Utilise un objet")
        print("drop <item>    - Jette un objet")
        print("sort <type>    - Trie l'inventaire (name, type, rarity)")
        print("back/exit      - Retourne au jeu")
        print("")
    
    def examine_target(self, target):
        """Examine un objet, PNJ ou élément du monde"""
        # Vérifier d'abord dans l'environnement
        if self.world.examine_object(target):
            return
        
        # Vérifier ensuite dans l'inventaire
        if self.player.examine_item(target):
            return
        
        # Vérifier les PNJ
        if self.world.examine_npc(target):
            return
        
        # Si on arrive ici, l'objet n'a pas été trouvé
        print(f"Vous ne voyez pas de '{target}' ici ou dans votre inventaire.")
    
    def start_combat(self, enemy):
        """Démarre un combat avec un ennemi"""
        self.current_state = "combat"
        self.combat_system.start_combat(enemy)
    
    def end_combat(self, fled=False):
        """Termine un combat"""
        self.current_state = "game"
        if fled:
            print("Vous avez fui le combat!")
        else:
            # Vérifier les accomplissements après combat
            self.achievement_system.check_combat_achievements()
            # Vérifier la logique cachée
            self.logic_engine.analyze_combat_pattern()
    
    def confirm_quit(self):
        """Demande confirmation avant de quitter"""
        choice = input("Voulez-vous sauvegarder avant de quitter? (o/n): ")
        if choice.lower() == 'o':
            save_name = f"{self.player.name}_lvl{self.player.level}"
            self.save_system.save_game(self.player, save_name)
            print(f"Partie sauvegardée sous '{save_name}'.")
        
        self.current_state = "main_menu"
    
    def run(self):
        """Boucle principale du jeu"""
        while self.running:
            if self.current_state == "main_menu":
                self.main_menu()
            else:
                command = input("\n> ")
                self.process_command(command)
                
                # Analyse des patterns de jeu après chaque commande
                if self.logic_engine and len(self.command_history) % 10 == 0:
                    self.logic_engine.analyze_player_patterns(self.command_history)

def cls():
    """Efface l'écran de la console"""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nJeu terminé.")
    except Exception as e:
        print(f"Une erreur est survenue: {e}")
        input("Appuyez sur Entrée pour quitter...")
