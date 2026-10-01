import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizedCode,createInputState,attachInput} from '../runtime/input.js';

test('Safari normalizes code, upper/lower key, legacy keyCode and which',()=>{
  for(const e of [{code:'KeyW'},{key:'w'},{key:'W'},{keyCode:87},{which:87}])assert.equal(normalizedCode(e),'KeyW');
  assert.equal(normalizedCode({key:'Shift',location:2}),'ShiftRight');
  assert.equal(normalizedCode({key:'ArrowUp'}),'ArrowUp');
  assert.equal(normalizedCode({code:'Unidentified',key:'d'}),'KeyD');
  assert.equal(normalizedCode({key:'Escape'}),'');
});
test('physical and virtual holds cannot clear each other; blur clears buffered look',()=>{
  const state=createInputState();state.set('KeyW',true);state.set('KeyW',true,'virtual');
  state.set('KeyW',false);assert.equal(state.held('KeyW'),true);
  state.set('KeyW',false,'virtual');assert.equal(state.held('KeyW'),false);
  state.look(6,-2);state.look(3,4);assert.deepEqual(state.consumeLook(),[9,2]);assert.deepEqual(state.consumeLook(),[0,0]);
  state.set('KeyD',true);state.look(4,4);state.clear();assert.deepEqual(state.snapshot().held,[]);assert.deepEqual(state.consumeLook(),[0,0]);
});
class Element extends EventTarget {
  constructor(tagName='CANVAS'){super();this.tagName=tagName;this.style={};this.dataset={};this.classList={add(){},remove(){}};}
  focus(){}setPointerCapture(){}
}
function fire(target,type,props={}){const e=new Event(type,{cancelable:true});Object.assign(e,props);target.dispatchEvent(e);return e;}
test('input ignores before entry, handles blur, lost capture, fields and D-pad release',()=>{
  const win=new EventTarget(),doc=new EventTarget(),canvas=new Element(),pad=new Element('BUTTON');pad.dataset.move='KeyW';
  let started=false,actions=0;
  const input=attachInput({canvas,buttons:[pad],window:win,document:doc,isStarted:()=>started,onAction:()=>actions++});
  fire(canvas,'keydown',{code:'KeyW'});assert.equal(input.held('KeyW'),false);
  started=true;fire(canvas,'keydown',{keyCode:87});assert.equal(input.held('KeyW'),true);
  fire(win,'blur');assert.equal(input.held('KeyW'),false);
  fire(canvas,'pointerdown',{pointerId:1,button:0,clientX:10,clientY:10});
  fire(canvas,'pointermove',{pointerId:1,clientX:25,clientY:5});assert.deepEqual(input.consumeLook(),[15,-5]);
  fire(canvas,'lostpointercapture',{pointerId:1});fire(canvas,'pointermove',{pointerId:1,clientX:50,clientY:50});assert.deepEqual(input.consumeLook(),[0,0]);
  fire(pad,'pointerdown',{pointerId:2});assert.equal(input.held('KeyW'),true);
  fire(win,'pointerup',{pointerId:2});assert.equal(input.held('KeyW'),false);
  fire(canvas,'keydown',{code:'KeyE'});fire(canvas,'keydown',{code:'KeyE',repeat:true});assert.equal(actions,1);
  fire(canvas,'keydown',{code:'KeyW',metaKey:true});assert.equal(input.held('KeyW'),false);
  canvas.tagName='INPUT';fire(canvas,'keydown',{code:'KeyW'});assert.equal(input.held('KeyW'),false);
  canvas.tagName='CANVAS';fire(canvas,'keydown',{code:'KeyW'});canvas.tagName='INPUT';fire(canvas,'keyup',{code:'KeyW'});assert.equal(input.held('KeyW'),false);canvas.tagName='CANVAS';
  doc.hidden=true;fire(doc,'visibilitychange');assert.deepEqual(input.snapshot().held,[]);
  input.dispose();fire(canvas,'keydown',{code:'KeyW'});assert.equal(input.held('KeyW'),false);
});
