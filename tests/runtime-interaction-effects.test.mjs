import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../runtime/vendor/three.module.js';
import {createInteractionEffects} from '../runtime/interaction-effects.js';

function furniture(id = 'tv', objectName = 'TVScreen', extra = {}) {
  return { id, interaction: { effects: [{ objectName, emissive: '#5080ff', intensity: 2, ...extra }] } };
}
function fixture() {
  const scene = new THREE.Scene();
  const material = new THREE.MeshStandardMaterial({ emissive: '#203040', emissiveIntensity: .25 });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(), material);
  mesh.name = 'TVScreen';
  const neighbor = new THREE.Mesh(mesh.geometry, material);
  neighbor.name = 'AdjacentTV';
  scene.add(mesh, neighbor);
  return { scene, mesh, neighbor, material };
}

test('plans without effects do not inspect the scene or change legacy materials', () => {
  const untouched = { traverse() { throw new Error('Should not traverse'); } };
  for (const config of [undefined, [], [{id: 'desk'}], [{id: 'desk', interaction: {effects: []}}]]) {
    const effects = createInteractionEffects(untouched, config);
    assert.equal(effects.activate('desk'), false);
    effects.reset();
    assert.deepEqual(effects.snapshot(), {enabled: false, targets: []});
  }
});

test('activation changes only bound material clones; repeat/reset preserve identities and transforms', () => {
  const {scene, mesh, neighbor, material} = fixture();
  const group = new THREE.Group();
  group.position.set(2, 3, 4); group.rotation.set(.1, .2, .3); group.scale.set(2, 2, 2);
  mesh.position.set(.5, 1, 2); group.add(mesh); scene.add(group);
  scene.updateMatrixWorld(true);
  const world = mesh.matrixWorld.clone();
  const originalColor = material.emissive.clone();
  const source = furniture();
  const effects = createInteractionEffects(scene, [source]);
  const clone = mesh.material;
  assert.notEqual(clone, material);
  assert.equal(neighbor.material, material);
  assert.equal(mesh.parent, group);
  assert.ok(mesh.matrixWorld.equals(world));
  assert.equal(effects.activate('missing'), false);
  source.interaction.effects[0].intensity = 19;
  source.interaction.effects[0].emissive = '#ff0000';
  for (let cycle = 0; cycle < 3; cycle++) {
    assert.equal(effects.activate('tv'), true);
    assert.equal(effects.activate('tv'), true);
    assert.equal(clone.emissive.getHexString(), '5080ff');
    assert.equal(clone.emissiveIntensity, 2);
    assert.ok(material.emissive.equals(originalColor));
    assert.equal(material.emissiveIntensity, .25);
    assert.equal(effects.snapshot().targets[0].active, true);
    effects.reset();
    assert.equal(mesh.material, clone, 'Reset must not allocate another material');
    assert.ok(clone.emissive.equals(originalColor));
    assert.equal(clone.emissiveIntensity, .25);
    assert.equal(effects.snapshot().targets[0].active, false);
  }
  scene.updateMatrixWorld(true);
  assert.ok(mesh.matrixWorld.equals(world));
});

test('each material slot and each target has its own state and exact reset baseline', () => {
  const {scene, mesh, material} = fixture();
  const second = new THREE.MeshPhongMaterial({emissive: '#112233', emissiveIntensity: .75});
  // Preserve the full linear color rather than a lossy hexadecimal round trip.
  second.emissive.setRGB(.123456789, .234567891, .345678912);
  mesh.material = [material, second];
  const lamp = new THREE.Mesh(mesh.geometry, material); lamp.name = 'Lamp'; scene.add(lamp);
  const effects = createInteractionEffects(scene, [furniture(), furniture('bedroom', 'Lamp', {intensity: 0})]);
  const clones = [...mesh.material, lamp.material];
  assert.notEqual(clones[0], clones[2]);
  effects.activate('tv');
  assert.equal(lamp.material.emissiveIntensity, .25);
  effects.activate('bedroom');
  assert.equal(lamp.material.emissiveIntensity, 0);
  assert.deepEqual(effects.snapshot().targets.map(t => t.active), [true, true]);
  assert.equal(mesh.material.length, 2);
  for (const clone of mesh.material) assert.equal(clone.emissiveIntensity, 2);
  effects.reset();
  assert.equal(mesh.material[0], clones[0]); assert.equal(mesh.material[1], clones[1]);
  assert.ok(mesh.material[0].emissive.equals(material.emissive));
  assert.ok(mesh.material[1].emissive.equals(second.emissive));
  assert.equal(mesh.material[1].emissiveIntensity, .75);
});

test('snapshots expose actual values without leaking mutable internal state', () => {
  const {scene, mesh} = fixture();
  const effects = createInteractionEffects(scene, [furniture()]);
  const snapshot = effects.snapshot();
  assert.deepEqual(snapshot, {enabled: true, targets: [{targetId: 'tv', active: false, effects: [{
    objectName: 'TVScreen', planned: {emissive: '#5080ff', intensity: 2},
    materials: [{initial: {emissive: '#203040', intensity: .25}, current: {emissive: '#203040', intensity: .25}}]
  }]}]});
  snapshot.targets[0].effects[0].planned.intensity = 19;
  snapshot.targets[0].effects[0].materials[0].initial.intensity = 18;
  effects.activate('tv');
  assert.equal(mesh.material.emissiveIntensity, 2);
  mesh.material.emissiveIntensity = 3;
  assert.equal(effects.snapshot().targets[0].effects[0].materials[0].current.intensity, 3);
  effects.reset();
  assert.equal(mesh.material.emissiveIntensity, .25);
});

test('one interaction can activate several named meshes with distinct visual responses', () => {
  const {scene, mesh, neighbor, material} = fixture();
  const config = furniture();
  config.interaction.effects.push({objectName: neighbor.name, emissive: '#ffaa55', intensity: .5});
  const effects = createInteractionEffects(scene, [config]);
  assert.equal(effects.activate('missing'), false);
  assert.equal(effects.snapshot().targets[0].active, false);
  effects.activate('tv');
  assert.equal(mesh.material.emissive.getHexString(), '5080ff');
  assert.equal(mesh.material.emissiveIntensity, 2);
  assert.equal(neighbor.material.emissive.getHexString(), 'ffaa55');
  assert.equal(neighbor.material.emissiveIntensity, .5);
  assert.notEqual(mesh.material, neighbor.material);
  assert.equal(material.emissiveIntensity, .25);
  effects.reset();
  for (const object of [mesh, neighbor]) {
    assert.ok(object.material.emissive.equals(material.emissive));
    assert.equal(object.material.emissiveIntensity, .25);
  }
});

test('missing, duplicate, non-mesh and shared effect names fail before material replacement', () => {
  for (const scenario of ['missing', 'duplicate', 'non-mesh', 'cross-target', 'same-target']) {
    const {scene, mesh, material} = fixture();
    let config = [furniture()];
    if (scenario === 'missing') config.push(furniture('lamp', 'Missing'));
    if (scenario === 'duplicate') { const object = new THREE.Object3D(); object.name = mesh.name; scene.add(object); }
    if (scenario === 'non-mesh') { scene.remove(mesh); const object = new THREE.Object3D(); object.name = mesh.name; scene.add(object); }
    if (scenario === 'cross-target') config.push(furniture('other-tv'));
    if (scenario === 'same-target') config[0].interaction.effects.push({...config[0].interaction.effects[0]});
    assert.throws(() => createInteractionEffects(scene, config), /Interaction effects:/, scenario);
    assert.equal(mesh.material, material, `${scenario} must not leave a partially bound scene`);
  }
});

test('unsupported material slots are rejected atomically, even after another valid binding', () => {
  for (const badMaterials of [[new THREE.MeshStandardMaterial(), new THREE.MeshBasicMaterial()], [], [null]]) {
    const {scene, mesh, material} = fixture();
    const lamp = new THREE.Mesh(mesh.geometry, badMaterials); lamp.name = 'Lamp'; scene.add(lamp);
    assert.throws(() => createInteractionEffects(scene, [furniture(), furniture('lamp', 'Lamp')]), /every material slot/);
    assert.equal(mesh.material, material);
    assert.equal(lamp.material, badMaterials);
  }
});

test('invalid effect values cannot silently become a different visual response', () => {
  for (const invalid of [{intensity: NaN}, {intensity: Infinity}, {intensity: -1}, {intensity: 21}, {emissive: 'red'}, {objectName: ''}]) {
    const {scene, mesh, material} = fixture();
    assert.throws(() => createInteractionEffects(scene, [furniture('tv', 'TVScreen', invalid)]), /invalid effect/);
    assert.equal(mesh.material, material);
  }
});
