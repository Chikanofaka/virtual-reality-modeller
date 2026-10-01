/** Safari-compatible event normalization and event-source independent state. */
const allowed = new Set(['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','KeyE','KeyM','KeyR','KeyQ']);
const legacy={87:'KeyW',65:'KeyA',83:'KeyS',68:'KeyD',16:'ShiftLeft',37:'ArrowLeft',38:'ArrowUp',39:'ArrowRight',40:'ArrowDown',69:'KeyE',77:'KeyM',82:'KeyR',81:'KeyQ'};
export function normalizedCode(e) {
  if(allowed.has(e.code)) return e.code;
  const key=String(e.key||'').toLowerCase();
  if(/^[wasdemrq]$/.test(key)) return 'Key'+key.toUpperCase();
  if(key==='shift') return e.location===2?'ShiftRight':'ShiftLeft';
  const arrows={arrowleft:'ArrowLeft',arrowright:'ArrowRight',arrowup:'ArrowUp',arrowdown:'ArrowDown'};
  return arrows[key]||legacy[e.which||e.keyCode||0]||'';
}
export function editableTarget(target) {
  return !!target && (['input','textarea','select'].includes(String(target.tagName||'').toLowerCase())||target.isContentEditable);
}
export function createInputState() {
  const physical=new Set(),virtual=new Set();
  let dx=0,dy=0;
  return {
    physical,virtual,
    set(code,down,source='physical') {if(!allowed.has(code))return; const s=source==='virtual'?virtual:physical;down?s.add(code):s.delete(code);},
    held(code){return physical.has(code)||virtual.has(code);},
    look(x,y){dx+=x;dy+=y;},
    consumeLook(){const out=[dx,dy];dx=dy=0;return out;},
    clear(){physical.clear();virtual.clear();dx=dy=0;},
    snapshot(){return {physical:[...physical],virtual:[...virtual],held:[...new Set([...physical,...virtual])]};}
  };
}
export function attachInput({canvas,buttons=[],isStarted,onAction,onNote,window:win=window,document:doc=document}) {
  const state=createInputState(),seen=new WeakSet(),cleanup=[];
  let pointerId=null,lastX=0,lastY=0;
  const listen=(target,type,fn,options)=>{const opts=typeof options==='boolean'?{capture:options}:options;target.addEventListener(type,fn,opts);cleanup.push(()=>target.removeEventListener(type,fn,opts));};
  const note=text=>onNote?.(text);
  function focus(){try{canvas.focus({preventScroll:true});}catch{canvas.focus();}}
  function endDrag(){pointerId=null;canvas.style.cursor='grab';}
  function reset(reason){state.clear();endDrag();for(const button of buttons) button.classList.remove('held');note(reason);}
  function key(e,down) {
    if(seen.has(e))return;seen.add(e);
    const code=normalizedCode(e);if(!code)return;
    // Keyup must release even when focus moved into a field after keydown.
    if(!down){state.set(code,false);return;}
    if(!isStarted()||editableTarget(e.target)||e.metaKey||e.ctrlKey||e.altKey||e.isComposing)return;
    state.set(code,true);e.preventDefault();
    note(`key=${e.key||'?'} code=${e.code||'?'} legacy=${e.which||e.keyCode||0} → ${code}`);
    if(!e.repeat && ['KeyE','KeyM','KeyR','KeyQ'].includes(code)) onAction?.(code);
  }
  const down=e=>key(e,true),up=e=>key(e,false);
  for(const target of [win,doc,canvas]){listen(target,'keydown',down,true);listen(target,'keyup',up,true);}
  canvas.tabIndex=0;canvas.style.cursor='grab';canvas.style.touchAction='none';
  listen(canvas,'pointerdown',e=>{
    if(!isStarted()||e.button!==0||pointerId!==null)return;
    e.preventDefault();focus();pointerId=e.pointerId;lastX=e.clientX;lastY=e.clientY;
    try{canvas.setPointerCapture(e.pointerId);}catch{}
    canvas.style.cursor='grabbing';note('drag look / canvas focused');
  });
  listen(canvas,'pointermove',e=>{if(pointerId!==e.pointerId)return;state.look(e.clientX-lastX,e.clientY-lastY);lastX=e.clientX;lastY=e.clientY;});
  for(const type of ['pointerup','pointercancel','lostpointercapture'])listen(canvas,type,e=>{if(pointerId===e.pointerId)endDrag();});
  listen(win,'pointerup',e=>{if(pointerId===e.pointerId)endDrag();});
  listen(canvas,'click',()=>{if(isStarted())focus();});
  listen(canvas,'contextmenu',e=>e.preventDefault());
  listen(win,'blur',()=>reset('window blur — input cleared'));
  listen(win,'pagehide',()=>reset('page hidden — input cleared'));
  listen(doc,'visibilitychange',()=>{if(doc.hidden)reset('tab hidden — input cleared');});
  for(const button of buttons) {
    const code=button.dataset.move;let heldPointer=null;
    listen(button,'pointerdown',e=>{
      if(!isStarted())return;e.preventDefault();heldPointer=e.pointerId;
      try{button.setPointerCapture(e.pointerId);}catch{}
      state.set(code,true,'virtual');button.classList.add('held');focus();note(`virtual ${code} down`);
    });
    const release=e=>{if(heldPointer!==e.pointerId)return;heldPointer=null;state.set(code,false,'virtual');button.classList.remove('held');};
    for(const type of ['pointerup','pointercancel','lostpointercapture'])listen(button,type,release);
    // Window fallback covers browsers that decline capture.
    listen(win,'pointerup',release);
  }
  return {...state,focus,reset,dispose(){reset('input disposed');cleanup.forEach(fn=>fn());}};
}
