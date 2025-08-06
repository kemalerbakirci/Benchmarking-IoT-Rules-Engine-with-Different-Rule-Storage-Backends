"""
Storage backends for the IoT Rules Engine
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import sqlite3
import json


class Rule:
    """Represents a rule in the system"""
    def __init__(self, condition: str, action: str, rule_id: Optional[str] = None):
        self.id = rule_id
        self.condition = condition
        self.action = action
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'condition': self.condition,
            'action': self.action
        }


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def add_rule(self, rule: Rule) -> str:
        """Add a rule and return its ID"""
        pass
    
    @abstractmethod
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID"""
        pass
    
    @abstractmethod
    def get_all_rules(self) -> List[Rule]:
        """Get all rules"""
        pass
    
    @abstractmethod
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by ID"""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Clear all rules"""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage using Python lists"""
    
    def __init__(self):
        self.rules = {}
        self.next_id = 1
    
    def add_rule(self, rule: Rule) -> str:
        rule_id = str(self.next_id)
        rule.id = rule_id
        self.rules[rule_id] = rule
        self.next_id += 1
        return rule_id
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[Rule]:
        return list(self.rules.values())
    
    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def clear_all(self) -> None:
        self.rules.clear()


class SQLiteStorage(StorageBackend):
    """SQLite database storage"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY,
                condition TEXT NOT NULL,
                action TEXT NOT NULL
            )
        ''')
        self.conn.commit()
    
    def add_rule(self, rule: Rule) -> str:
        rule_id = str(hash(rule.condition + rule.action))
        rule.id = rule_id
        self.conn.execute(
            'INSERT OR REPLACE INTO rules (id, condition, action) VALUES (?, ?, ?)',
            (rule_id, rule.condition, rule.action)
        )
        self.conn.commit()
        return rule_id
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        cursor = self.conn.execute(
            'SELECT id, condition, action FROM rules WHERE id = ?',
            (rule_id,)
        )
        row = cursor.fetchone()
        if row:
            return Rule(row[1], row[2], row[0])
        return None
    
    def get_all_rules(self) -> List[Rule]:
        cursor = self.conn.execute('SELECT id, condition, action FROM rules')
        return [Rule(row[1], row[2], row[0]) for row in cursor.fetchall()]
    
    def delete_rule(self, rule_id: str) -> bool:
        cursor = self.conn.execute('DELETE FROM rules WHERE id = ?', (rule_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def clear_all(self) -> None:
        self.conn.execute('DELETE FROM rules')
        self.conn.commit()


class RedisStorage(StorageBackend):
    """Redis storage (optional, requires redis package)"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        try:
            import redis
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()  # Test connection
        except (ImportError, Exception):
            # Fallback to in-memory if Redis is not available
            print("Redis not available, falling back to in-memory storage")
            self.fallback = InMemoryStorage()
            self.redis = None
    
    def _get_key(self, rule_id: str) -> str:
        return f"rule:{rule_id}"
    
    def add_rule(self, rule: Rule) -> str:
        if self.redis is None:
            return self.fallback.add_rule(rule)
        
        rule_id = str(hash(rule.condition + rule.action))
        rule.id = rule_id
        self.redis.set(self._get_key(rule_id), json.dumps(rule.to_dict()))
        return rule_id
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        if self.redis is None:
            return self.fallback.get_rule(rule_id)
        
        data = self.redis.get(self._get_key(rule_id))
        if data:
            rule_dict = json.loads(data)
            return Rule(rule_dict['condition'], rule_dict['action'], rule_dict['id'])
        return None
    
    def get_all_rules(self) -> List[Rule]:
        if self.redis is None:
            return self.fallback.get_all_rules()
        
        keys = self.redis.keys("rule:*")
        rules = []
        for key in keys:
            data = self.redis.get(key)
            if data:
                rule_dict = json.loads(data)
                rules.append(Rule(rule_dict['condition'], rule_dict['action'], rule_dict['id']))
        return rules
    
    def delete_rule(self, rule_id: str) -> bool:
        if self.redis is None:
            return self.fallback.delete_rule(rule_id)
        
        return self.redis.delete(self._get_key(rule_id)) > 0
    
    def clear_all(self) -> None:
        if self.redis is None:
            return self.fallback.clear_all()
        
        keys = self.redis.keys("rule:*")
        if keys:
            self.redis.delete(*keys)
