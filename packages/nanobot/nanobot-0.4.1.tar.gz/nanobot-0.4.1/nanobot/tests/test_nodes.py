"""Tests for builtin nodes"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from nanobot.core import SensorData, Action
from nanobot.nodes import SafetyNode, NavigationNode, ExplorerNode
from nanobot.config import RobotConfig


class TestSafetyNode:
    """Tests pour SafetyNode"""

    def setup_method(self):
        self.node = SafetyNode()

    def test_front_blocked_turn_left(self):
        """Front bloqué, plus d'espace à gauche -> tourne à gauche"""
        sensors = SensorData(front=0.2, left=1.0, right=0.5)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_LEFT

    def test_front_blocked_turn_right(self):
        """Front bloqué, plus d'espace à droite -> tourne à droite"""
        sensors = SensorData(front=0.2, left=0.5, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_RIGHT

    def test_all_blocked_backward(self):
        """Tout bloqué -> recule"""
        sensors = SensorData(front=0.2, left=0.2, right=0.2)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.BACKWARD

    def test_clear_path_no_decision(self):
        """Voie libre -> pas de décision (laisse passer)"""
        sensors = SensorData(front=2.0, left=1.0, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is None

    def test_invalid_sensors_no_decision(self):
        """Capteurs invalides -> pas de décision"""
        sensors = SensorData(left=1.0)  # Pas de front
        decision = self.node.evaluate(sensors)

        assert decision is None


class TestNavigationNode:
    """Tests pour NavigationNode"""

    def setup_method(self):
        self.node = NavigationNode()

    def test_angle_right_turn_left(self):
        """Angle à droite -> tourne à gauche"""
        sensors = SensorData(front=1.5, left=1.0, right=0.2)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_LEFT

    def test_angle_left_turn_right(self):
        """Angle à gauche -> tourne à droite"""
        sensors = SensorData(front=1.5, left=0.2, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_RIGHT

    def test_narrow_corridor_choose_best(self):
        """Couloir étroit -> choisit le côté le plus dégagé"""
        sensors = SensorData(front=2.0, left=0.25, right=0.3)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_RIGHT  # right=0.3 > left=0.25

    def test_clear_path_no_decision(self):
        """Voie libre -> pas de décision"""
        sensors = SensorData(front=2.0, left=1.0, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is None

    def test_turn_persistence(self):
        """Persistence du virage pendant quelques ticks"""
        # Premier tick: détecte l'angle
        sensors = SensorData(front=1.5, left=1.0, right=0.2)
        decision = self.node.evaluate(sensors)
        assert decision.action == Action.TURN_LEFT

        # Deuxième tick: capteurs invalides, mais garde le virage
        invalid_sensors = SensorData(left=1.0)  # Pas de front
        decision = self.node.evaluate(invalid_sensors)
        assert decision is not None
        assert decision.action == Action.TURN_LEFT


class TestExplorerNode:
    """Tests pour ExplorerNode"""

    def setup_method(self):
        self.node = ExplorerNode()

    def test_clear_path_forward_fast(self):
        """Beaucoup d'espace -> avance vite"""
        sensors = SensorData(front=3.0, left=1.0, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.FORWARD
        assert decision.speed == RobotConfig.VITESSE_MAX

    def test_medium_space_forward_normal(self):
        """Espace moyen -> vitesse normale"""
        sensors = SensorData(front=1.2, left=1.0, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.FORWARD
        assert decision.speed == RobotConfig.VITESSE_NORMALE

    def test_limited_space_forward_slow(self):
        """Espace limité -> vitesse lente"""
        sensors = SensorData(front=0.6, left=1.0, right=1.0)
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.FORWARD
        assert decision.speed == RobotConfig.VITESSE_LENTE

    def test_no_sensors_stop(self):
        """Pas de capteurs -> stop"""
        sensors = SensorData()  # Tout à None
        decision = self.node.evaluate(sensors)

        assert decision is not None
        assert decision.action == Action.STOP


class TestNodeIntegration:
    """Tests d'intégration entre nodes"""

    def test_safety_overrides_navigation(self):
        """Safety a priorité sur Navigation"""
        from nanobot.core import NodeEngine

        engine = NodeEngine()
        engine.add_node(SafetyNode())
        engine.add_node(NavigationNode())
        engine.add_node(ExplorerNode())

        # Situation critique: front très proche
        sensors = SensorData(front=0.15, left=1.0, right=0.5)
        decision = engine.tick(sensors)

        assert decision is not None
        assert engine.last_node == "SAFETY"

    def test_navigation_overrides_explorer(self):
        """Navigation a priorité sur Explorer"""
        from nanobot.core import NodeEngine

        engine = NodeEngine()
        engine.add_node(SafetyNode())
        engine.add_node(NavigationNode())
        engine.add_node(ExplorerNode())

        # Angle détecté mais pas critique
        sensors = SensorData(front=1.5, left=1.0, right=0.2)
        decision = engine.tick(sensors)

        assert decision is not None
        assert engine.last_node == "NAVIGATION"

    def test_explorer_when_all_clear(self):
        """Explorer prend le relais quand tout est OK"""
        from nanobot.core import NodeEngine

        engine = NodeEngine()
        engine.add_node(SafetyNode())
        engine.add_node(NavigationNode())
        engine.add_node(ExplorerNode())

        # Tout dégagé
        sensors = SensorData(front=3.0, left=1.5, right=1.5)
        decision = engine.tick(sensors)

        assert decision is not None
        assert engine.last_node == "EXPLORER"
        assert decision.action == Action.FORWARD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
