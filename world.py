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

import random
import json
from termcolor import colored

class World:
    def __init__(self, player, monster_manager, item_manager):
        self.player = player
        self.monster_manager = monster_manager
        self.item_manager = item_manager
        
        # Carte du monde
        self.world_map = self.initialize_world_map()
        
        # État actuel du monde
        self.current_location = self.world_map["starting_town"]
        self.time_of_day = "jour"  # jour, soir, nuit
        self.day_count = 1
        
        # Liste des PNJ du monde actuel
        self.current_npcs = self.current_location.get("npcs", [])
        
        # Liste des ennemis dans la zone actuelle
        self.current_enemies = []
        self.populate_enemies()
        
        # Événements du monde
        self.world_events = []
        self.active_events = []
        
        # Objets interactifs dans la zone actuelle (coffres, portes, etc.)
        self.interactive_objects = self.current_location.get("objects", [])
    
    def initialize_world_map(self):
        """Initialise la carte du monde"""
        # Cette fonction devrait charger la carte depuis un fichier JSON
        # Pour l'exemple, on crée une carte simple en dur
        
        world_map = {
            "starting_town": {
                "name": "Villevent",
                "description": "Une petite ville paisible située au pied des montagnes. Les habitants y vivent de l'agriculture et du commerce.",
                "type": "ville",
                "danger_level": 0,
                "connections": {
                    "nord": "dark_forest",
                    "est": "eastern_plains",
                    "sud": "southern_road",
                    "ouest": "western_hills"
                },
                "npcs": [
                    {
                        "id": "mayor",
                        "name": "Maire Durand",
                        "description": "Un homme corpulent avec une moustache imposante. Il dirige la ville depuis 15 ans.",
                        "dialogue": {
                            "greeting": "Bonjour voyageur! Bienvenue à Villevent.",
                            "topics": {
                                "ville": "Villevent est une ville paisible, fondée il y a 200 ans. Nous vivons principalement de l'agriculture et du commerce.",
                                "quête": "Hmm, maintenant que vous le mentionnez, nous avons des problèmes avec des gobelins qui pillent nos fermes. Si vous pouviez nous aider...",
                                "rumeurs": "On raconte qu'il y a un trésor caché dans la forêt sombre au nord. Mais personne n'ose s'y aventurer..."
                            },
                            "quest_offer": "goblin_problem"
                        }
                    },
                    {
                        "id": "blacksmith",
                        "name": "Forgeron Bras-d'Acier",
                        "description": "Un nain trapu aux bras musclés, toujours couvert de suie.",
                        "dialogue": {
                            "greeting": "Mrph! Besoin d'une arme solide?",
                            "topics": {
                                "armes": "J'ai les meilleures armes de la région! Forgées avec du minerai des montagnes de l'ouest.",
                                "armures": "Mes armures vous protégeront même contre un troll. Garantie à vie!",
                                "forgeage": "Je peux améliorer votre équipement si vous m'apportez les bons matériaux."
                            },
                            "shop": "blacksmith_shop"
                        }
                    }
                ],
                "objects": [
                    {
                        "id": "town_well",
                        "name": "Puits",
                        "description": "Un vieux puits en pierre au centre de la place du marché.",
                        "interactive": True,
                        "action": "Vous regardez dans le puits. Il semble profond et sombre. Vous entendez l'écho de l'eau en bas."
                    },
                    {
                        "id": "notice_board",
                        "name": "Panneau d'affichage",
                        "description": "Un tableau en bois où sont affichées diverses annonces et offres de quêtes.",
                        "interactive": True,
                        "action": "Vous examinez les annonces. Il y a plusieurs offres de quêtes disponibles."
                    }
                ],
                "shops": [
                    {
                        "id": "blacksmith_shop",
                        "name": "Forge de Bras-d'Acier",
                        "description": "Une forge chaude et bruyante, remplie d'armes et d'
