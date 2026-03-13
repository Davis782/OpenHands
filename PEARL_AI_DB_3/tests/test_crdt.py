import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime, timedelta
from App.src.core.database.pearl_qlite.pearl_qlite import PearlClient
from App.src.agent_pearl.agent_pearl import AgentPearl

class TestCRDT(unittest.TestCase):
    def setUp(self):
        self.pearl_client = PearlClient(default_db=":memory:")

        # Patch _initialize_text_to_sql to prevent SQLiteConnector issues
        self.initialize_text_to_sql_patch = patch('App.src.agent_pearl.agent_pearl.AgentPearl._initialize_text_to_sql')
        self.mock_initialize_text_to_sql = self.initialize_text_to_sql_patch.start()
        self.mock_text_to_sql_converter = MagicMock()
        self.mock_text_to_sql_converter.convert.return_value = ""
        self.mock_initialize_text_to_sql.return_value = self.mock_text_to_sql_converter

        self.agent_pearl = AgentPearl(pearl_client=self.pearl_client)

    def tearDown(self):
        self.initialize_text_to_sql_patch.stop()








    def test_add_and_get_crdt_log(self):
        # Test adding a log entry
        entry_type = "TEST_EVENT"
        entity_id = "entity_123"
        data = "Some test data"
        self.agent_pearl.add_crdt_log_entry(entry_type, entity_id, data)

        # Test retrieving the log entry
        log_entries = self.agent_pearl.get_crdt_log()
        self.assertEqual(len(log_entries), 1)
        self.assertEqual(log_entries[0]['site_id'], entity_id)
        self.assertEqual(log_entries[0]['log_entry'], f"Type: {entry_type}, Data: {data}")

        # Test adding another entry and verifying count
        self.agent_pearl.add_crdt_log_entry("ANOTHER_EVENT", "entity_456", "More data")
        log_entries = self.agent_pearl.get_crdt_log()
        self.assertEqual(len(log_entries), 2)

    def test_increment_and_get_crdt_counter(self):
        counter_name = "test_counter"
        site_id_1 = "site_A"
        site_id_2 = "site_B"

        # Initial value should be 0
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 0)

        # Increment from site A
        self.agent_pearl.increment_crdt_counter(counter_name, site_id_1, 5)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 5)

        # Increment from site B
        self.agent_pearl.increment_crdt_counter(counter_name, site_id_2, 3)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 8)

        # Increment site A again
        self.agent_pearl.increment_crdt_counter(counter_name, site_id_1, 2)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 10)

        # Test with negative increment (decrement)
        self.agent_pearl.increment_crdt_counter(counter_name, site_id_1, -4)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 6)

        # Test another counter
        another_counter = "another_counter"
        self.agent_pearl.increment_crdt_counter(another_counter, site_id_1, 10)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(another_counter), 10)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 6) # Ensure other counter is unaffected

    def test_crdt_counter_multiple_sites_and_decrements(self):
        counter_name = "complex_counter"
        site_a = "site_alpha"
        site_b = "site_beta"

        # Site A increments
        self.agent_pearl.increment_crdt_counter(counter_name, site_a, 10)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 10)

        # Site B increments
        self.agent_pearl.increment_crdt_counter(counter_name, site_b, 5)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 15)

        # Site A decrements
        self.agent_pearl.increment_crdt_counter(counter_name, site_a, -3)
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 12)

        # Site B decrements
        self.agent_pearl.increment_crdt_counter(counter_name, site_b, -7) # Should result in a negative contribution from site B
        self.assertEqual(self.agent_pearl.get_crdt_counter_value(counter_name), 5) # 10 (A inc) - 3 (A dec) + 5 (B inc) - 7 (B dec) = 5

        # Verify individual site contributions (internal check, not directly exposed by get_crdt_counter_value)
        # This would require direct DB access or a specific method in PearlClient to expose site-specific values
        # For now, we rely on the aggregate value being correct.

if __name__ == '__main__':
    unittest.main()
