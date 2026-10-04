import test from 'node:test';
import assert from 'node:assert/strict';
import {createGameplay} from '../runtime/gameplay.js';

const config={objectives:[
  {id:'find-desk',label:'Inspect desk',targetId:'desk'},
  {id:'find-chair',label:'Inspect chair',targetId:'chair'}
],completionMessage:'Discovery complete.'};

test('plans without gameplay preserve exploration and legacy progression',()=>{
  const game=createGameplay();assert.equal(game.enabled,false);
  assert.equal(game.interact('reception'),false);
  assert.deepEqual(game.snapshot(),{enabled:false,index:0,total:0,complete:false,currentObjective:null,completedObjectiveIds:[]});
});
test('only the current target advances ordered objectives; completion is stable',()=>{
  const game=createGameplay(config);
  assert.equal(game.interact('chair'),false);assert.equal(game.interact('unknown'),false);
  assert.equal(game.snapshot().index,0);
  assert.equal(game.interact('desk'),true);
  assert.equal(game.snapshot().currentObjective.id,'find-chair');
  assert.equal(game.interact('desk'),false);assert.equal(game.snapshot().index,1);
  assert.equal(game.interact('chair'),true);assert.equal(game.snapshot().complete,true);
  assert.deepEqual(game.snapshot().completedObjectiveIds,['find-desk','find-chair']);
  assert.equal(game.snapshot().currentObjective,null);assert.equal(game.interact('chair'),false);
  assert.equal(game.snapshot().index,2);assert.equal(game.completionMessage,'Discovery complete.');
});
test('reset after partial or complete play restores the first objective',()=>{
  const game=createGameplay(config);
  for(const targets of [['desk'],['desk','chair']]) {
    targets.forEach(target=>game.interact(target));game.reset();
    assert.equal(game.snapshot().index,0);assert.equal(game.snapshot().complete,false);
    assert.equal(game.snapshot().currentObjective.id,'find-desk');
    assert.deepEqual(game.snapshot().completedObjectiveIds,[]);
    assert.equal(game.interact('chair'),false);
  }
});
test('diagnostic snapshots and source objects cannot mutate live progress',()=>{
  const source=structuredClone(config),game=createGameplay(source);
  source.objectives[0].targetId='chair';
  const snapshot=game.snapshot();snapshot.currentObjective.targetId='chair';snapshot.completedObjectiveIds.push('forged');
  assert.equal(game.interact('chair'),false);assert.equal(game.interact('desk'),true);
  assert.deepEqual(game.snapshot().completedObjectiveIds,['find-desk']);
});
