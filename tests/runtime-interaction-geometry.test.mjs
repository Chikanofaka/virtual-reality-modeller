import test from 'node:test';
import assert from 'node:assert/strict';
import {interactionVisible,selectNearestInteraction} from '../runtime/interaction-geometry.js';

const wall=(a,b,thickness=0)=>({a,b,thickness});
const config=(segments,extra={})=>({runtime:{interactionOcclusion:'structural-segments'},navigation:{segments},...extra});
const target=(id,x,z,y=0)=>({id,position:[x,y,z]});

test('legacy distance selection is unchanged when occlusion is absent or none',()=>{
  const candidates=[target('first',1,0,100),target('equal',-1,0),target('farther',1.5,0)];
  const navigation={segments:[wall([.5,-1],[.5,1],.2)]};
  for(const cfg of [{navigation},{runtime:{interactionOcclusion:'none'},navigation}]) {
    assert.equal(interactionVisible(cfg,[0,0],[1,0]),true);
    assert.equal(selectNearestInteraction(cfg,[0,0],candidates),candidates[0]);
  }
  assert.equal(selectNearestInteraction({},[0,0],[target('boundary',2.15,0)]),null);
  assert.equal(selectNearestInteraction({},[0,0],[target('inside',2.149,0)])?.id,'inside');
  assert.equal(selectNearestInteraction({},[0,0],[target('custom boundary',1,0)],1),null);
  assert.equal(selectNearestInteraction({},[0,0],[]),null);
});

test('a nearer object across a structural wall is skipped for a visible object',()=>{
  const cfg=config([wall([.5,-1],[.5,1],.1)]);
  const candidates=[target('behind wall',1,0),target('same room',-1.5,0)];
  assert.equal(selectNearestInteraction(cfg,[0,0],candidates),candidates[1]);
  assert.equal(selectNearestInteraction(cfg,[0,0],[candidates[0]]),null);
});

test('doorway gaps remain visible with no player-radius expansion',()=>{
  const cfg=config([wall([1,-3],[1,-.6],.2),wall([1,.6],[1,3],.2)]);
  cfg.runtime.playerRadius=.5;
  assert.equal(interactionVisible(cfg,[0,0],[2,0]),true);
  assert.equal(interactionVisible(cfg,[0,.45],[2,.45]),true);
  assert.equal(interactionVisible(cfg,[0,.55],[2,.55]),false);
  assert.equal(interactionVisible(cfg,[0,.8],[2,.8]),false);
});

test('thin and diagonal walls cannot be missed between visibility samples',()=>{
  const cfg=config([wall([.123456789,-.01],[.123456789,.01],.000001)]);
  assert.equal(interactionVisible(cfg,[0,0],[2,0]),false);
  assert.equal(interactionVisible(config([wall([.4,.1],[.6,-.1])]),[0,0],[1,0]),false);
  assert.equal(interactionVisible(config([wall([.4,1],[.6,.8])]),[0,0],[1,0]),true);
});

test('crossings, endpoints, collinear overlap and separated collinear lines are exact',()=>{
  assert.equal(interactionVisible(config([wall([1,-1],[1,1])]),[0,0],[2,0]),false);
  assert.equal(interactionVisible(config([wall([1,0],[1,1])]),[0,0],[1,0]),false);
  assert.equal(interactionVisible(config([wall([1,0],[3,0])]),[0,0],[2,0]),false);
  assert.equal(interactionVisible(config([wall([3,0],[4,0])]),[0,0],[2,0]),true);
  assert.equal(interactionVisible(config([wall([4,0],[3,0])]),[2,0],[0,0]),true);
});

test('capsule side and round endpoint contact block, but outside clearance does not',()=>{
  const cfg=config([wall([1,0],[2,0],.5)]);
  assert.equal(interactionVisible(cfg,[0,.25],[3,.25]),false);
  assert.equal(interactionVisible(cfg,[0,.251],[3,.251]),true);
  assert.equal(interactionVisible(cfg,[2.25,-1],[2.25,1]),false);
  assert.equal(interactionVisible(cfg,[2.251,-1],[2.251,1]),true);
});

test('zero length sight lines and wall segments retain capsule semantics',()=>{
  const cfg=config([wall([1,0],[1,0],.5)]);
  assert.equal(interactionVisible(cfg,[0,0],[2,0]),false);
  assert.equal(interactionVisible(cfg,[1,.25],[1,.25]),false);
  assert.equal(interactionVisible(cfg,[1,.251],[1,.251]),true);
  assert.equal(interactionVisible(config([wall([1,0],[1,0])]),[0,0],[2,0]),false);
  assert.equal(interactionVisible(config([wall([1,1],[1,1])]),[0,0],[0,0]),true);
  assert.equal(interactionVisible(config([wall([1,0],[2,0])]),[1.5,0],[1.5,0]),false);
});

test('furniture AABBs and target elevation do not implement structural occlusion',()=>{
  const cfg=config([]);
  cfg.navigation.blockers=[{bounds:[.25,-1,.75,1]}];
  cfg.runtime.playerRadius=1;
  assert.equal(interactionVisible(cfg,[0,0],[1,0]),true);
  assert.equal(selectNearestInteraction(cfg,[0,0],[target('high',1,0,50)])?.id,'high');
});
