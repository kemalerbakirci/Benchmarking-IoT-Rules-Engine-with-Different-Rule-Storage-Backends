"""
Simple IoT Rules Engine
"""
import time
from typing import Dict, Any, List
from .storage import StorageBackend, Rule


class RulesEngine:
    """Simple rules engine for processing IoT messages"""
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.stats = {
            'messages_processed': 0,
            'rules_triggered': 0,
            'processing_time': 0.0
        }
    
    def add_rule(self, condition: str, action: str) -> str:
        """Add a new rule to the engine"""
        rule = Rule(condition, action)
        return self.storage.add_rule(rule)
    
    def process_message(self, message: Dict[str, Any]) -> List[str]:
        """Process an IoT message against all rules"""
        start_time = time.time()
        triggered_actions = []
        
        rules = self.storage.get_all_rules()
        for rule in rules:
            if self._evaluate_condition(rule.condition, message):
                triggered_actions.append(rule.action)
                self.stats['rules_triggered'] += 1
        
        self.stats['messages_processed'] += 1
        self.stats['processing_time'] += time.time() - start_time
        
        return triggered_actions
    
    def _evaluate_condition(self, condition: str, message: Dict[str, Any]) -> bool:
        """Simple condition evaluation"""
        try:
            # Replace message field names with actual values
            for key, value in message.items():
                condition = condition.replace(key, str(value))
            
            # Basic evaluation for simple conditions
            return eval(condition)
        except:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        avg_time = (self.stats['processing_time'] / self.stats['messages_processed'] 
                   if self.stats['messages_processed'] > 0 else 0)
        
        return {
            'messages_processed': self.stats['messages_processed'],
            'rules_triggered': self.stats['rules_triggered'],
            'total_processing_time': self.stats['processing_time'],
            'average_processing_time': avg_time
        }
    
    def reset_statistics(self):
        """Reset engine statistics"""
        self.stats = {
            'messages_processed': 0,
            'rules_triggered': 0,
            'processing_time': 0.0
        }
