"""Tests for NodeEngine"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from nanobot.core import NodeEngine, SensorData, Action, Decision, Node


class DummyNode(Node):
    """Node de test qui retourne toujours FORWARD"""
    def __init__(self, name="DUMMY", priority=50, action=None):
        super().__init__(name, priority)
        self._action = action

    def evaluate(self, sensors):
        if self._action:
            return Decision(self._action, 0.5, f"DummyNode: {self._action.name}")
        return None


class TestNodeEngine:
    """Tests pour NodeEngine"""

    def test_create_engine(self):
        """Engine se crée correctement"""
        engine = NodeEngine()
        assert engine is not None
        assert engine.tick_count == 0

    def test_add_node(self):
        """Ajout de nodes fonctionne"""
        engine = NodeEngine()
        engine.add_node(DummyNode("A", 10))
        engine.add_node(DummyNode("B", 20))
        assert len(engine._nodes) == 2

    def test_node_priority_order(self):
        """Nodes sont triés par priorité"""
        engine = NodeEngine()
        engine.add_node(DummyNode("C", 30))
        engine.add_node(DummyNode("A", 10))
        engine.add_node(DummyNode("B", 20))
        engine._ensure_sorted()
        names = [n.name for n in engine._nodes]
        assert names == ["A", "B", "C"]

    def test_first_decision_wins(self):
        """Premier node qui décide gagne"""
        engine = NodeEngine()
        engine.add_node(DummyNode("HIGH", 10, Action.TURN_LEFT))
        engine.add_node(DummyNode("LOW", 50, Action.FORWARD))

        sensors = SensorData(front=1.0)
        decision = engine.tick(sensors)

        assert decision is not None
        assert decision.action == Action.TURN_LEFT
        assert engine.last_node == "HIGH"

    def test_skip_none_decisions(self):
        """Nodes qui retournent None sont sautés"""
        engine = NodeEngine()
        engine.add_node(DummyNode("SKIP", 10, None))  # Retourne None
        engine.add_node(DummyNode("DECIDE", 50, Action.FORWARD))

        sensors = SensorData(front=1.0)
        decision = engine.tick(sensors)

        assert decision is not None
        assert decision.action == Action.FORWARD
        assert engine.last_node == "DECIDE"

    def test_no_decision(self):
        """Retourne None si aucun node ne décide"""
        engine = NodeEngine()
        engine.add_node(DummyNode("SKIP1", 10, None))
        engine.add_node(DummyNode("SKIP2", 20, None))

        sensors = SensorData(front=1.0)
        decision = engine.tick(sensors)

        assert decision is None

    def test_tick_count_increments(self):
        """tick_count s'incrémente à chaque tick"""
        engine = NodeEngine()
        engine.add_node(DummyNode("A", 10, Action.FORWARD))

        sensors = SensorData(front=1.0)
        engine.tick(sensors)
        assert engine.tick_count == 1
        engine.tick(sensors)
        assert engine.tick_count == 2

    def test_reset(self):
        """Reset remet le compteur à zéro"""
        engine = NodeEngine()
        engine.add_node(DummyNode("A", 10, Action.FORWARD))

        sensors = SensorData(front=1.0)
        engine.tick(sensors)
        engine.tick(sensors)
        engine.reset()

        assert engine.tick_count == 0
        assert engine.last_decision is None

    def test_remove_node(self):
        """Suppression de node fonctionne"""
        engine = NodeEngine()
        engine.add_node(DummyNode("A", 10))
        engine.add_node(DummyNode("B", 20))

        result = engine.remove_node("A")
        assert result == True
        assert len(engine._nodes) == 1

        result = engine.remove_node("NOTFOUND")
        assert result == False

    def test_get_node(self):
        """Récupération de node par nom"""
        engine = NodeEngine()
        node_a = DummyNode("A", 10)
        engine.add_node(node_a)

        found = engine.get_node("A")
        assert found is node_a

        not_found = engine.get_node("NOTFOUND")
        assert not_found is None


class TestSensorData:
    """Tests pour SensorData"""

    def test_create_sensors(self):
        """Création de SensorData"""
        s = SensorData(front=1.0, left=0.5, right=0.8)
        assert s.front == 1.0
        assert s.left == 0.5
        assert s.right == 0.8

    def test_from_dict(self):
        """Création depuis dictionnaire"""
        data = {"front": 1.5, "left": 0.8, "right": 0.6}
        s = SensorData.from_dict(data)
        assert s.front == 1.5
        assert s.left == 0.8
        assert s.right == 0.6

    def test_is_valid(self):
        """Validation des capteurs"""
        valid = SensorData(front=1.0)
        assert valid.is_valid() == True

        invalid = SensorData(left=1.0)  # Pas de front
        assert invalid.is_valid() == False

    def test_min_distance(self):
        """Distance minimale"""
        s = SensorData(front=2.0, left=0.5, right=1.0)
        assert s.min_distance() == 0.5


class TestDecision:
    """Tests pour Decision"""

    def test_create_decision(self):
        """Création de Decision"""
        d = Decision(Action.FORWARD, 0.8, "test")
        assert d.action == Action.FORWARD
        assert d.speed == 0.8
        assert d.reason == "test"

    def test_default_values(self):
        """Valeurs par défaut"""
        d = Decision(Action.STOP)
        assert d.speed == 0.5
        assert d.reason == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
