import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from '../runtime/vendor/three.module.js';
import {createPearlScene} from '../runtime/scene-pearl.js';
import {createPlannedScene} from '../runtime/scene-planned.js';
// Geometry-only checks: a no-op Canvas2D surface lets Three create label textures.
// This does not claim a real GPU/browser rendering result.
const ctx=new Proxy({},{get:()=>()=>{}});
globalThis.document={createElement:()=>({width:0,height:0,getContext:()=>ctx})};
const plan=JSON.parse(readFileSync(new URL('../examples/pearl-office/planning.json',import.meta.url)));
const visual=createPearlScene(THREE,plan);visual.scene.updateMatrixWorld(true);

test('preserved Pearl detail and every interactive object survive extraction',()=>{
  let meshes=0;visual.scene.traverse(o=>{if(o.isMesh)meshes++;});
  assert.ok(meshes>400,`Expected full source detail, got ${meshes} meshes`);
  assert.equal(visual.zones.length,13);assert.ok(visual.interactables.length>=10);
  for(const item of visual.interactables)assert.ok(item.obj?.isObject3D,item.label);
  const console=visual.interactables.find(i=>i.type==='pearl');assert.equal(console.obj.name,'DeskTop');
  assert.ok(visual.scene.getObjectByName('PearlGlass'));assert.ok(visual.scene.getObjectByName('Monitor'));
});
test('Pearl floor has upward triangle winding and original plan Z orientation',()=>{
  const g=visual.floor.geometry,idx=g.index,p=g.attributes.position,n=g.attributes.normal;
  let minZ=Infinity,maxZ=-Infinity;
  for(let i=0;i<p.count;i++){minZ=Math.min(minZ,p.getZ(i));maxZ=Math.max(maxZ,p.getZ(i));assert.ok(n.getY(i)>.999);}
  assert.ok(minZ< -10);assert.ok(maxZ>7.7&&maxZ<7.9);
  for(let i=0;i<idx.count;i+=3){const a=new THREE.Vector3().fromBufferAttribute(p,idx.getX(i)),b=new THREE.Vector3().fromBufferAttribute(p,idx.getX(i+1)),c=new THREE.Vector3().fromBufferAttribute(p,idx.getX(i+2));assert.ok(b.sub(a).cross(c.sub(a)).y>=-1e-8);}
  for(const polygon of plan.navigation.polygons)assert.ok(visual.scene.getObjectByName('NavigationFloor_'+polygon.id),'Supporting floor covers '+polygon.id);
});
test('procedural game exposes stable furniture IDs for its objectives',()=>{
  const config=JSON.parse(readFileSync(new URL('../templates/measured-studio.json',import.meta.url)));
  config.furniture[0].interaction={label:'Inspect desk',message:'Desk found'};
  const planned=createPlannedScene(THREE,config);
  assert.equal(planned.interactables.length,1);
  const item=planned.interactables[0];assert.equal(item.id,'work-desk');
  assert.ok(item.obj.isMesh);assert.equal(item.label,'Inspect desk');assert.equal(item.message,'Desk found');
  assert.equal(item.obj.position.x,config.furniture[0].position[0]);
});
test('imported scenes preserve interaction anchors without duplicate primitive furniture',()=>{
  const config=JSON.parse(readFileSync(new URL('../templates/measured-studio.json',import.meta.url)));
  config.scene.mode='imported-glb';
  for(const item of config.furniture)item.interaction={label:'Inspect '+item.id,message:'Found '+item.id};
  const imported=createPlannedScene(THREE,config);
  assert.equal(imported.interactables.length,2);assert.equal(imported.zones.length,1);
  for(const item of imported.interactables){
    const furniture=config.furniture.find(f=>f.id===item.id);
    assert.ok(item.obj.isObject3D);assert.equal(item.obj.isMesh,undefined);assert.equal(item.obj.visible,false);
    assert.deepEqual(item.obj.position.toArray(),furniture.position);
    assert.equal(imported.scene.getObjectByName(item.id),undefined);
  }
  const meshes=[];imported.scene.traverse(object=>{if(object.isMesh)meshes.push(object);});
  assert.equal(meshes.length,config.navigation.polygons.length,'Only navigation floor is generated before model import');
});
