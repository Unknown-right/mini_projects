import json
import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QGroupBox
from PyQt5.QtCore import Qt

class MapView(QWidget):
    def __init__(self, locations_path):
        super().__init__()
        self.setWindowTitle('Carte du Monde - Console_VR')
        self.locations = self.load_locations(locations_path)
        self.layout = QVBoxLayout()
        self.map_grid = QGridLayout()
        self.layout.addWidget(self.create_map_group())
        self.setLayout(self.layout)

    def load_locations(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_map_group(self):
        group = QGroupBox('Carte du Monde')
        grid = QGridLayout()
        # Placement schématique (exemple, à adapter selon la vraie carte)
        positions = {
            'starting_town': (2, 2),
            'dark_forest': (1, 2),
            'eastern_plains': (2, 3),
            'southern_road': (3, 2),
            'western_hills': (2, 1)
        }
        for loc_id, pos in positions.items():
            loc = self.locations.get(loc_id)
            if loc:
                label = QLabel(f"{loc['name']}\n({loc['type']})")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet('border: 1px solid #888; background: #222; color: #fff; padding: 8px;')
                grid.addWidget(label, *pos)
        group.setLayout(grid)
        return group
