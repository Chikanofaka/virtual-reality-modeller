import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createNavigation,pointInPolygon,pearlNavigationConfig} from '../runtime/navigation.js';
import {verifyBuildIdentity} from '../runtime/build-identity.js';

test('adjacent surfaces share a seamless walkable union including boundary',()=>{
  const nav=createNavigation({runtime:{playerRadius:.22},navigation:{polygons:[{vertices:[[0,0],[5,0],[5,5],[0,5]]},{vertices:[[5,0],[10,0],[10,5],[5,5]]}]}});
  assert.equal(pointInPolygon(5,2,[[0,0],[5,0],[5,5],[0,5]]),true);
  assert.equal(nav.canMove(5,2),true);assert.equal(nav.canMove(.1,2),false);
  const pos={x:2,z:2};nav.move(pos,6,0);assert.ok(Math.abs(pos.x-8)<1e-8);
});
test('substeps prevent crossing thin barriers and allow sliding',()=>{
  const nav=createNavigation({runtime:{playerRadius:.22},navigation:{polygons:[{vertices:[[0,0],[10,0],[10,10],[0,10]]}],segments:[{a:[5,0],b:[5,10],thickness:.08}]}});
  const pos={x:2,z:2};nav.move(pos,6,3);assert.ok(pos.x<4.75);assert.ok(pos.z>4.9);
});
test('Pearl spawn, glass ring and sole southeast portal are enforced',()=>{
  const nav=createNavigation(pearlNavigationConfig());
  assert.equal(nav.canMove(-11.75,2.35),true);assert.equal(nav.canMove(0,0),true);assert.equal(nav.canMove(7.25,-.25),false);
  assert.equal(nav.canMove(5.22,2.72),true);assert.equal(nav.canMove(30,30),false);
  const blocked={x:8,z:-.25};nav.move(blocked,-2,0);assert.ok(blocked.x>7.4);
  const portal={x:6.5,z:3.7};nav.move(portal,-2.6,-2);assert.ok(portal.x<4&&portal.z<2);
});
test('approved Pearl route is walkable at 3.5 cm spacing',()=>{
  const plan=JSON.parse(readFileSync(new URL('../examples/pearl-office/planning.json',import.meta.url)));
  const nav=createNavigation(plan);
  for(const route of plan.navigation.routes)for(let i=1;i<route.points.length;i++){
    const a=route.points[i-1],b=route.points[i],steps=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])/.035);
    for(let j=0;j<=steps;j++){const x=a[0]+(b[0]-a[0])*j/steps,z=a[1]+(b[1]-a[1])*j/steps;assert.ok(nav.canMove(x,z),`${route.id} blocked at ${x},${z}`);}
  }
});
test('missing, stale and wrong-port build URLs are blocked',()=>{
  const build={buildId:'abc123',version:'1.0',expectedPort:8123};
  assert.equal(verifyBuildIdentity(build,{search:'?build=abc123',port:'8123'}).ok,true);
  assert.equal(verifyBuildIdentity(build,{search:'?build=old',port:'8123'}).ok,false);
  assert.equal(verifyBuildIdentity(build,{search:'',port:'8123'}).ok,false);
  assert.equal(verifyBuildIdentity(build,{search:'?build=abc123',port:'8124'}).ok,false);
});
