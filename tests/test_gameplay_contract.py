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

    def test_interaction_occlusion_is_opt_in_and_requires_a_known_mode(self):
        self.plan['furniture'][1]['position'] = [4.3, 0, 1.8]
        # This target is just outside the east wall, close enough to activate
        # under the legacy proximity rule. All actual floor cells stay connected.
        result = h.validate_config(self.plan)
        self.assertEqual(result['walkableCells'], result['connectedCells'])
        self.plan['runtime']['interactionOcclusion'] = 'none'
        h.validate_config(self.plan)
        self.plan['runtime']['interactionOcclusion'] = 'structural-segments'
        with self.assertRaisesRegex(ValueError, 'no reachable nearest-interaction approach: reading-chair'):
            h.validate_config(self.plan)
        for bad in (None, '', 'mesh-raycast', True, 1, [], {}):
            self.plan['runtime']['interactionOcclusion'] = bad
            with self.assertRaisesRegex(ValueError, 'runtime.interactionOcclusion'):
                h.validate_config(self.plan, False)

    def test_occluded_nearer_target_does_not_shadow_visible_objective(self):
        self.plan['rooms'][0].update(open=True, accessPoint=[.5, .5])
        self.plan['doors'] = []
        self.plan['entrance']['position'] = [.5, 1.65, .5]
        self.plan['navigation'].update(
            polygons=[{'id': 'test-floor', 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}],
            blockers=[],
            segments=[{'id': 'wall', 'a': [1.2, -2], 'b': [1.2, 2], 'thickness': .1}],
            spawn=[.5, 1.65, .5],
            routes=[{'id': 'inside', 'points': [[.3, .4], [.7, .4]]}])
        self.plan['furniture'][0]['position'] = [1.4, 0, .5]
        self.plan['furniture'][1]['position'] = [-1, 0, .5]
        self.plan['gameplay']['objectives'] = [self.plan['gameplay']['objectives'][1]]
        with self.assertRaisesRegex(ValueError, 'no reachable nearest-interaction approach'):
            h.validate_config(self.plan)
        self.plan['runtime']['interactionOcclusion'] = 'structural-segments'
        h.validate_config(self.plan)

    def test_structural_visibility_handles_thin_crossings_and_degenerate_segments(self):
        self.plan['runtime']['interactionOcclusion'] = 'structural-segments'
        cases = [
            # origin, target, wall a, wall b, thickness, visible
            ([0, 0], [4, 0], [2.001, -1], [2.001, 1], .00001, False),
            ([0, 0], [4, 0], [2, .1], [3, .1], .2, False),
            ([0, 0], [4, 0], [2, .10001], [3, .10001], .2, True),
            ([0, 0], [4, 0], [4, 0], [4, 2], .1, False),
            ([0, 0], [4, 0], [.5, 0], [1, 0], .1, False),
            ([0, 0], [4, 0], [5, 0], [6, 0], .1, True),
            ([0, 0], [4, 4], [0, 4], [4, 0], .1, False),
            ([0, 0], [0, 0], [-1, 0], [1, 0], .1, False),
            ([0, 1], [0, 1], [-1, 0], [1, 0], .1, True),
            ([0, 0], [4, 0], [2, 0], [2, 0], .1, False),
            ([0, 0], [4, 0], [2, 1], [2, 1], .1, True),
            ([0, 0], [0, 0], [0, 0], [0, 0], .1, False),
        ]
        for origin, target, a, b, thickness, visible in cases:
            with self.subTest(origin=origin, target=target, a=a, b=b):
                for first, second in ((a, b), (b, a)):
                    self.plan['navigation']['segments'] = [{'a': first, 'b': second, 'thickness': thickness}]
                    self.assertEqual(h.interaction_visible(self.plan, origin, target), visible)
                    self.assertEqual(h.interaction_visible(self.plan, target, origin), visible)

    def test_structural_visibility_ignores_furniture_and_player_clearance(self):
        self.plan['runtime'].update(interactionOcclusion='structural-segments', playerRadius=1)
        self.plan['navigation'].update(
            blockers=[{'bounds': [.5, -.5, 1.5, .5]}],
            segments=[{'a': [0, .2], 'b': [2, .2], 'thickness': .2}])
        self.assertTrue(h.interaction_visible(self.plan, [0, 0], [2, 0]))

    def test_effects_accept_emissive_changes_for_supported_goal_scenes(self):
        effects = [{'objectName': 'desk-screen', 'emissive': '#A0bbFF', 'intensity': 0},
                   {'objectName': 'desk-lamp', 'emissive': '#ffffff', 'intensity': 20}]
        self.plan['furniture'][0]['interaction']['effects'] = effects
        h.validate_config(self.plan, False)
        self.plan['scene'].update(mode='imported-glb', assetId='room')
        self.plan['assets'] = [{'id': 'room', 'type': 'model', 'path': 'room.glb', 'sha256': '0' * 64}]
        h.validate_config(self.plan, False)

    def test_effects_reject_malformed_entries_and_duplicate_ownership(self):
        valid = {'objectName': 'screen', 'emissive': '#aaccee', 'intensity': 1}
        bad_effects = [None, [], {}, [None], [{}],
                       [{**valid, 'extra': True}],
                       [{**valid, 'objectName': None}], [{**valid, 'objectName': ' \n'}],
                       [{**valid, 'emissive': '#fff'}], [{**valid, 'emissive': 123}],
                       [valid, valid]]
        bad_effects += [[{**valid, 'intensity': bad}] for bad in (None, True, '1', -1, 20.001, float('nan'), float('inf'))]
        for effects in bad_effects:
            with self.subTest(effects=effects):
                plan = copy.deepcopy(self.plan)
                plan['furniture'][0]['interaction']['effects'] = effects
                with self.assertRaisesRegex(ValueError, '[Ii]nteraction effect'):
                    h.validate_config(plan, False)
        for item in self.plan['furniture']:
            item['interaction']['effects'] = [valid.copy()]
        with self.assertRaisesRegex(ValueError, 'unique across all targets'):
            h.validate_config(self.plan, False)

    def test_effects_require_an_objective_target_and_exclude_legacy_scenes(self):
        self.plan['furniture'][0]['interaction']['effects'] = [
            {'objectName': 'screen', 'emissive': '#aaccee', 'intensity': 1}]
        for change in ('no-gameplay', 'non-target', 'pearl'):
            with self.subTest(change=change):
                plan = copy.deepcopy(self.plan)
                if change == 'no-gameplay':
                    del plan['gameplay']
                elif change == 'non-target':
                    plan['gameplay']['objectives'] = [plan['gameplay']['objectives'][1]]
                else:
                    plan['scene']['mode'] = 'pearl-v7'
                with self.assertRaisesRegex(ValueError, 'Interaction effects'):
                    h.validate_config(plan, False)
