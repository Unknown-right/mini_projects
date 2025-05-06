#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FateQuest - Module Player
Gestion des caractéristiques du joueur, inventaire, compétences, etc.

Fonctionnalités:
- Stats du joueur (HP, MP, Force, etc)
- Système de classes et d'évolution
- Gestion de l'inventaire
- Gestion des titres et leurs effets
- Système de compétences avec progression
- Système de quêtes
"""

import json
import random
import math
from termcolor import colored

class Player:
    def __init__(self, name, starting_class):
        self.name = name
        self.current_class = starting_class
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100  # Expérience requise pour passer au niveau suivant
        
        # Stats de base (ajustées selon la classe)
        self.base_stats = {
            "hp": 100,
            "mp": 50,
            "strength": 10,
            "intelligence": 10,
            "agility": 10,
            "vitality": 10,
            "luck": 5
        }
        
        # Ajustement des stats selon la classe
        self.adjust_stats_for_class()
        
        # Stats actuelles (peuvent être modifiées par effets, objets, etc.)
        self.current_hp = self.base_stats["hp"]
        self.current_mp = self.base_stats["mp"]
        
        # Inventaire et équipement
        self.inventory = []  # Liste d'objets (dictionnaires)
        self.equipment = {
            "head": None,
            "body": None,
            "legs": None,
            "feet": None,
            "weapon": None,
            "offhand": None,
            "accessory1": None,
            "accessory2": None
        }
        
        # Argent
        self.gold = 100
        
        # Compétences (skill_name: {level, exp, type, effect, mp_cost})
        self.skills = {}
        self.add_starting_skills()
        
        # Titres (actifs et disponibles)
        self.titles = []  # Liste de titres (dictionnaires)
        self.active_title = None
        
        # Réputation avec diverses factions
        self.reputation = {
            "humains": 0,
            "elfes": 0,
            "nains": 0,
            "orcs": -10,  # Commence avec une mauvaise réputation
            "non-morts": -20
        }
        
        # Quêtes (en cours et terminées)
        self.active_quests = []
        self.completed_quests = []
        
        # Compteurs pour les accomplissements cachés
        self.kill_counters = {}  # Type de monstre: nombre tué
        self.action_counters = {
            "steps_taken": 0,
            "items_used": 0,
            "skills_used": 0,
            "critical_hits": 0,
            "treasure_found": 0,
            "quests_completed": 0,
            "boss_defeated": 0,
            "deaths": 0,
            "times_fled": 0
        }
        
        # Flags pour les événements spéciaux ou découvertes
        self.discovery_flags = {}
    
    def adjust_stats_for_class(self):
        """Ajuste les statistiques de base selon la classe choisie"""
        if self.current_class == "Guerrier":
            self.base_stats["strength"] += 5
            self.base_stats["vitality"] += 3
            self.base_stats["hp"] += 20
        elif self.current_class == "Mage":
            self.base_stats["intelligence"] += 5
            self.base_stats["mp"] += 30
            self.base_stats["strength"] -= 2
        elif self.current_class == "Voleur":
            self.base_stats["agility"] += 5
            self.base_stats["luck"] += 3
            self.base_stats["vitality"] -= 1
        elif self.current_class == "Archer":
            self.base_stats["agility"] += 3
            self.base_stats["strength"] += 2
            self.base_stats["luck"] += 2
    
    def add_starting_skills(self):
        """Ajoute les compétences de départ selon la classe"""
        # Compétences communes à toutes les classes
        self.skills["Frappe"] = {
            "level": 1,
            "exp": 0,
            "type": "physical",
            "description": "Une attaque physique basique",
            "effect": {"damage_mult": 1.0},
            "mp_cost": 0
        }
        
        # Compétences spécifiques aux classes
        if self.current_class == "Guerrier":
            self.skills["Coup Puissant"] = {
                "level": 1,
                "exp": 0,
                "type": "physical",
                "description": "Une attaque puissante qui ignore une partie de la défense",
                "effect": {"damage_mult": 1.3, "defense_ignore": 0.2},
                "mp_cost": 10
            }
        elif self.current_class == "Mage":
            self.skills["Boule de Feu"] = {
                "level": 1,
                "exp": 0,
                "type": "magic",
                "description": "Lance une boule de feu sur l'ennemi",
                "effect": {"damage_mult": 1.5, "element": "fire"},
                "mp_cost": 15
            }
        elif self.current_class == "Voleur":
            self.skills["Attaque Furtive"] = {
                "level": 1,
                "exp": 0,
                "type": "physical",
                "description": "Une attaque rapide avec chance de coup critique augmentée",
                "effect": {"damage_mult": 1.1, "crit_chance": 0.15},
                "mp_cost": 8
            }
        elif self.current_class == "Archer":
            self.skills["Tir Précis"] = {
                "level": 1,
                "exp": 0,
                "type": "physical",
                "description": "Un tir visant un point faible de l'ennemi",
                "effect": {"damage_mult": 1.2, "accuracy": 1.2},
                "mp_cost": 10
            }
    
    def display_status(self):
        """Affiche les statistiques du joueur"""
        print(colored("\n=== STATUT DU JOUEUR ===\n", "cyan", attrs=["bold"]))
        print(f"Nom: {self.name}")
        print(f"Classe: {self.current_class}")
        print(f"Niveau: {self.level}")
        print(f"EXP: {self.exp}/{self.exp_to_next}")
        print(f"Titre actif: {self.active_title['name'] if self.active_title else 'Aucun'}")
        print(f"HP: {self.current_hp}/{self.base_stats['hp']}")
        print(f"MP: {self.current_mp}/{self.base_stats['mp']}")
        print(f"Or: {self.gold}")
        
        print("\nStatistiques:")
        print(f"Force: {self.get_total_stat('strength')}")
        print(f"Intelligence: {self.get_total_stat('intelligence')}")
        print(f"Agilité: {self.get_total_stat('agility')}")
        print(f"Vitalité: {self.get_total_stat('vitality')}")
        print(f"Chance: {self.get_total_stat('luck')}")
        
        print("\nÉquipement:")
        for slot, item in self.equipment.items():
            print(f"{slot.capitalize()}: {item['name'] if item else 'Vide'}")
        
        print("\nQuêtes actives:", len(self.active_quests))
        print("Quêtes terminées:", len(self.completed_quests))
    
    def display_inventory(self):
        """Affiche le contenu de l'inventaire"""
        print(colored("\n=== INVENTAIRE ===\n", "yellow", attrs=["bold"]))
        if not self.inventory:
            print("Votre inventaire est vide.")
            return
        
        print(f"Or: {self.gold}")
        print("\nObjets:")
        for i, item in enumerate(self.inventory, 1):
            rarity_color = self.get_rarity_color(item.get("rarity", "commun"))
            equipped = " [Équipé]" if any(eq and eq.get("id") == item.get("id") for eq in self.equipment.values()) else ""
            print(colored(f"{i}. {item['name']}{equipped} - {item.get('description', 'Pas de description')}", rarity_color))
    
    def get_rarity_color(self, rarity):
        """Renvoie la couleur correspondant à la rareté d'un objet"""
        rarity_colors = {
            "commun": "white",
            "rare": "blue",
            "épique": "magenta",
            "légendaire": "yellow",
            "mythique": "red"
        }
        return rarity_colors.get(rarity.lower(), "white")
    
    def add_item(self, item):
        """Ajoute un objet à l'inventaire"""
        self.inventory.append(item)
        rarity_color = self.get_rarity_color(item.get("rarity", "commun"))
        print(colored(f"Vous avez obtenu: {item['name']}", rarity_color))
        return True
    
    def remove_item(self, item_id):
        """Retire un objet de l'inventaire par son ID"""
        for i, item in enumerate(self.inventory):
            if item.get("id") == item_id:
                removed = self.inventory.pop(i)
                print(f"Vous avez retiré {removed['name']} de votre inventaire.")
                return True
        return False
    
    def find_item_by_name(self, name):
        """Trouve un objet dans l'inventaire par son nom"""
        for item in self.inventory:
            if item['name'].lower() == name.lower():
                return item
        return None
    
    def examine_item(self, item_name):
        """Examine un objet dans l'inventaire"""
        item = self.find_item_by_name(item_name)
        if not item:
            return False
        
        rarity_color = self.get_rarity_color(item.get("rarity", "commun"))
        print(colored(f"\n=== {item['name']} ===", rarity_color, attrs=["bold"]))
        print(f"Type: {item.get('type', 'Divers')}")
        print(f"Rareté: {item.get('rarity', 'Commun')}")
        print(f"Description: {item.get('description', 'Pas de description')}")
        
        if "stats" in item:
            print("\nStatistiques:")
            for stat, value in item["stats"].items():
                print(f"{stat.capitalize()}: {'+' if value > 0 else ''}{value}")
        
        if "effects" in item:
            print("\nEffets:")
            for effect, details in item["effects"].items():
                print(f"{effect}: {details}")
        
        if "requirements" in item:
            print("\nPrérequis:")
            for req, value in item["requirements"].items():
                print(f"{req.capitalize()}: {value}")
        
        return True
    
    def equip_item(self, item_name):
        """Équipe un objet s'il est équipable"""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"Vous n'avez pas d'objet nommé '{item_name}' dans votre inventaire.")
            return False
        
        # Vérifier si l'objet est équipable
        if "slot" not in item:
            print(f"{item['name']} n'est pas équipable.")
            return False
        
        # Vérifier les prérequis
        if "requirements" in item:
            for stat, req_value in item["requirements"].items():
                if self.base_stats.get(stat, 0) < req_value:
                    print(f"Vous ne remplissez pas les conditions pour équiper {item['name']}.")
                    print(f"Requis: {stat.capitalize()} {req_value}, Actuel: {self.base_stats.get(stat, 0)}")
                    return False
        
        # Si un objet est déjà équipé dans ce slot, le déséquiper
        current_equipped = self.equipment[item["slot"]]
        if current_equipped:
            print(f"Vous déséquipez {current_equipped['name']}.")
        
        # Équiper le nouvel objet
        self.equipment[item["slot"]] = item
        print(f"Vous équipez {item['name']}.")
        
        # Recalculer les stats si nécessaire
        return True
    
    def unequip_item(self, slot):
        """Déséquipe un objet d'un emplacement spécifique"""
        if slot not in self.equipment or not self.equipment[slot]:
            print(f"Aucun objet n'est équipé dans l'emplacement {slot}.")
            return False
        
        item = self.equipment[slot]
        self.equipment[slot] = None
        print(f"Vous déséquipez {item['name']}.")
        return True
    
    def use_item(self, item_name):
        """Utilise un objet consommable"""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"Vous n'avez pas d'objet nommé '{item_name}' dans votre inventaire.")
            return False
        
        # Vérifier si l'objet est utilisable
        if item.get("type") != "consumable":
            print(f"{item['name']} n'est pas utilisable.")
            return False
        
        # Appliquer les effets
        if "effects" in item:
            print(f"Vous utilisez {item['name']}.")
            for effect, value in item["effects"].items():
                if effect == "heal_hp":
                    self.heal(value)
                    print(f"Vous récupérez {value} points de vie.")
                elif effect == "heal_mp":
                    self.restore_mp(value)
                    print(f"Vous récupérez {value} points de mana.")
                elif effect.startswith("buff_"):
                    stat = effect[5:]  # Extraire le nom de la stat (buff_strength -> strength)
                    # Implémentation des buffs temporaires à faire
                    print(f"Votre {stat} est augmenté temporairement de {value}.")
                # Ajouter d'autres effets selon les besoins
            
            # Incrémenter le compteur d'objets utilisés
            self.action_counters["items_used"] += 1
            
            # Supprimer l'objet s'il est consommable
            if item.get("consumable", True):
                self.remove_item(item["id"])
            
            return True
        else:
            print(f"{item['name']} n'a aucun effet.")
            return False
    
    def drop_item(self, item_name):
        """Jette un objet de l'inventaire"""
        item = self.find_item_by_name(item_name)
        if not item:
            print(f"Vous n'avez pas d'objet nommé '{item_name}' dans votre inventaire.")
            return False
        
        # Vérifier si l'objet est équipé
        for slot, equipped_item in self.equipment.items():
            if equipped_item and equipped_item.get("id") == item.get("id"):
                print(f"Vous devez d'abord déséquiper {item['name']}.")
                return False
        
        # Demander confirmation
        confirm = input(f"Êtes-vous sûr de vouloir jeter {item['name']}? (o/n): ")
        if confirm.lower() != 'o':
            print("Action annulée.")
            return False
        
        # Supprimer l'objet
        self.remove_item(item["id"])
        print(f"Vous jetez {item['name']}.")
        return True
    
    def sort_inventory(self, sort_type="name"):
        """Trie l'inventaire selon différents critères"""
        if sort_type == "name":
            self.inventory.sort(key=lambda x: x.get("name", ""))
        elif sort_type == "type":
            self.inventory.sort(key=lambda x: x.get("type", ""))
        elif sort_type == "rarity":
            rarity_order = {"commun": 0, "rare": 1, "épique": 2, "légendaire": 3, "mythique": 4}
            self.inventory.sort(key=lambda x: rarity_order.get(x.get("rarity", "").lower(), 0))
        else:
            print(f"Critère de tri inconnu: {sort_type}")
            return False
        
        print(f"Inventaire trié par {sort_type}.")
        return True
    
    def display_usable_items(self):
        """Affiche tous les objets utilisables dans l'inventaire"""
        usable_items = [item for item in self.inventory if item.get("type") == "consumable"]
        if not usable_items:
            print("Vous n'avez aucun objet utilisable.")
            return
        
        print(colored("\n=== OBJETS UTILISABLES ===\n", "yellow", attrs=["bold"]))
        for i, item in enumerate(usable_items, 1):
            rarity_color = self.get_rarity_color(item.get("rarity", "commun"))
            print(colored(f"{i}. {item['name']} - {item.get('description', 'Pas de description')}", rarity_color))
    
    def get_total_stat(self, stat):
        """Calcule la valeur totale d'une statistique (base + équipement + buffs)"""
        # Stat de base
        total = self.base_stats.get(stat, 0)
        
        # Bonus d'équipement
        for item in self.equipment.values():
            if item and "stats" in item and stat in item["stats"]:
                total += item["stats"][stat]
        
        # Bonus de titre actif
        if self.active_title and "effects" in self.active_title:
            if f"boost_{stat}" in self.active_title["effects"]:
                total += self.active_title["effects"][f"boost_{stat}"]
        
        # Buffs temporaires à implémenter
        
        return total
    
    def heal(self, amount):
        """Soigne le joueur d'un montant donné"""
        self.current_hp = min(self.current_hp + amount, self.base_stats["hp"])
    
    def restore_mp(self, amount):
        """Restaure le mana du joueur d'un montant donné"""
        self.current_mp = min(self.current_mp + amount, self.base_stats["mp"])
    
    def take_damage(self, amount):
        """Inflige des dégâts au joueur"""
        self.current_hp -= amount
        print(f"Vous subissez {amount} points de dégâts.")
        
        if self.current_hp <= 0:
            self.current_hp = 0
            self.on_death()
            return True  # Indique que le joueur est mort
        return False
    
    def on_death(self):
        """Gestion de la mort du joueur"""
        self.action_counters["deaths"] += 1
        print(colored("\nVous avez été vaincu!", "red", attrs=["bold"]))
        # Pénalités de mort, perte d'XP, etc.
        # À implémenter selon les règles du jeu
    
    def use_mp(self, amount):
        """Utilise du mana pour une compétence"""
        if self.current_mp < amount:
            print("Vous n'avez pas assez de mana!")
            return False
        
        self.current_mp -= amount
        return True
    
    def gain_exp(self, amount):
        """Attribue de l'expérience au joueur et gère le passage de niveau"""
        self.exp += amount
        print(f"Vous gagnez {amount} points d'expérience.")
        
        # Vérifier si le joueur passe un niveau
        while self.exp >= self.exp_to_next:
            self.level_up()
    
    def level_up(self):
        """Fait passer le joueur au niveau supérieur"""
        self.level += 1
        self.exp -= self.exp_to_next  # Soustrait l'XP nécessaire
        
        # Calcul de l'XP requise pour le prochain niveau (formule à ajuster selon vos préférences)
        self.exp_to_next = int(self.exp_to_next * 1.5)
        
        # Augmentation des stats de base
        for stat in self.base_stats:
            if stat in ["hp", "mp"]:
                self.base_stats[stat] += int(self.base_stats[stat] * 0.1)  # +10% par niveau
            else:
                # Pour les autres stats, augmentation plus modérée
                self.base_stats[stat] += random.randint(1, 3)
        
        # Restaurer complètement HP et MP
        self.current_hp = self.base_stats["hp"]
        self.current_mp = self.base_stats["mp"]
        
        print(colored(f"\nNIVEAU SUPÉRIEUR! Vous êtes maintenant niveau {self.level}!", "green", attrs=["bold"]))
        print("Vos statistiques ont augmenté!")
    
    def add_skill_exp(self, skill_name, exp_amount):
        """Ajoute de l'expérience à une compétence"""
        if skill_name not in self.skills:
            return False
        
        self.skills[skill_name]["exp"] += exp_amount
        
        # Vérifier si la compétence monte de niveau
        exp_for_next = self.calculate_skill_exp_for_level(self.skills[skill_name]["level"] + 1)
        if self.skills[skill_name]["exp"] >= exp_for_next:
            self.level_up_skill(skill_name)
            return True
        return False
    
    def calculate_skill_exp_for_level(self, level):
        """Calcule l'XP requise pour un niveau de compétence donné"""
        return 50 * level * level
    
    def level_up_skill(self, skill_name):
        """Fait monter une compétence en niveau"""
        if skill_name not in self.skills:
            return False
        
        self.skills[skill_name]["level"] += 1
        level = self.skills[skill_name]["level"]
        
        # Améliorer les effets de la compétence selon son niveau
        if "effect" in self.skills[skill_name]:
            # Exemple: augmenter les multiplicateurs de dégâts
            if "damage_mult" in self.skills[skill_name]["effect"]:
                self.skills[skill_name]["effect"]["damage_mult"] += 0.1
        
        print(colored(f"Votre compétence {skill_name} atteint le niveau {level}!", "green"))
        return True
    
    def display_skills(self):
        """Affiche toutes les compétences du joueur"""
        print(colored("\n=== COMPÉTENCES ===\n", "cyan", attrs=["bold"]))
        if not self.skills:
            print("Vous n'avez aucune compétence.")
            return
        
        for name, skill in self.skills.items():
            print(colored(f"{name} (Niv. {skill['level']})", "cyan"))
            print(f"Type: {skill['type']}")
            print(f"Description: {skill['description']}")
            print(f"Coût en MP: {skill['mp_cost']}")
            
            # Afficher la progression vers le niveau suivant
            exp_for_next = self.calculate_skill_exp_for_level(skill["level"] + 1)
            print(f"EXP: {skill['exp']}/{exp_for_next}")
            
            # Afficher les effets
            if "effect" in skill:
                print("Effets:", end=" ")
                effects = []
                for effect, value in skill["effect"].items():
                    if effect == "damage_mult":
                        effects.append(f"Dégâts x{value}")
                    elif effect == "defense_ignore":
                        effects.append(f"Ignore {int(value*100)}% de la défense")
                    elif effect == "crit_chance":
                        effects.append(f"+{int(value*100)}% chance critique")
                    elif effect == "element":
                        effects.append(f"Élément: {value}")
                    # Ajouter d'autres effets au besoin
                print(", ".join(effects))
            print("")
    
    def add_title(self, title):
        """Ajoute un nouveau titre au joueur"""
        # Vérifier si le titre existe déjà
        for existing_title in self.titles:
            if existing_title["name"] == title["name"]:
                print(f"Vous possédez déjà le titre '{title['name']}'.")
                return False
        
        self.titles.append(title)
        print(colored(f"Nouveau titre obtenu: {title['name']}!", "green", attrs=["bold"]))
        print(f"Description: {title.get('description', 'Pas de description')}")
        
        # Suggérer d'activer le titre
        if len(self.titles) == 1 or not self.active_title:
            choice = input("Voulez-vous activer ce titre maintenant? (o/n): ")
            if choice.lower() == 'o':
                self.set_active_title(title["name"])
        
        return True
    
    def set_active_title(self, title_name):
        """Définit un titre comme actif"""
        for title in self.titles:
            if title["name"].lower() == title_name.lower():
                self.active_title = title
                print(f"Titre actif: {title['name']}")
                return True
        
        print(f"Vous ne possédez pas le titre '{title_name}'.")
        return False
    
    def display_titles(self):
        """Affiche tous les titres du joueur"""
        print(colored("\n=== TITRES ===\n", "magenta", attrs=["bold"]))
        if not self.titles:
            print("Vous ne possédez aucun titre.")
            return
        
        print(f"Titre actif: {self.active_title['name'] if self.active_title else 'Aucun'}")
        print("\nTitres disponibles:")
        for i, title in enumerate(self.titles, 1):
            active = " [Actif]" if self.active_title and title["name"] == self.active_title["name"] else ""
            print(colored(f"{i}. {title['name']}{active}", "magenta"))
            print(f"   Description: {title.get('description', 'Pas de description')}")
            if "effects" in title:
                print("   Effets:", end=" ")
                effects = []
                for effect, value in title["effects"].items():
                    if effect.startswith("boost_"):
                        stat = effect[6:]
                        effects.append(f"+{value} {stat}")
                    elif effect == "damage_bonus":
                        effects.append(f"+{int(value*100)}% dégâts")
                    elif effect.startswith("resistance_"):
                        element = effect[11:]
                        effects.append(f"+{int(value*100)}% résistance {element}")
                    # Ajouter d'autres effets au besoin
                print(", ".join(effects))
            print("")
    
    def add_quest(self, quest):
        """Ajoute une nouvelle quête au joueur"""
        # Vérifier si la quête est déjà active ou terminée
        for active_quest in self.active_quests:
            if active_quest["id"] == quest["id"]:
                print(f"Vous avez déjà accepté la quête '{quest['name']}'.")
                return False
        
        for completed_quest in self.completed_quests:
            if completed_quest["id"] == quest["id"]:
                print(f"Vous avez déjà terminé la quête '{quest['name']}'.")
                return False
        
        self.active_quests.append(quest)
        print(colored(f"Nouvelle quête acceptée: {quest['name']}", "green"))
        print(f"Description: {quest.get('description', 'Pas de description')}")
        return True
    
    def update_quest_progress(self, quest_id, objective_id, progress=1):
        """Met à jour la progression d'un objectif de quête"""
        for quest in self.active_quests:
            if quest["id"] == quest_id:
                for objective in quest["objectives"]:
                    if objective["id"] == objective_id:
                        objective["current"] += progress
                        if objective["current"] >= objective["required"]:
                            objective["completed"] = True
                            print(f"Objectif terminé: {objective['description']}")
                            
                            # Vérifier si tous les objectifs sont terminés
                            all_completed = all(obj.get("completed", False) for obj in quest["objectives"])
                            if all_completed:
                                self.complete_quest(quest_id)
                        else:
                            print(f"Progression de quête: {objective['current']}/{objective['required']} {objective['description']}")
                        return True
        return False
    
    def complete_quest(self, quest_id):
        """Marque une quête comme terminée et attribue les récompenses"""
        for i, quest in enumerate(self.active_quests):
            if quest["id"] == quest_id:
                completed_quest = self.active_quests.pop(i)
                self.completed_quests.append(completed_quest)
                
                print(colored(f"\nQuête terminée: {completed_quest['name']}!", "green", attrs=["bold"]))
                
                # Attribuer les récompenses
                if "rewards" in completed_quest:
                    print("Récompenses:")
                    if "exp" in completed_quest["rewards"]:
                        exp = completed_quest["rewards"]["exp"]
                        print(f"- {exp} points d'expérience")
                        self.gain_exp(exp)
                    
                    if "gold" in completed_quest["rewards"]:
                        gold = completed_quest["rewards"]["gold"]
                        print(f"- {gold} pièces d'or")
                        self.gold += gold
                    
                    if "items" in completed_quest["rewards"]:
                        for item_id in completed_quest["rewards"]["items"]:
                            # L'item_manager devrait être passé en paramètre pour créer l'objet
                            # Pour l'instant, on suppose que l'ID est l'objet lui-même
                            self.add_item(item_id)
                    
                    if "title" in completed_quest["rewards"]:
                        title = completed_quest["rewards"]["title"]
                        self.add_title(title)
                
                # Incrémenter le compteur de quêtes terminées
                self.action_counters["quests_completed"] += 1
                
                return True
        return False
    
    def display_quests(self):
        """Affiche toutes les quêtes actives du joueur"""
        print(colored("\n=== QUÊTES ACTIVES ===\n", "yellow", attrs=["bold"]))
        if not self.active_quests:
            print("Vous n'avez aucune quête active.")
        else:
            for i, quest in enumerate(self.active_quests, 1):
                print(colored(f"{i}. {quest['name']}", "yellow"))
                print(f"   Description: {quest.get('description', 'Pas de description')}")
                
                print("   Objectifs:")
                for objective in quest["objectives"]:
                    status = "✓" if objective.get("completed", False) else " "
                    print(f"   [{status}] {objective['current']}/{objective['required']} {objective['description']}")
                print("")
        
        if self.completed_quests and input("\nVoir les quêtes terminées? (o/n): ").lower() == 'o':
            print(colored("\n=== QUÊTES TERMINÉES ===\n", "green", attrs=["bold"]))
            for i, quest in enumerate(self.completed_quests, 1):
                print(colored(f"{i}. {quest['name']}", "green"))
                print(f"   Description: {quest.get('description', 'Pas de description')}")
                print("")
    
    def increment_kill_counter(self, monster_type):
        """Incrémente le compteur de monstres tués"""
        if monster_type not in self.kill_counters:
            self.kill_counters[monster_type] = 0
        
        self.kill_counters[monster_type] += 1
        return self.kill_counters[monster_type]
    
    def to_dict(self):
        """Convertit les données du joueur en dictionnaire pour la sauvegarde"""
        return {
            "name": self.name,
            "current_class": self.current_class,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "base_stats": self.base_stats,
            "current_hp": self.current_hp,
            "current_mp": self.current_mp,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "gold": self.gold,
            "skills": self.skills,
            "titles": self.titles,
            "active_title": self.active_title,
            "reputation": self.reputation,
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "kill_counters": self.kill_counters,
            "action_counters": self.action_counters,
            "discovery_flags": self.discovery_flags
        }
    
    @classmethod
    def load_from_data(cls, data, item_manager=None):
        """Crée un joueur à partir des données de sauvegarde"""
        player = cls(data["name"], data["current_class"])
        
        # Charger les données sauvegardées
        player.level = data["level"]
        player.exp = data["exp"]
        player.exp_to_next = data["exp_to_next"]
        player.base_stats = data["base_stats"]
        player.current_hp = data["current_hp"]
        player.current_mp = data["current_mp"]
        player.inventory = data["inventory"]
        player.equipment = data["equipment"]
        player.gold = data["gold"]
        player.skills = data["skills"]
        player.titles = data["titles"]
        player.active_title = data["active_title"]
        player.reputation = data["reputation"]
        player.active_quests = data["active_quests"]
        player.completed_quests = data["completed_quests"]
        player.kill_counters = data["kill_counters"]
        player.action_counters = data["action_counters"]
        player.discovery_flags = data["discovery_flags"]
        
        return player
