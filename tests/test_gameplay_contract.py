"""Reject plans whose custom goal cannot be completed in the runtime."""
import contextlib
import copy
import io
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import harness as h


class CustomGameContractTests(unittest.TestCase):
    def setUp(self):
        self.plan = h.read(h.ROOT / 'templates/external-user-game.json')

    def test_custom_goal_has_connected_interaction_approaches(self):
        result = h.validate_config(self.plan)
        self.assertEqual(result['walkableCells'], result['connectedCells'])

    def test_objectives_require_interactive_targets_and_unique_ids(self):
        changes = [('targetId', 'missing'), ('id', self.plan['gameplay']['objectives'][0]['id'])]
        for key, value in changes:
            plan = copy.deepcopy(self.plan)
            plan['gameplay']['objectives'][1][key] = value
            with self.assertRaises(ValueError):
                h.validate_config(plan, False)
        del self.plan['furniture'][0]['interaction']
        with self.assertRaisesRegex(ValueError, 'with an interaction'):
            h.validate_config(self.plan, False)

    def test_unreachable_or_permanently_shadowed_target_is_rejected(self):
        for position in ([1000, 0, 1000], self.plan['furniture'][0]['position']):
            plan = copy.deepcopy(self.plan)
            plan['furniture'][1]['position'] = position
            with self.assertRaisesRegex(ValueError, 'no reachable nearest-interaction approach'):
                h.validate_config(plan)

    def test_gameplay_shape_and_legacy_mode_are_explicit(self):
        for bad in (None, {}, {'objectives': [], 'completionMessage': 'Done'},
                    {'objectives': [None], 'completionMessage': 'Done'}):
            plan = copy.deepcopy(self.plan)
            plan['gameplay'] = bad
            with self.assertRaises(ValueError):
                h.validate_config(plan, False)
        self.plan['scene']['mode'] = 'pearl-v7'
        with self.assertRaisesRegex(ValueError, 'procedural or imported'):
            h.validate_config(self.plan, False)

    def test_browser_targets_belong_to_the_new_owner(self):
        self.plan['runtime']['browsers'] = ['chrome']
        h.validate_config(self.plan, False)
        for browsers in ([], ['unknown'], ['chrome', 'chrome'], [None], [['chrome']]):
            self.plan['runtime']['browsers'] = browsers
            with self.assertRaisesRegex(ValueError, 'Target browsers'):
                h.validate_config(self.plan, False)

    def test_malformed_sections_fail_with_actionable_errors(self):
        for field in ('project', 'provenance', 'shell', 'entrance', 'navigation', 'materials', 'runtime', 'scene'):
            plan = copy.deepcopy(self.plan)
            plan[field] = None
            with self.assertRaisesRegex(ValueError, 'must be an object'):
                h.validate_config(plan, False)
        for field in ('rooms', 'doors', 'furniture', 'assets'):
            plan = copy.deepcopy(self.plan)
            plan[field] = [None]
            with self.assertRaisesRegex(ValueError, 'list of objects'):
                h.validate_config(plan, False)
