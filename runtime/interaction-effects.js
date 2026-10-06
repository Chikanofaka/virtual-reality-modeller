/** Bind plan-owned visual responses after imported models have loaded. */
export function createInteractionEffects(scene, furniture = []) {
  const targets = [];
  const names = new Set();
  const targetIds = new Set();
  for (const item of furniture) {
    const effects = item.interaction?.effects;
    if (!effects?.length) continue;
    if (targetIds.has(item.id)) throw new Error(`Interaction effects: duplicate target "${item.id}".`);
    targetIds.add(item.id);
    targets.push({ targetId: item.id, active: false, effects: effects.map(effect => {
      const { objectName, emissive, intensity } = effect;
      if (typeof objectName !== 'string' || !objectName.trim() ||
          typeof emissive !== 'string' || !/^#[0-9a-f]{6}$/i.test(emissive) ||
          !Number.isFinite(intensity) || intensity < 0 || intensity > 20) {
        throw new Error(`Interaction effects: invalid effect for target "${item.id}".`);
      }
      if (names.has(objectName)) throw new Error(`Interaction effects: object "${objectName}" is configured more than once.`);
      names.add(objectName);
      return { objectName, planned: { emissive, intensity } };
    }) });
  }

  // Legacy plans do not traverse the scene or replace any of its materials.
  if (!targets.length) return {
    activate: () => false,
    reset() {},
    snapshot: () => ({ enabled: false, targets: [] })
  };

  const objectsByName = new Map([...names].map(name => [name, []]));
  scene.traverse(object => { objectsByName.get(object.name)?.push(object); });
  for (const target of targets) for (const effect of target.effects) {
    const matches = objectsByName.get(effect.objectName);
    const context = `Interaction effects: target "${target.targetId}", object "${effect.objectName}"`;
    if (matches.length !== 1) {
      throw new Error(`${context} must match exactly one Mesh; found ${matches.length} objects.`);
    }
    const mesh = matches[0];
    if (!mesh.isMesh) throw new Error(`${context} is not a Mesh.`);
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    if (!materials.length || materials.some(material =>
      !material?.isMaterial || !material.emissive?.isColor ||
      !Number.isFinite(material.emissiveIntensity) || typeof material.clone !== 'function')) {
      throw new Error(`${context} needs emissive-capable materials in every material slot.`);
    }
    effect.mesh = mesh;
    effect.sourceMaterials = materials;
  }

  // Validate every binding before changing a scene; clone once, never on interaction/reset.
  const clones = [];
  try {
    for (const target of targets) for (const effect of target.effects) {
      effect.materials = effect.sourceMaterials.map(source => {
        const material = source.clone();
        clones.push(material);
        return { material, initialColor: material.emissive.clone(), initialIntensity: material.emissiveIntensity };
      });
    }
  } catch (error) {
    for (const material of clones) material.dispose();
    throw error;
  }
  for (const target of targets) for (const effect of target.effects) {
    const materials = effect.materials.map(binding => binding.material);
    effect.mesh.material = Array.isArray(effect.mesh.material) ? materials : materials[0];
    delete effect.sourceMaterials;
  }
  const colorValue = color => `#${color.getHexString()}`;
  return {
    activate(targetId) {
      const target = targets.find(candidate => candidate.targetId === targetId);
      if (!target) return false;
      for (const effect of target.effects) for (const { material } of effect.materials) {
        material.emissive.set(effect.planned.emissive);
        material.emissiveIntensity = effect.planned.intensity;
      }
      target.active = true;
      return true;
    },
    reset() {
      for (const target of targets) {
        for (const effect of target.effects) for (const { material, initialColor, initialIntensity } of effect.materials) {
          material.emissive.copy(initialColor);
          material.emissiveIntensity = initialIntensity;
        }
        target.active = false;
      }
    },
    snapshot() {
      return { enabled: true, targets: targets.map(target => ({
        targetId: target.targetId, active: target.active,
        effects: target.effects.map(effect => ({
          objectName: effect.objectName, planned: { ...effect.planned },
          materials: effect.materials.map(({ material, initialColor, initialIntensity }) => ({
            initial: { emissive: colorValue(initialColor), intensity: initialIntensity },
            current: { emissive: colorValue(material.emissive), intensity: material.emissiveIntensity }
          }))
        }))
      })) };
    }
  };
}
