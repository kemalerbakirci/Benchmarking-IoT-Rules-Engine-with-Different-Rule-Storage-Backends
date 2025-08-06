"""
Simple tests for IoT Rules Engine
"""

import unittest
import tempfile
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rules_engine.storage import InMemoryStorage, SQLiteStorage, RedisStorage, Rule
from rules_engine.engine import RulesEngine


class TestRule(unittest.TestCase):
    """Test Rule class"""
    
    def test_rule_creation(self):
        rule = Rule("temperature > 25", "High temperature alert")
        self.assertEqual(rule.condition, "temperature > 25")
        self.assertEqual(rule.action, "High temperature alert")
        self.assertIsNone(rule.id)
    
    def test_rule_to_dict(self):
        rule = Rule("humidity < 30", "Low humidity warning", "rule_123")
        rule_dict = rule.to_dict()
        
        expected = {
            'id': 'rule_123',
            'condition': 'humidity < 30',
            'action': 'Low humidity warning'
        }
        self.assertEqual(rule_dict, expected)


class TestInMemoryStorage(unittest.TestCase):
    """Test InMemory storage backend"""
    
    def setUp(self):
        self.storage = InMemoryStorage()
    
    def test_add_and_get_rule(self):
        rule = Rule("temperature > 25", "High temperature alert")
        rule_id = self.storage.add_rule(rule)
        
        retrieved_rule = self.storage.get_rule(rule_id)
        self.assertIsNotNone(retrieved_rule)
        self.assertEqual(retrieved_rule.condition, "temperature > 25")
        self.assertEqual(retrieved_rule.action, "High temperature alert")
        self.assertEqual(retrieved_rule.id, rule_id)
    
    def test_get_all_rules(self):
        rule1 = Rule("temperature > 25", "High temperature alert")
        rule2 = Rule("humidity < 30", "Low humidity warning")
        
        self.storage.add_rule(rule1)
        self.storage.add_rule(rule2)
        
        all_rules = self.storage.get_all_rules()
        self.assertEqual(len(all_rules), 2)
    
        rule = Rule("temperature > 25", "High temperature alert")
        rule_id = self.storage.add_rule(rule)
        
        # Verify rule exists
        self.assertIsNotNone(self.storage.get_rule(rule_id))
        
        # Delete rule
        deleted = self.storage.delete_rule(rule_id)
        self.assertTrue(deleted)
        
        # Verify rule is gone
        self.assertIsNone(self.storage.get_rule(rule_id))
    
    def test_clear_all(self):
        rule1 = Rule("temperature > 25", "High temperature alert")
        rule2 = Rule("humidity < 30", "Low humidity warning")
        
        self.storage.add_rule(rule1)
        self.storage.add_rule(rule2)
        
        self.assertEqual(len(self.storage.get_all_rules()), 2)
        
        self.storage.clear_all()
        self.assertEqual(len(self.storage.get_all_rules()), 0)


class TestSQLiteStorage(unittest.TestCase):
    """Test SQLite storage backend"""
    
    def setUp(self):
        # Use in-memory database for testing
        self.storage = SQLiteStorage(":memory:")
    
    def test_add_and_get_rule(self):
        rule = Rule("temperature > 25", "High temperature alert")
        rule_id = self.storage.add_rule(rule)
        
        retrieved_rule = self.storage.get_rule(rule_id)
        self.assertIsNotNone(retrieved_rule)
        self.assertEqual(retrieved_rule.condition, "temperature > 25")
        self.assertEqual(retrieved_rule.action, "High temperature alert")
    
    def test_get_all_rules(self):
        rule1 = Rule("temperature > 25", "High temperature alert")
        rule2 = Rule("humidity < 30", "Low humidity warning")
        
        self.storage.add_rule(rule1)
        self.storage.add_rule(rule2)
        
        all_rules = self.storage.get_all_rules()
        self.assertEqual(len(all_rules), 2)
    
    def test_delete_rule(self):
        rule = Rule("temperature > 25", "High temperature alert")
        rule_id = self.storage.add_rule(rule)
        
        # Verify rule exists
        self.assertIsNotNone(self.storage.get_rule(rule_id))
        
        # Delete rule
        deleted = self.storage.delete_rule(rule_id)
        self.assertTrue(deleted)
        
        # Verify rule is gone
        self.assertIsNone(self.storage.get_rule(rule_id))


class TestRulesEngine(unittest.TestCase):
    """Test Rules Engine"""
    
    def setUp(self):
        self.storage = InMemoryStorage()
        self.engine = RulesEngine(self.storage)
    
    def test_add_rule(self):
        rule_id = self.engine.add_rule("temperature > 25", "High temperature alert")
        self.assertIsNotNone(rule_id)
        
        # Verify rule was added to storage
        rule = self.storage.get_rule(rule_id)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.condition, "temperature > 25")
        self.assertEqual(rule.action, "High temperature alert")
    
    def test_process_message(self):
        # Add some rules
        self.engine.add_rule("temperature > 25", "High temperature alert")
        self.engine.add_rule("humidity < 30", "Low humidity warning")
        self.engine.add_rule("pressure > 1013", "High pressure detected")
        
        # Test message that triggers temperature rule
        message = {"temperature": 30, "humidity": 50, "pressure": 1000}
        actions = self.engine.process_message(message)
        
        self.assertEqual(len(actions), 1)
        self.assertIn("High temperature alert", actions)
        
        # Test message that triggers multiple rules
        message2 = {"temperature": 30, "humidity": 20, "pressure": 1020}
        actions2 = self.engine.process_message(message2)
        
        self.assertEqual(len(actions2), 3)
        self.assertIn("High temperature alert", actions2)
        self.assertIn("Low humidity warning", actions2)
        self.assertIn("High pressure detected", actions2)
    
    def test_statistics(self):
        # Add a rule
        self.engine.add_rule("temperature > 25", "High temperature alert")
        
        # Get initial stats
        stats = self.engine.get_statistics()
        self.assertEqual(stats['messages_processed'], 0)
        self.assertEqual(stats['rules_triggered'], 0)
        
        # Process some messages
        self.engine.process_message({"temperature": 30})  # Should trigger
        self.engine.process_message({"temperature": 20})  # Should not trigger
        self.engine.process_message({"temperature": 35})  # Should trigger
        
        # Check updated stats
        stats = self.engine.get_statistics()
        self.assertEqual(stats['messages_processed'], 3)
        self.assertEqual(stats['rules_triggered'], 2)
        self.assertGreater(stats['total_processing_time'], 0)
        self.assertGreater(stats['average_processing_time'], 0)
    
    def test_reset_statistics(self):
        # Add a rule and process messages
        self.engine.add_rule("temperature > 25", "High temperature alert")
        self.engine.process_message({"temperature": 30})
        
        # Verify stats exist
        stats = self.engine.get_statistics()
        self.assertGreater(stats['messages_processed'], 0)
        
        # Reset and verify
        self.engine.reset_statistics()
        stats = self.engine.get_statistics()
        self.assertEqual(stats['messages_processed'], 0)
        self.assertEqual(stats['rules_triggered'], 0)
        self.assertEqual(stats['total_processing_time'], 0.0)


if __name__ == '__main__':
    unittest.main()
