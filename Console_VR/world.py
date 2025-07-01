#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FateQuest - Module World
Gestion du monde, des lieux, des PNJ et déplacements

Fonctionnalités:
- Carte du monde avec zones
- PNJ et dialogues
- Événements aléatoires
- Système de voyage
"""
import os
import random
import json
import time
from termcolor import colored

class World:
    def __init__(self, player, monster_manager, item_manager, data_dir="data"):
        self.player = player
        self.monster_manager = monster_manager
        self.item_manager = item_manager
        self.data_dir = data_dir
        
        # Charger les données JSON du monde
        self.npcs = self.load_npcs()
        self.shops = self.load_shops()
        self.quests = self.load_quests()
        self.world_events = self.load_events()
        self.locations = self.load_locations()

        # Lier les PNJ et boutiques aux lieux correspondants
        for npc in self.npcs.values():
            loc_id = npc.get("location")
            if loc_id and loc_id in self.locations:
                self.locations[loc_id].setdefault("npcs", []).append(npc)
        for shop in self.shops.values():
            loc_id = shop.get("location")
            if loc_id and loc_id in self.locations:
                self.locations[loc_id].setdefault("shops", []).append(shop)

        # Initialiser l'état actuel du joueur dans le monde
        self.world_map = self.locations
        self.current_location = self.world_map.get("starting_town")
        if not self.current_location and self.world_map:
            self.current_location = next(iter(self.world_map.values()))
        self.current_npcs = self.current_location.get("npcs", [])
        self.current_enemies = []
        self.populate_enemies()
        self.interactive_objects = self.current_location.get("objects", [])
        self.active_events = []

        # Métriques cachées pour détecter les comportements du joueur
        self.exploration_metrics = {
            "locations_visited": set(),
            "visits_per_location": {},
            "unique_enemies_encountered": set(),
            "npcs_talked_to": set(),
            "objects_interacted": set(),
            "secret_discoveries": 0,
            "discoveries": {}
        }
        
        self.secrets = self.load_secrets()
        self.unlocked_secrets = set()
        self.recent_secrets = []

        # Temps de jeu
        self.elapsed_time = 0
        self.last_time_update = time.time()
    
    def load_locations(self):
        """Charge les lieux depuis world/locations.json."""
        path = os.path.join(self.data_dir, "world", "locations.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        locations = {}
        for loc_id, loc_data in data.items():
            loc = dict(loc_data)
            loc["id"] = loc_id
            locations[loc_id] = loc
        return locations

    def load_npcs(self):
        """Charge les PNJ depuis world/npcs.json."""
        path = os.path.join(self.data_dir, "world", "npcs.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        npcs = {}
        for npc_id, npc_data in data.items():
            npc = dict(npc_data)
            npc["id"] = npc_id
            npcs[npc_id] = npc
        return npcs

    def load_shops(self):
        """Charge les boutiques depuis world/shops.json."""
        path = os.path.join(self.data_dir, "world", "shops.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        shops = {}
        for shop_id, shop_data in data.items():
            shop = dict(shop_data)
            shop["id"] = shop_id
            shops[shop_id] = shop
        return shops

    def load_quests(self):
        """Charge les quêtes depuis world/quests.json."""
        path = os.path.join(self.data_dir, "world", "quests.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        quests = {}
        for quest_id, quest_data in data.items():
            quests[quest_id] = dict(quest_data)
        return quests

    def load_events(self):
        """Charge les événements depuis world/events.json."""
        path = os.path.join(self.data_dir, "world", "events.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return events

    def load_quest(self, quest_id):
        """Retourne les données d'une quête chargée."""
        return self.quests.get(quest_id)

    def load_secrets(self):
        """Charge secrets.json depuis data/world/."""
        path = os.path.join(self.data_dir, "world", "secrets.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def check_secrets(self, trigger_type, context=None):
        """
        Vérifie tous les secrets non encore débloqués dont 'trigger' == trigger_type
        et dont les conditions sont satisfaites. context est un dict libre.
        """
        for secret_id, secret in self.secrets.items():
            if secret_id in self.unlocked_secrets:
                continue
            if secret.get("trigger") != trigger_type:
                continue

            cond = secret.get("condition", {})
            # exemple : {"location": "dark_forest"} ou {"action_count": 3}
            ok = True
            for key, val in cond.items():
                if self.player.__dict__.get(key) != val:
                    ok = False
                    break
            if not ok:
                continue

            # Débloquer le secret
            self.apply_secret(secret)
            self.unlocked_secrets.add(secret_id)
            # On garde un historique court
            self.recent_secrets.append(secret_id)
            if len(self.recent_secrets) > 10:
                self.recent_secrets.pop(0)

    def apply_secret(self, secret):
        """Exécute l’effet d’un secret (give_item, teleport, reveal_skill…)."""
        effect = secret.get("effect")
        if effect == "give_item":
            item = self.item_manager.get_item_by_id(secret["item_id"])
            if item:
                self.player.add_item(item)
                print(colored(secret.get("message", "Vous obtenez un objet secret !"), "green"))
        elif effect == "teleport":
            dest = secret.get("destination")
            if dest:
                self.teleport(dest)
                print(colored(secret.get("message", "Vous avez découvert un passage secret !"), "magenta"))
        elif effect == "reveal_skill":
            skl = secret.get("skill_id")
            self.player.learn_skill(skl)
            print(colored(secret.get("message", "Vous maîtrisez une nouvelle compétence secrète !"), "yellow"))
        # … autres effets possibles …

    def populate_enemies(self):
        """Peuple la zone actuelle avec des ennemis en fonction du type de zone et du niveau de danger"""
        if "enemies" not in self.current_location:
            self.current_enemies = []
            return
        
        # Vider la liste actuelle
        self.current_enemies = []
        
        # Nombre d'ennemis basé sur le niveau de danger
        danger_level = self.current_location.get("danger_level", 0)
        enemy_count = random.randint(danger_level, danger_level * 2 + 1)
        
        # Limiter le nombre d'ennemis
        enemy_count = min(enemy_count, 10)
        
        # Ajouter des ennemis aléatoires de la liste de la zone
        enemy_types = self.current_location.get("enemies", [])
        
        if enemy_types:
            for _ in range(enemy_count):
                enemy_id = random.choice(enemy_types)
                enemy = self.monster_manager.get_monster(enemy_id)
                
                if enemy:
                    # Variation aléatoire de niveau
                    level_variation = random.randint(-1, 1)
                    enemy_level = max(1, self.player.level + level_variation)
                    enemy["level"] = enemy_level
                    
                    # Ajuster les statistiques en fonction du niveau
                    self.monster_manager.adjust_monster_stats(enemy, enemy_level)
                    
                    self.current_enemies.append(enemy)
        
        # Vérifier si un boss doit apparaître
        self.check_boss_spawn()
    
    def check_boss_spawn(self):
        """Vérifie si un boss doit apparaître dans la zone actuelle"""
        if "boss" not in self.current_location:
            return
        
        boss_info = self.current_location["boss"]
        boss_id = boss_info["id"]
        
        # Vérifier les conditions d'apparition du boss
        trigger_type = boss_info.get("trigger", "random")
        trigger_value = boss_info.get("trigger_value", 0.1)
        
        spawn_boss = False
        
        if trigger_type == "random":
            # Chance aléatoire d'apparition
            spawn_boss = random.random() < trigger_value
        elif trigger_type == "exploration_count":
            # Basé sur le nombre de fois où la zone a été explorée
            location_id = self.get_current_location_id()
            visits = self.exploration_metrics["visits_per_location"].get(location_id, 0)
            spawn_boss = visits >= trigger_value
        elif trigger_type == "kill_count":
            # Basé sur le nombre de monstres tués dans cette zone
            enemy_type = boss_info.get("enemy_type", None)
            if enemy_type:
                if not hasattr(self.player, 'kill_counters'):
                    self.player.kill_counters = {}
                kills = self.player.kill_counters.get(enemy_type, 0)
                spawn_boss = kills >= trigger_value
        
        # Si les conditions sont remplies et que le boss n'a pas été vaincu
        if spawn_boss and not self.check_boss_defeated(boss_id):
            boss = self.monster_manager.get_monster(boss_id)
            if boss:
                # Ajuster le niveau du boss
                boss["level"] = max(self.player.level + 2, 5)
                self.monster_manager.adjust_monster_stats(boss, boss["level"])
                self.current_enemies.append(boss)
                
                print(colored(f"\nUn boss apparaît! {boss['name']} vous défie!", "red", attrs=["bold"]))
    
    def check_boss_defeated(self, boss_id):
        """Vérifie si un boss a déjà été vaincu"""
        return boss_id in self.player.defeated_bosses
    
    def update_time(self):
        """Met à jour le temps dans le jeu"""
        current_time = time.time()
        elapsed = current_time - self.last_time_update
        self.elapsed_time += elapsed
        self.last_time_update = current_time
        
        # Un jour de jeu dure 30 minutes réelles
        minutes_per_day = 30
        seconds_per_day = minutes_per_day * 60
        
        # Calculer le jour actuel
        new_day_count = 1 + int(self.elapsed_time / seconds_per_day)
        
        # Si un nouveau jour commence
        if new_day_count > self.day_count:
            self.on_new_day(new_day_count)
        
        # Déterminer l'heure de la journée
        day_progress = (self.elapsed_time % seconds_per_day) / seconds_per_day
        
        if day_progress < 0.33:
            new_time = "jour"
        elif day_progress < 0.66:
            new_time = "soir"
        else:
            new_time = "nuit"
        
        # Si l'heure change
        if new_time != self.time_of_day:
            self.on_time_change(new_time)
    
    def on_new_day(self, new_day_count):
        """Actions à effectuer lors d'un changement de jour"""
        days_passed = new_day_count - self.day_count
        self.day_count = new_day_count
        
        print(colored(f"\n=== Jour {self.day_count} ===", "yellow"))
        
        # Régénération de PV et MP
        if self.player.hp < self.player.max_hp:
            regen_hp = min(self.player.max_hp * 0.2 * days_passed, self.player.max_hp - self.player.hp)
            self.player.heal(regen_hp)
            print(f"Vous récupérez {int(regen_hp)} points de vie en vous reposant.")
        
        if self.player.mp < self.player.max_mp:
            regen_mp = min(self.player.max_mp * 0.3 * days_passed, self.player.max_mp - self.player.mp)
            self.player.restore_mp(regen_mp)
            print(f"Vous récupérez {int(regen_mp)} points de mana en vous reposant.")
        
        # Vérifier les événements mondiaux
        self.check_world_events()
        
        # Défis et récompenses adaptatifs
        if self.day_count % 7 == 0:
            # Défi hebdomadaire
            self.generate_procedural_challenge()
        if self.day_count == 7:
            if 'survivant_hebdomadaire' not in self.player.titles:
                self.player.add_title({
                    'id': 'survivant_hebdomadaire',
                    'name': 'Survivant Hebdomadaire',
                    'description': 'Vous avez survécu 7 jours dans le monde.',
                    'effects': {'hp_regen': 1.1}
                })
                print(colored('Titre obtenu: Survivant Hebdomadaire!', 'green', attrs=['bold']))
        if self.day_count == 30:
            if 'veteran_du_jeu' not in self.player.titles:
                self.player.add_title({
                    'id': 'veteran_du_jeu',
                    'name': 'Vétéran du Jeu',
                    'description': 'Vous avez survécu 30 jours dans le monde.',
                    'effects': {'xp_gain': 1.2, 'hp_regen': 1.1}
                })
                print(colored('Titre obtenu: Vétéran du Jeu!', 'green', attrs=['bold']))
        
        # Réinitialiser certains compteurs
        # ...
    
    def on_time_change(self, new_time):
        """Actions à effectuer lors d'un changement d'heure"""
        self.time_of_day = new_time
        
        time_colors = {
            "jour": "yellow",
            "soir": "blue",
            "nuit": "magenta"
        }
        
        print(colored(f"\nL'heure change, c'est maintenant le {self.time_of_day}.", time_colors.get(self.time_of_day, "white")))
        
        # Modifier les taux de spawn et types d'ennemis selon l'heure
        if self.time_of_day == "nuit":
            print("Les monstres sont plus nombreux et plus dangereux pendant la nuit.")
            # Repeupler la zone avec plus d'ennemis
            self.populate_enemies()
        
        # Modifier le comportement des PNJ selon l'heure
        for npc in self.current_npcs:
            if "schedule" in npc and self.time_of_day in npc["schedule"]:
                new_location = npc["schedule"][self.time_of_day]
                print(f"{npc['name']} se dirige vers {new_location}.")
                # Logique pour déplacer le PNJ (non implémentée ici)
    
    def check_world_events(self):
        """Vérifie et déclenche les événements mondiaux"""
        # Mettre à jour les événements actifs
        self.active_events = [e for e in self.active_events if e["duration"] > 0]
        
        # Réduire la durée des événements actifs
        for event in self.active_events:
            event["duration"] -= 1
            if event["duration"] <= 0:
                print(colored(f"L'événement '{event['name']}' se termine.", "yellow"))
        
        # Vérifier les nouveaux événements
        for event in self.world_events:
            # Ignorer les événements déjà actifs
            if any(e["id"] == event["id"] for e in self.active_events):
                continue
            
            # Vérifier si l'événement doit se déclencher
            trigger = event["trigger"]
            
            if trigger == "day_count" and self.day_count >= event["trigger_value"]:
                if event.get("repeatable", False):
                    # Pour les événements répétables, vérifier si le bon nombre de jours s'est écoulé
                    repeat_interval = event.get("repeat_interval", 1)
                    if (self.day_count - event["trigger_value"]) % repeat_interval == 0:
                        self.trigger_event(event)
                else:
                    # Événement unique
                    self.trigger_event(event)
            elif trigger == "random" and random.random() < event.get("trigger_chance", 0.1):
                self.trigger_event(event)
    
    def trigger_event(self, event):
        """Déclenche un événement mondial"""
        event_copy = event.copy()
        self.active_events.append(event_copy)
        
        print(colored(f"\nÉvénement mondial: {event['name']}", "cyan", attrs=["bold"]))
        print(colored(event["description"], "cyan"))
        
        # Appliquer les effets de l'événement
        # ...
    
    def move_to(self, direction):
        """Déplace le joueur dans une direction donnée"""
        if direction not in self.current_location["connections"]:
            print(colored(f"Vous ne pouvez pas aller dans cette direction.", "red"))
            return False
        
        # Obtenir l'ID de la destination
        destination_id = self.current_location["connections"][direction]
        
        # Vérifier si la destination existe
        if destination_id not in self.world_map:
            print(colored(f"Erreur: destination inconnue ({destination_id}).", "red"))
            return False
        
        # Sauvegarder l'ID de l'emplacement actuel pour les métriques
        old_location_id = self.get_current_location_id()
        
        # Changer d'emplacement
        self.current_location = self.world_map[destination_id]
        
        # Mettre à jour les PNJ actuels
        self.current_npcs = self.current_location.get("npcs", [])
        
        # Mettre à jour les objets interactifs
        self.interactive_objects = self.current_location.get("objects", [])
        
        # Générer de nouveaux ennemis
        self.populate_enemies()
        
        # Afficher la description du lieu
        self.describe_current_location()
        
        # Mettre à jour les métriques d'exploration
        self.update_exploration_metrics(old_location_id, destination_id)
        
        return True
    
    def get_current_location_id(self):
        """Renvoie l'ID de l'emplacement actuel"""
        for location_id, location in self.world_map.items():
            if location == self.current_location:
                return location_id
        return None
    
    def update_exploration_metrics(self, old_location_id, new_location_id):
        """Met à jour les métriques d'exploration du joueur"""
        # Ajouter à l'ensemble des lieux visités
        self.exploration_metrics["locations_visited"].add(new_location_id)
        
        # Incrémenter le compteur de visites pour ce lieu
        if new_location_id in self.exploration_metrics["visits_per_location"]:
            self.exploration_metrics["visits_per_location"][new_location_id] += 1
        else:
            self.exploration_metrics["visits_per_location"][new_location_id] = 1
        
        # Vérifier si c'est la première visite
        visits = self.exploration_metrics["visits_per_location"][new_location_id]
        if visits == 1:
            print(colored(f"C'est votre première visite à {self.current_location['name']}.", "green"))
            # Récompenser l'exploration de nouveaux lieux
            self.player.gain_exp(20)
        
        # Débloquer des accomplissements en fonction du nombre de lieux visités
        unique_locations = len(self.exploration_metrics["locations_visited"])
        
        # Exemples d'accomplissements implicites liés à l'exploration
        if unique_locations == 5 and "explorateur_débutant" not in self.player.titles:
            self.player.add_title({
                "id": "explorateur_débutant",
                "name": "Explorateur Débutant",
                "description": "Vous avez visité 5 lieux différents.",
                "effects": {"xp_gain": 1.05}
            })
            print(colored("Titre obtenu: Explorateur Débutant!", "green", attrs=["bold"]))
        
        if unique_locations == 10 and "grand_voyageur" not in self.player.titles:
            self.player.add_title({
                "id": "grand_voyageur",
                "name": "Grand Voyageur",
                "description": "Vous avez visité 10 lieux différents.",
                "effects": {"xp_gain": 1.1, "movement_speed": 1.1}
            })
            print(colored("Titre obtenu: Grand Voyageur!", "green", attrs=["bold"]))
    
    def describe_current_location(self):
        """Affiche la description de l'emplacement actuel"""
        location = self.current_location
        
        # Déterminer la couleur en fonction du type de lieu
        location_colors = {
            "ville": "green",
            "forêt": "dark_green",
            "plaine": "yellow",
            "donjon": "red",
            "montagne": "grey",
            "ruines": "magenta"
        }
        color = location_colors.get(location.get("type", ""), "white")
        
        print("\n" + "=" * 50)
        print(colored(f"Vous êtes à: {location['name']}", color, attrs=["bold"]))
        print(colored(location["description"], color))
        
        # Afficher le niveau de danger
        danger = location.get("danger_level", 0)
        danger_text = ["Très sûr", "Sûr", "Peu dangereux", "Dangereux", "Très dangereux", "Extrêmement dangereux"]
        danger_index = min(danger, len(danger_text) - 1)
        
        if danger > 0:
            print(colored(f"Niveau de danger: {danger_text[danger_index]}", "red"))
        else:
            print(colored("Niveau de danger: Aucun", "green"))
        
        # Afficher les directions possibles
        directions = list(location.get("connections", {}).keys())
        if directions:
            print("\nDirections possibles:", end=" ")
            for direction in directions:
                connected_location = self.world_map[location["connections"][direction]]
                print(colored(f"{direction} ({connected_location['name']})", "blue"), end=" ")
            print()
        
        # Lister les PNJ présents
        if self.current_npcs:
            print("\nPersonnages présents:")
            for npc in self.current_npcs:
                print(f"- {npc['name']}: {npc['description']}")
        
        # Lister les objets interactifs
        if self.interactive_objects:
            print("\nObjets remarquables:")
            for obj in self.interactive_objects:
                print(f"- {obj['name']}: {obj['description']}")
    
    def talk_to_npc(self, npc_name):
        """Engage une conversation avec un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom (insensible à la casse)
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Ajouter ce PNJ à la liste des PNJ rencontrés
        self.exploration_metrics["npcs_talked_to"].add(npc["id"])
        
        # Afficher le message d'accueil
        print(colored(f"\n{npc['name']}: ", "yellow") + npc["dialogue"]["greeting"])
        
        # Lister les sujets de conversation disponibles
        topics = npc["dialogue"].get("topics", {})
        if topics:
            print("\nSujets de conversation disponibles:")
            for topic in topics:
                print(f"- {topic}")
        
        # Vérifier si le PNJ propose une quête
        if "quest_offer" in npc["dialogue"]:
            quest_id = npc["dialogue"]["quest_offer"]
            if quest_id not in self.player.completed_quests and quest_id not in [q["id"] for q in self.player.active_quests]:
                print(colored("[Une quête est disponible]", "green"))
        
        # Vérifier si le PNJ a une boutique
        if "shop" in npc["dialogue"]:
            print(colored("[Une boutique est disponible]", "cyan"))
        
        # Mettre à jour l'état du PNJ si nécessaire
        if "state_change" in npc:
            conditions = npc["state_change"].get("conditions", {})
            # Vérifier les conditions pour changer l'état du PNJ
            # ...
    
    def discuss_topic(self, npc_name, topic):
        """Discute d'un sujet spécifique avec un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Vérifier si le sujet existe
        topics = npc["dialogue"].get("topics", {})
        
        # Recherche insensible à la casse
        topic_key = None
        for key in topics.keys():
            if key.lower() == topic.lower():
                topic_key = key
                break
        
        if not topic_key:
            print(colored(f"{npc['name']} n'a rien à dire sur ce sujet.", "red"))
            return
        
        # Afficher la réponse
        print(colored(f"\n{npc['name']}: ", "yellow") + topics[topic_key])
        
        # Vérifier si la discussion déclenche un événement
        if "topic_triggers" in npc["dialogue"] and topic_key in npc["dialogue"]["topic_triggers"]:
            trigger = npc["dialogue"]["topic_triggers"][topic_key]
            
            if trigger["type"] == "quest":
                quest_id = trigger["quest_id"]
                self.offer_quest(npc, quest_id)
            elif trigger["type"] == "item":
                item_id = trigger["item_id"]
                self.give_item_from_npc(npc, item_id)
            elif trigger["type"] == "skill":
                skill_id = trigger["skill_id"]
                self.learn_skill_from_npc(npc, skill_id)
    
    def accept_quest(self, npc_name):
        """Accepte une quête proposée par un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Vérifier si le PNJ propose une quête
        if "quest_offer" not in npc["dialogue"]:
            print(colored(f"{npc['name']} n'a pas de quête à vous proposer.", "red"))
            return
        
        quest_id = npc["dialogue"]["quest_offer"]
        
        # Vérifier si la quête est déjà active ou terminée
        if quest_id in self.player.completed_quests:
            print(colored(f"Vous avez déjà terminé cette quête.", "yellow"))
            return
            
        if quest_id in [q["id"] for q in self.player.active_quests]:
            print(colored(f"Vous avez déjà accepté cette quête.", "yellow"))
            return
        
        # Charger les informations de la quête
        quest = self.load_quest(quest_id)
        if not quest:
            print(colored(f"Erreur: quête {quest_id} introuvable.", "red"))
            return
        
        # Ajouter la quête au joueur
        self.player.add_quest(quest)
        
        print(colored(f"\nVous avez accepté la quête: {quest['name']}", "green"))
        print(colored(quest["description"], "green"))
        print("\nObjectifs:")
        for objective in quest["objectives"]:
            print(f"- {objective['description']}")
    
    def load_quest(self, quest_id):
        """
        Retourne les données d'une quête.
        
        Args:
            quest_id (str): L'identifiant de la quête
            
        Returns:
            dict: Les données de la quête
        """
        try:
            with open("data/quests.json", "r", encoding="utf-8") as f:
                quests = json.load(f)
                if quest_id in quests:
                    return quests[quest_id]
                else:
                    print(colored(f"Erreur: Quête {quest_id} non trouvée!", "red"))
                    return None
        except (FileNotFoundError, json.JSONDecodeError):
            print(colored("Erreur: Fichier de quêtes introuvable ou corrompu!", "red"))
            return None
    
    def open_shop(self, npc_name):
        """Ouvre la boutique d'un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Vérifier si le PNJ a une boutique
        if "shop" not in npc["dialogue"]:
            print(colored(f"{npc['name']} n'a pas de boutique.", "red"))
            return
        
        shop_id = npc["dialogue"]["shop"]
        
        # Trouver les données de la boutique
        shop = None
        if "shops" in self.current_location:
            for s in self.current_location["shops"]:
                if s["id"] == shop_id:
                    shop = s
                    break
        
        if not shop:
            print(colored(f"Erreur: boutique {shop_id} introuvable.", "red"))
            return
        
        # Afficher les articles de la boutique
        print(colored(f"\n=== {shop['name']} ===", "cyan"))
        print(shop["description"])
        print("\nArticles à vendre:")
        
        items = shop.get("inventory", [])
        if not items:
            print("Aucun article disponible.")
            return
        
        for i, item_data in enumerate(items, 1):
            item_id = item_data["id"]
            item = self.item_manager.get_item(item_id)
            
            if item:
                item_price = item_data.get("price", item.get("value", 0))
                rarity = item.get("rarity", "common")
                color = self.get_rarity_color(rarity)
                
                print(f"{i}. {colored(item['name'], color)} - {item_price} or")
                print(f"   {item['description']}")
        
        # Indiquer comment acheter/vendre
        print("\nUtilisez 'acheter <numéro>' pour acheter un article ou 'vendre' pour vendre vos objets.")
    
    def get_rarity_color(self, rarity):
        """Renvoie la couleur correspondant à la rareté d'un objet"""
        colors = {
            "common": "white",
            "uncommon": "green",
            "rare": "blue",
            "epic": "magenta",
            "legendary": "yellow",
            "mythic": "red"
        }
        return colors.get(rarity.lower(), "white")
    
    def buy_item(self, npc_name, item_index):
        """Achète un objet dans la boutique d'un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Vérifier si le PNJ a une boutique
        if "shop" not in npc["dialogue"]:
            print(colored(f"{npc['name']} n'a pas de boutique.", "red"))
            return
        
        shop_id = npc["dialogue"]["shop"]
        
        # Trouver les données de la boutique
        shop = None
        if "shops" in self.current_location:
            for s in self.current_location["shops"]:
                if s["id"] == shop_id:
                    shop = s
                    break
        
        if not shop:
            print(colored(f"Erreur: boutique {shop_id} introuvable.", "red"))
            return
        
        # Vérifier si l'index est valide
        items = shop.get("inventory", [])
        if not items or item_index < 1 or item_index > len(items):
            print(colored("Article invalide.", "red"))
            return
        
        # Récupérer les informations de l'article
        item_data = items[item_index - 1]
        item_id = item_data["id"]
        item = self.item_manager.get_item(item_id)
        
        if not item:
            print(colored(f"Erreur: article {item_id} introuvable.", "red"))
            return
        
        # Vérifier le prix
        item_price = item_data.get("price", item.get("value", 0))
        
        # Vérifier si le joueur a assez d'or
        if self.player.gold < item_price:
            print(colored(f"Vous n'avez pas assez d'or. (Vous avez {self.player.gold}, besoin de {item_price})", "red"))
            return
        
        # Acheter l'article
        self.player.gold -= item_price
        self.player.add_item(item)
        
        print(colored(f"Vous avez acheté {item['name']} pour {item_price} or.", "green"))
        print(f"Or restant: {self.player.gold}")
    
    def sell_item(self, npc_name, item_name):
        """Vend un objet à un PNJ"""
        npc = None
        
        # Chercher le PNJ par son nom
        for n in self.current_npcs:
            if n["name"].lower() == npc_name.lower():
                npc = n
                break
        
        if not npc:
            print(colored(f"Il n'y a personne du nom de {npc_name} ici.", "red"))
            return
        
        # Vérifier si le PNJ a une boutique
        if "shop" not in npc["dialogue"]:
            print(colored(f"{npc['name']} n'a pas de boutique.", "red"))
            return
        
        # Trouver l'objet dans l'inventaire du joueur
        item = self.player.find_item_by_name(item_name)
        if not item:
            print(colored(f"Vous n'avez pas d'objet nommé {item_name}.", "red"))
            return
        
        # Vérifier si l'objet peut être vendu
        if item.get("unsellable", False):
            print(colored(f"{item['name']} ne peut pas être vendu.", "red"))
            return
        
        # Calculer le prix de vente (généralement 50% de la valeur)
        sell_price = int(item.get("value", 0) * 0.5)
        
        # Vendre l'objet
        self.player.gold += sell_price
        self.player.remove_item(item["id"])
        
        print(colored(f"Vous avez vendu {item['name']} pour {sell_price} or.", "green"))
        print(f"Or total: {self.player.gold}")
    
    def interact_with_object(self, object_name):
        """Interagit avec un objet dans la zone actuelle"""
        obj = None
        
        # Chercher l'objet par son nom
        for o in self.interactive_objects:
            if o["name"].lower() == object_name.lower():
                obj = o
                break
        
        if not obj:
            print(colored(f"Il n'y a pas d'objet nommé {object_name} ici.", "red"))
            return
        
        # Vérifier si l'objet est interactif
        if not obj.get("interactive", False):
            print(colored(f"Vous ne pouvez pas interagir avec {obj['name']}.", "red"))
            return
        
        # Ajouter cet objet à la liste des objets avec lesquels le joueur a interagi
        self.exploration_metrics["objects_interacted"].add(obj["id"])
        
        # Compteur d'interactions pour cet objet
        obj_id = obj["id"]
        if "interactions" not in obj:
            obj["interactions"] = 0
        obj["interactions"] += 1
        
        # Afficher l'action standard
        if "action" in obj:
            print(colored(obj["action"], "cyan"))
        
        # Vérifier s'il y a un secret à révéler
        if "secret" in obj:
            secret = obj["secret"]
            trigger_type = secret.get("trigger", "examine_count")
            
            if trigger_type == "examine_count":
                trigger_value = secret.get("trigger_value", 1)
                if obj["interactions"] >= trigger_value:
                    self.reveal_secret(obj, secret)
            elif trigger_type == "item_required":
                required_item = secret.get("required_item")
                if self.player.find_item_by_name(required_item):
                    self.reveal_secret(obj, secret)
            elif trigger_type in self.player.titles:
                # Secret basé sur un titre
                self.reveal_secret(obj, secret)
            elif trigger_type == "skill_required":
                required_skill = secret.get("required_skill")
                required_level = secret.get("required_level", 1)
                if required_skill in self.player.skills and self.player.skills[required_skill]["level"] >= required_level:
                    self.reveal_secret(obj, secret)
        
        # Vérifier si l'objet est lié à une quête
        self.check_quest_interaction(obj)
        self.check_secrets("interact", {"object": object_name})
    
    def reveal_secret(self, obj, secret):
        """Révèle un secret lié à un objet"""
        # Vérifier si le secret a déjà été révélé
        if obj.get("secret_revealed", False):
            return
        
        # Marquer le secret comme révélé
        obj["secret_revealed"] = True
        
        # Incrémenter le compteur de découvertes secrètes
        self.exploration_metrics["secret_discoveries"] += 1
        
        # Afficher le message du secret
        if "message" in secret:
            print(colored(secret["message"], "yellow", attrs=["bold"]))
        
        # Appliquer l'effet du secret
        effect = secret.get("effect")
        
        if effect == "give_item":
            item_id = secret.get("item_id")
            item = self.item_manager.get_item(item_id)
            
            if item:
                self.player.add_item(item)
                print(colored(f"Vous avez obtenu: {item['name']}!", "green"))
        
        elif effect == "reveal_skill":
            skill_id = secret.get("skill_id")
            skill = {
                "id": skill_id,
                "name": secret.get("skill_name", "Compétence mystérieuse"),
                "description": secret.get("skill_description", "Une compétence mystérieuse."),
                "level": 1,
                "exp": 0,
                "next_level": 100
            }
            
            if skill_id not in self.player.skills:
                self.player.skills[skill_id] = skill
                print(colored(f"Vous avez appris une nouvelle compétence: {skill['name']}!", "green"))
        
        elif effect == "teleport":
            destination = secret.get("destination")
            if destination in self.world_map:
                self.current_location = self.world_map[destination]
                self.describe_current_location()
                print(colored("Vous avez été téléporté!", "magenta"))
    
    def check_quest_interaction(self, obj):
        """Vérifie si l'interaction avec l'objet fait progresser une quête"""
        obj_id = obj["id"]
        
        # Parcourir les quêtes actives du joueur
        for quest in self.player.active_quests:
            for objective in quest["objectives"]:
                if objective["type"] == "interact" and objective["target"] == obj_id:
                    # Mettre à jour la progression de la quête
                    self.player.update_quest_progress(quest["id"], objective["id"])
                    print(colored(f"Objectif de quête mis à jour: {objective['description']}", "green"))
    
    def rest(self):
        """Permet au joueur de se reposer pour récupérer des PV et MP"""
        # Vérifier si le lieu est sûr
        if self.current_location.get("danger_level", 0) > 1:
            # Chance de se faire attaquer pendant le repos
            if random.random() < 0.3:
                print(colored("Vous êtes attaqué pendant votre repos!", "red"))
                enemy = random.choice(self.current_enemies) if self.current_enemies else self.monster_manager.get_random_monster(self.player.level)
                
                if enemy:
                    # Lancer un combat
                    return {"event": "combat", "enemy": enemy}
        
        # Récupérer des PV et MP
        hp_recovery = min(self.player.max_hp * 0.3, self.player.max_hp - self.player.hp)
        mp_recovery = min(self.player.max_mp * 0.5, self.player.max_mp - self.player.mp)
        
        self.player.heal(hp_recovery)
        self.player.restore_mp(mp_recovery)
        
        print(colored(f"Vous vous reposez et récupérez {int(hp_recovery)} PV et {int(mp_recovery)} PM.", "green"))
        
        # Faire avancer le temps
        self.update_time()
        
        return {"event": "rest_completed"}
    
    def wait(self, hours=1):
        """Fait passer le temps"""
        print(f"Vous attendez {hours} heure(s)...")
        
        # Simuler le passage du temps
        for i in range(hours):
            # Vérifier si un événement aléatoire se produit
            if random.random() < 0.1:
                self.random_event()
            
            # Mettre à jour le temps
            self.update_time()
        
        print(f"L'attente est terminée. Il fait maintenant {self.time_of_day}.")
    
    def random_event(self):
        """Déclenche un événement aléatoire"""
        events = [
            {"name": "Marchand ambulant", "chance": 0.4, "function": self.wandering_merchant_event},
            {"name": "Voyageur perdu", "chance": 0.3, "function": self.lost_traveler_event},
            {"name": "Rencontre inattendue", "chance": 0.2, "function": self.unexpected_encounter_event},
            {"name": "Découverte", "chance": 0.1, "function": self.discovery_event}
        ]
        
        # Calculer la somme des chances
        total_chance = sum(event["chance"] for event in events)
        
        # Normaliser les chances
        for event in events:
            event["chance"] /= total_chance
        
        # Choisir un événement aléatoire
        roll = random.random()
        cumulative = 0
        
        for event in events:
            cumulative += event["chance"]
            if roll <= cumulative:
                event["function"]()
                break
    
    def wandering_merchant_event(self):
        """Événement: marchand ambulant"""
        print(colored("\nUn marchand ambulant apparaît sur votre chemin.", "cyan"))
        print("Il vous propose des objets rares et inhabituels.")
        
        # Générer un inventaire aléatoire pour le marchand
        inventory = []
        rarity_chances = {
            "common": 0.5,
            "uncommon": 0.3,
            "rare": 0.15,
            "epic": 0.04,
            "legendary": 0.01
        }
        
        # Générer 3 à 5 articles aléatoires
        num_items = random.randint(3, 5)
        
        for _ in range(num_items):
            # Déterminer la rareté
            roll = random.random()
            rarity = "common"
            cumulative = 0
            
            for r, chance in rarity_chances.items():
                cumulative += chance
                if roll <= cumulative:
                    rarity = r
                    break
            
            # Récupérer un objet aléatoire de cette rareté
            item = self.item_manager.get_random_item_by_rarity(rarity)
            
            if item:
                # Appliquer un prix spécial (légèrement plus élevé)
                price = int(item.get("value", 10) * 1.2)
                inventory.append({"id": item["id"], "price": price})
        
        # Afficher l'inventaire
        if inventory:
            print("\nArticles à vendre:")
            for i, item_data in enumerate(inventory, 1):
                item_id = item_data["id"]
                item = self.item_manager.get_item(item_id)
                
                if item:
                    item_price = item_data.get("price", item.get("value", 0))
                    rarity = item.get("rarity", "common")
                    color = self.get_rarity_color(rarity)
                    
                    print(f"{i}. {colored(item['name'], color)} - {item_price} or")
                    print(f"   {item['description']}")
            
            # Permettre au joueur d'acheter (à implémenter dans la boucle principale du jeu)
            print("\nUtilisez 'acheter <numéro>' pour acheter un article.")
        else:
            print("Malheureusement, le marchand n'a rien d'intéressant à vendre.")
    
    def lost_traveler_event(self):
        """Événement: voyageur perdu"""
        print(colored("\nVous rencontrez un voyageur qui semble perdu.", "cyan"))
        
        # Choix aléatoire de scénario
        scenario = random.choice([
            "Il vous demande le chemin vers la ville la plus proche.",
            "Il vous propose de partager son repas en échange d'informations sur la région.",
            "Blessé, il vous demande de l'aide pour soigner ses blessures."
        ])
        
        print(scenario)
        
        # Effet basé sur le scénario (à implémenter dans la boucle principale)
        print("\nUtilisez 'aider voyageur' pour l'aider ou 'ignorer voyageur' pour continuer votre route.")
    
    def unexpected_encounter_event(self):
        """Événement: rencontre inattendue"""
        # Choisir un type de rencontre
        encounter_type = random.choice(["monster", "npc", "traveler"])
        
        if encounter_type == "monster":
            # Rencontre avec un monstre
            monster = self.monster_manager.get_random_monster(self.player.level)
            if monster:
                print(colored(f"\nVous tombez sur un {monster['name']} qui semble vous avoir repéré!", "red"))
                print("Préparez-vous au combat!")
                
                # Lancer un combat (à implémenter dans la boucle principale)
                return {"event": "combat", "enemy": monster}
        
        elif encounter_type == "npc":
            # Rencontre avec un PNJ spécial
            npc_types = [
                {"name": "Voyant", "dialogue": "Ah, je vous attendais! Les étoiles m'ont parlé de votre venue."},
                {"name": "Mage errant", "dialogue": "Salutations, voyageur. Cherchez-vous la connaissance des arcanes?"},
                {"name": "Chasseur", "dialogue": "Méfiez-vous des créatures qui rôdent dans les environs. J'ai vu des traces inquiétantes."}
            ]
            
            npc = random.choice(npc_types)
            print(colored(f"\nVous rencontrez un {npc['name']} sur votre chemin.", "cyan"))
            print(f"{npc['name']}: \"{npc['dialogue']}\"")
            
            # À développer avec des options de dialogue
        
        elif encounter_type == "traveler":
            # Rencontre avec un autre voyageur
            print(colored("\nVous croisez un autre aventurier sur la route.", "cyan"))
            print("Il vous salue et vous propose d'échanger des informations sur la région.")
            
            # À développer avec des options d'interaction
    
    def discovery_event(self):
        """Événement: découverte"""
        discovery_types = [
            {"name": "Coffre caché", "function": self.hidden_chest_discovery},
            {"name": "Passage secret", "function": self.secret_passage_discovery},
            {"name": "Ressource rare", "function": self.rare_resource_discovery}
        ]
        
        discovery = random.choice(discovery_types)
        discovery["function"]()
    
    def hidden_chest_discovery(self):
        """Découverte d'un coffre caché"""
        print(colored("\nVous remarquez un reflet métallique derrière des buissons.", "cyan"))
        print("En explorant, vous découvrez un vieux coffre à moitié enterré.")
        
        # Contenu aléatoire du coffre
        gold = random.randint(10, 50)
        self.player.gold += gold
        
        print(colored(f"Vous ouvrez le coffre et trouvez {gold} pièces d'or!", "yellow"))
        
        # Possibilité de trouver un objet rare
        if random.random() < 0.3:  # 30% de chance
            rarity_chance = random.random()
            if rarity_chance < 0.6:  # 60% de chance pour un objet commun
                rarity = "common"
            elif rarity_chance < 0.9:  # 30% de chance pour un objet rare
                rarity = "rare"
            else:  # 10% de chance pour un objet épique
                rarity = "epic"
                
            # Obtenir un objet aléatoire de cette rareté
            item = self.item_manager.get_random_item_by_rarity(rarity)
            if item:
                self.player.add_item(item)
                color = self.get_rarity_color(rarity)
                print(colored(f"Vous trouvez également {item['name']} !", color))
        
        # Mise à jour des métriques
        discoveries = self.exploration_metrics.get("discoveries", {})
        discoveries["coffres_trouvés"] = discoveries.get("coffres_trouvés", 0) + 1
        self.exploration_metrics["discoveries"] = discoveries
        
        # Vérification des accomplissements cachés
        if discoveries["coffres_trouvés"] >= 10:
            if "chasseur_de_trésors" not in self.player.titles:
                self.player.add_title({
                    "id": "chasseur_de_trésors",
                    "name": "Chasseur de Trésors",
                    "description": "A découvert 10 coffres cachés",
                    "effects": {"luck": 5}
                })
                print(colored("\nVous avez obtenu le titre: Chasseur de Trésors!", "magenta"))
    
    def secret_passage_discovery(self):
        """Découverte d'un passage secret"""
        print(colored("\nEn examinant attentivement les environs, vous remarquez une légère irrégularité dans le terrain.", "cyan"))
        print("Après avoir déplacé quelques pierres, vous découvrez un passage secret!")
        
        # Déterminer où mène ce passage
        current_area_id = self.get_current_location_id()
        current_area = self.world_map[current_area_id]
        danger_level = current_area["danger_level"]
        
        # Créer un nouvel endroit secret ou utiliser un existant
        secret_id = f"secret_{current_area_id}"
        
        if secret_id not in self.world_map:
            # Créer un nouvel endroit secret
            secret_area = {
                "name": f"Passage Secret ({current_area['name']})",
                "description": "Un passage étroit et sombre, visiblement peu fréquenté. Qui sait ce qui vous attend...",
                "danger_level": danger_level + 1,
                "is_secret": True,
                "connections": {
                    "sortie": current_area_id
                },
                "objects": []
            }
            
            # Ajouter des objets interactifs
            if random.random() < 0.7:  # 70% de chance d'avoir un coffre
                secret_area["objects"].append({
                    "id": "coffre_secret",
                    "name": "Coffre Secret",
                    "description": "Un coffre ancien couvert de runes mystérieuses.",
                    "interactive": True,
                    "action": "Vous ouvrez le coffre et un mécanisme se déclenche.",
                    "contains": {
                        "gold": random.randint(50, 200),
                        "items": [self.item_manager.get_random_item_by_rarity("rare")]
                    }
                })
            
            # Chance d'avoir un PNJ secret
            if random.random() < 0.3:  # 30% de chance
                secret_area["npcs"] = [
                    {
                        "id": "hermite",
                        "name": "Ermite Mystérieux",
                        "description": "Un vieil homme vêtu de haillons qui semble vous attendre.",
                        "type": "special",
                        "dialogue": {
                            "greeting": "Peu de gens trouvent ce passage. Vous devez avoir un don...",
                            "topics": {
                                "secret": "Je peux vous enseigner une compétence rare, mais cela a un prix...",
                                "histoire": "J'habite ici depuis des décennies, observant le monde changer..."
                            }
                        },
                        "can_teach": ["perception_accrue", "déplacement_silencieux"]
                    }
                ]
            
            # Ajouter cette zone à la carte du monde
            self.world_map[secret_id] = secret_area
        
        # Se déplacer vers le passage secret
        old_location = current_area_id
        self.current_location = self.world_map[secret_id]
        print(colored(f"Vous entrez dans {self.current_location['name']}.", "green"))
        self.describe_current_location()
        
        # Mise à jour des métriques
        self.update_exploration_metrics(old_location, secret_id)
        discoveries = self.exploration_metrics.get("discoveries", {})
        discoveries["passages_secrets"] = discoveries.get("passages_secrets", 0) + 1
        self.exploration_metrics["discoveries"] = discoveries
        
        # Vérification des accomplissements cachés
        if discoveries["passages_secrets"] >= 5:
            if "explorateur_de_l_ombre" not in self.player.titles:
                self.player.add_title({
                    "id": "explorateur_de_l_ombre",
                    "name": "Explorateur de l'Ombre",
                    "description": "A découvert 5 passages secrets",
                    "effects": {"perception": 3, "stealth": 2}
                })
                print(colored("\nVous avez obtenu le titre: Explorateur de l'Ombre!", "magenta"))
    
    def rare_resource_discovery(self):
        """Découverte d'une ressource rare"""
        resources = [
            {"name": "Herbe médicinale rare", "description": "Une plante aux propriétés curatives exceptionnelles.", "effect": "healing"},
            {"name": "Cristal d'énergie", "description": "Un cristal qui pulse d'une énergie mystique.", "effect": "magic"},
            {"name": "Minerai précieux", "description": "Un minerai brillant et extrêmement rare.", "effect": "crafting"},
            {"name": "Essence élémentaire", "description": "Une substance éthérée qui semble contenir un pouvoir élémentaire.", "effect": "elemental"}
        ]
        
        resource = random.choice(resources)
        print(colored(f"\nEn explorant, vous trouvez {resource['name']}!", "cyan"))
        print(resource["description"])
        
        # Ajouter la ressource à l'inventaire
        item = {
            "id": f"resource_{resource['name'].lower().replace(' ', '_')}",
            "name": resource["name"],
            "description": resource["description"],
            "type": "resource",
            "effect": resource["effect"],
            "value": random.randint(15, 50),
            "rarity": "rare",
            "stackable": True,
            "quantity": 1
        }
        
        self.player.add_item(item)
        print(colored(f"Vous avez ajouté {resource['name']} à votre inventaire.", "green"))
        
        # Mise à jour des métriques
        discoveries = self.exploration_metrics.get("discoveries", {})
        discoveries["ressources_rares"] = discoveries.get("ressources_rares", 0) + 1
        self.exploration_metrics["discoveries"] = discoveries
        
        # Vérification des accomplissements cachés
        if discoveries["ressources_rares"] >= 8:
            if "collectionneur_rare" not in self.player.titles:
                self.player.add_title({
                    "id": "collectionneur_rare",
                    "name": "Collectionneur de Raretés",
                    "description": "A découvert 8 ressources rares",
                    "effects": {"luck": 3, "crafting": 5}
                })
                print(colored("\nVous avez obtenu le titre: Collectionneur de Raretés!", "magenta"))
    
    def update_npc_routines(self):
        """Met à jour les routines quotidiennes des PNJ (déplacement, actions)."""
        # Exemple: faire bouger les PNJ selon leur emploi du temps ou des routines aléatoires
        for location_id, loc in self.world_map.items():
            npcs = loc.get('npcs', [])
            for npc in npcs:
                schedule = npc.get('schedule')
                if schedule and self.time_of_day in schedule:
                    new_location = schedule[self.time_of_day]
                    print(colored(f"{npc['name']} se déplace vers {new_location}.", 'yellow'))
                    # Si la logique de déplacement global existait, on mettrait à jour la position du PNJ
    
    def update_npc_memory(self, npc_name, interaction_type, outcome):
        """Met à jour la mémoire d'un PNJ en fonction d'une interaction."""
        npc = None
        for n in self.current_npcs:
            if n['name'].lower() == npc_name.lower():
                npc = n
                break
        if not npc:
            return
        if 'memory' not in npc:
            npc['memory'] = {}
        npc['memory'][interaction_type] = outcome
        # Le PNJ pourrait modifier ses dialogues ou son comportement ultérieurement
    
    def get_faction_relation(self, faction1, faction2):
        """Retourne la relation actuelle entre deux factions."""
        # Exemples de relations (valeur positive = amical, négative = hostile)
        if not hasattr(self, 'faction_relations'):
            self.faction_relations = {}
        return self.faction_relations.get((faction1, faction2), 0)
    
    def update_faction_reputation(self, faction, value):
        """Met à jour la réputation du joueur auprès d'une faction."""
        if not hasattr(self.player, 'reputation'):
            self.player.reputation = {}
        self.player.reputation[faction] = self.player.reputation.get(faction, 0) + value
        print(colored(f"Réputation mise à jour avec {faction}: {self.player.reputation[faction]}", 'yellow'))
    
    def teleport(self, location_id):
        """Téléporte le joueur à l'emplacement spécifié."""
        if location_id not in self.world_map:
            print(colored(f"Destination inconnue: {location_id}", 'red'))
            return False
        self.current_location = self.world_map[location_id]
        self.current_npcs = self.current_location.get('npcs', [])
        self.interactive_objects = self.current_location.get('objects', [])
        print(colored(f"Vous êtes téléporté à {self.current_location['name']}", 'cyan'))
        self.describe_current_location()
        return True
    
    def generate_procedural_challenge(self):
        """Génère et présente un défi procédural personnalisé pour le joueur."""
        # Exemple simple de génération de défi
        challenge_types = ['combat', 'survie']
        ctype = random.choice(challenge_types)
        if ctype == 'combat':
            monster = random.choice(self.current_location.get('enemies', ['wolf']))
            count = random.randint(5, 15)
            print(colored(f"Un défi vous est proposé: éliminer {count} {monster}s!", 'cyan'))
            # Potentiellement suivre la progression et récompenser ultérieurement
        else:
            days = random.randint(2, 5)
            print(colored(f"Un défi vous est proposé: survivre pendant {days} nuits!", 'cyan'))
        # Récompense automatique (exemple): un titre temporaire ou un boost
        self.player.add_title({
            'id': f'defit_{self.day_count}',
            'name': 'Héros Éphémère',
            'description': 'Récompense pour avoir relevé un défi spontané.',
            'effects': {'xp_gain': 1.1}
        })
        print(colored("Titre obtenu: Héros Éphémère!", 'green', attrs=['bold']))
    
    def increment_kill_counter(self, monster_type):
        """Incrémente le compteur de tués pour un type de monstre."""
        if not hasattr(self.player, 'kill_counters'):
            self.player.kill_counters = {}
        self.player.kill_counters[monster_type] = self.player.kill_counters.get(monster_type, 0) + 1
        # Vérifier les paliers d'actions ou de combos
        self.check_action_milestone(monster_type)
    
    def increment_action_counter(self, action_type):
        """Incrémente le compteur pour un type d'action spécifique."""
        if not hasattr(self.player, 'action_counters'):
            self.player.action_counters = {}
        self.player.action_counters[action_type] = self.player.action_counters.get(action_type, 0) + 1
        self.check_action_milestone(action_type)
    
    def check_action_milestone(self, action_type):
        """Vérifie si un certain seuil d'utilisation d'une action est atteint."""
        count = self.player.action_counters.get(action_type, 0)
        if count == 100:
            title_id = f'maître_{action_type}'
            title_name = f'Maître de {action_type.replace("_", " ")}'
            if title_id not in self.player.titles:
                self.player.add_title({
                    'id': title_id,
                    'name': title_name,
                    'description': f"Vous avez utilisé {action_type} 100 fois!",
                    'effects': {'xp_gain': 1.1}
                })
                print(colored(f"Titre obtenu: {title_name}!", 'green', attrs=['bold']))

    def to_dict(self):
        """
        Serialize the full dynamic state of the world for saving.
        """
        return {
            "current_location_id": self.get_current_location_id(),
            "current_time": self.elapsed_time,
            "time_of_day": getattr(self, "time_of_day", "jour"),
            "day_count": getattr(self, "day_count", 1),
            "current_npcs": [npc["id"] for npc in self.current_npcs],
            "current_enemies": [e["id"] for e in self.current_enemies] if self.current_enemies else [],
            "interactive_objects": [
                {
                    "id": obj.get("id"),
                    "interactions": obj.get("interactions", 0),
                    "secret_revealed": obj.get("secret_revealed", False)
                }
                for obj in self.interactive_objects
            ],
            "active_events": [dict(e) for e in self.active_events] if hasattr(self, "active_events") else [],
            "exploration_metrics": {
                k: list(v) if isinstance(v, set) else v
                for k, v in self.exploration_metrics.items()
            },
            "unlocked_secrets": list(self.unlocked_secrets),
            "recent_secrets": list(self.recent_secrets),
            # Optionnel : sérialiser l’état de tous les lieux visités
            "locations": {
                loc_id: {
                    # État dynamique des PNJ, objets, shops de chaque lieu
                    "npcs": [n["id"] for n in loc.get("npcs", [])],
                    "shops": [s["id"] for s in loc.get("shops", [])],
                    "objects": [
                        {
                            "id": o.get("id"),
                            "interactions": o.get("interactions", 0),
                            "secret_revealed": o.get("secret_revealed", False)
                        }
                        for o in loc.get("objects", [])
                    ]
                }
                for loc_id, loc in self.world_map.items()
            } if hasattr(self, "world_map") else {},
            # Optionnel : ajout d’un hash ou d’un timestamp pour le debug/perf
            "save_timestamp": time.time(),
        }