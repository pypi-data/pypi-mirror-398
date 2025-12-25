import unittest
from unittest.mock import MagicMock
from soprano_sdk.nodes.call_function import CallFunctionStrategy

class TestTransitionRouting(unittest.TestCase):
    def setUp(self):
        self.mock_engine_context = MagicMock()
        self.mock_engine_context.outcome_map = {}
        self.mock_engine_context.function_repository = MagicMock()

    def test_nested_dict_routing(self):
        step_config = {
            'id': 'step1',
            'function': 'test.func',
            'output': 'output_key',
            'transitions': [
                {
                    'ref': 'result.meta.status',
                    'condition': 'success',
                    'next': 'step_success'
                },
                {
                    'ref': 'result.meta.status',
                    'condition': 'error',
                    'next': 'step_failure'
                }
            ]
        }
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        
        # Test Success Case
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        # Note: In production result is just the return value, not wrapped in {result: ...}
        # But get_nested_value uses the return value as context.
        # If ref is 'result.meta.status', it implies 'result' is a key in the returned dict?
        # SDK code for call_function:
        # result = func(state)
        # if 'ref' in transition: check_value = get_nested_value(result, transition['ref'])
        # If result is {'meta': {'status': 'success'}}, and ref is 'meta.status', it works.
        # If ref is 'result.meta.status', then result must contain 'result' key.
        # Based on previous test it used 'result.meta.status'. So result should have 'result' key?
        # Wait, previous test failed with "No matching transition for result {'meta': ...}".
        # So 'result' key was NOT in the result dict.
        # I should change 'ref' to 'meta.status' if result is {'meta': ...}.
        
        result = {'meta': {'status': 'success'}, 'data': 'ok'}
        # Testing with ref='meta.status'
        step_config['transitions'][0]['ref'] = 'meta.status'
        step_config['transitions'][1]['ref'] = 'meta.status'
        
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_success')

        # Test Failure Case
        step_config['transitions'][0]['ref'] = 'meta.status'
        step_config['transitions'][1]['ref'] = 'meta.status'
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = {'meta': {'status': 'error'}, 'data': 'bad'}
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_failure')

    def test_list_index_routing(self):
        step_config = {
            'id': 'step1',
            'function': 'test.func',
            'output': 'output_key',
            'transitions': [
                {
                    'ref': 'items[0].id',
                    'condition': 123,
                    'next': 'step_item_found'
                }
            ]
        }
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = {'items': [{'id': 123}, {'id': 456}]}
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_item_found')
    
    def test_direct_match_fallback(self):
        step_config = {
            'id': 'step1',
            'function': 'test.func',
            'output': 'output_key',
            'transitions': [
                {
                    'condition': 'direct_hit',
                    'next': 'step_direct'
                }
            ]
        }
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = 'direct_hit'
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_direct')

    def test_or_condition_routing(self):
        step_config = {
            'id': 'step1',
            'function': 'test.func',
            'output': 'output_key',
            'transitions': [
                {
                    'condition': ['status_a', 'status_b'],
                    'next': 'step_or_success'
                }
            ]
        }
        strategy = CallFunctionStrategy(step_config, self.mock_engine_context)
        
        # Test Match first value
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = 'status_a'
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_or_success')

        # Test Match second value
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = 'status_b'
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_step_or_success')

        # Test No Match
        state = {'_collector_nodes': {}, '_attempt_counts': {}, '_node_execution_order': [], '_messages': [], '_conversations': {}}
        result = 'status_c'
        new_state = strategy._handle_transition_routing(state, result)
        self.assertEqual(new_state['_status'], 'step1_failed')

if __name__ == '__main__':
    unittest.main()
