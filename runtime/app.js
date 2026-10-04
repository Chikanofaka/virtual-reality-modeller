import * as THREE from './vendor/three.module.js';
import {createPearlScene} from './scene-pearl.js';
import {createPlannedScene} from './scene-planned.js';
import {createNavigation,pearlNavigationConfig} from './navigation.js';
import {attachInput} from './input.js';
import {verifyBuildIdentity} from './build-identity.js';
import {loadModels} from './assets.js';
import {createGameplay} from './gameplay.js';

const $=id=>document.getElementById(id);
const diagnostics={ready:false,started:false,frames:0,renderCount:0,simulationTicks:0,errors:[],build:null,actualPort:location.port};
window.__VSMVP=diagnostics;
function fatal(error) {
  const message=error?.message||String(error);diagnostics.errors.push(message);diagnostics.ready=false;
  $('start').hidden=false;$('startDescription').textContent=message;$('enter').disabled=true;
  $('startTitle').textContent='Build needs attention';$('versionBadge').textContent='BLOCKED — '+message;
  $('versionBadge').classList.add('error');console.error(error);
}
window.addEventListener('error',e=>fatal(e.error||e.message));
window.addEventListener('unhandledrejection',e=>fatal(e.reason));

async function loadJSON(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw new Error(`${path}: HTTP ${r.status}. Build and launch through the harness.`);return r.json();}
async function boot() {
  const [build,config]=await Promise.all([loadJSON('build.json'),loadJSON('config.json')]);
  diagnostics.build=build;
  const identity=verifyBuildIdentity(build,location);
  $('versionBadge').textContent=`${build.version} · ${build.buildId} · PORT ${location.port||'default'} · ${identity.reason}`;
  if(!identity.ok)throw new Error(identity.reason);
  const pearl=config.scene?.mode==='pearl-v7';
  const visual=pearl?createPearlScene(THREE,config):createPlannedScene(THREE,config);
  const {scene,sun,interactables,zones,dynamicGlow}=visual;
  const gameplay=createGameplay(config.gameplay);
  const imported=await loadModels(config,scene,message=>{$('startDescription').textContent=message;});
  diagnostics.importedModels=imported.models;diagnostics.importedMeshes=imported.meshes;
  const navigation=createNavigation(config.navigation?.polygons?.length?config:pearlNavigationConfig());
  for(const item of interactables) if(!item.obj?.position)throw new Error(`Invalid interactable: ${item.label}. Scene adapter must return positioned objects.`);
  if(gameplay.enabled)for(const objective of config.gameplay.objectives)if(!interactables.some(item=>item.id===objective.targetId))throw new Error(`Objective ${objective.id} has no interactive target: ${objective.targetId}`);
  const spawn=config.navigation?.spawn||config.entrance?.position||[-11.75,1.68,2.35];
  const eyeHeight=config.runtime?.eyeHeight||spawn[1]||1.68;
  const initialYaw=config.entrance?.yaw??-.95;
  if(!navigation.canMove(spawn[0],spawn[2]))throw new Error(`Spawn [${spawn[0]}, ${spawn[2]}] is outside the connected walkable surface or inside a barrier.`);
  const camera=new THREE.PerspectiveCamera(66,innerWidth/innerHeight,.05,120);camera.rotation.order='YXZ';
  const renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.35));renderer.setSize(innerWidth,innerHeight);
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.22;
  const canvas=renderer.domElement;canvas.id='gameCanvas';canvas.setAttribute('aria-label','3D space. Press WASD to move. Drag to look.');
  canvas.style.willChange='transform';canvas.style.transform='translateZ(0)';
  document.body.prepend(canvas);
  let started=false,yaw=initialYaw,pitch=0,stage=0,nearest=null,cinematic=false,resizePending=false,qualityPending=false;
  let note='ready / click Enter',lastTime=0,uiElapsed=0,glowElapsed=0,waypoint=null;
  let sceneMeshCount=0;scene.traverse(o=>{if(o.isMesh)sceneMeshCount++;});
  diagnostics.meshCount=sceneMeshCount;diagnostics.legacyVisualColliderCount=visual.legacyVisualColliderCount;
  diagnostics.interactableCount=interactables.length;
  function toast(text){$('toast').textContent=text;$('toast').classList.add('visible');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.remove('visible'),2600);}
  function objective(text){$('objective').textContent='Objective: '+text;}
  function updateObjective(){objective(gameplay.enabled?(gameplay.snapshot().currentObjective?.label||gameplay.completionMessage):pearl?'check in at Reception (E)':'explore your planned space');}
  function findNearest(){
    let best=null,distance=2.15;
    for(const item of interactables){const d=Math.hypot(camera.position.x-item.obj.position.x,camera.position.z-item.obj.position.z);if(d<distance){distance=d;best=item;}}
    return best;
  }
  function reset(){camera.position.set(spawn[0],eyeHeight,spawn[2]);yaw=initialYaw;pitch=0;stage=0;gameplay.reset();nearest=null;waypoint=null;input?.reset('reset to entrance');updateObjective();}
  function interact() {
    // Actions use the current location, even between throttled HUD updates.
    nearest=findNearest();
    if(!nearest){toast('Move closer to an interactive object.');return;}
    if(['meeting','wine'].includes(nearest.type)) {
      // Clone shared source materials before changing one interactive feature.
      if(!nearest.ownsMaterial){nearest.obj.material=nearest.obj.material.clone();nearest.ownsMaterial=true;}
      nearest.obj.material.emissiveIntensity=nearest.obj.material.emissiveIntensity>4?2.3:5.5;
    }
    toast(nearest.message||nearest.label);
    if(gameplay.enabled){
      if(gameplay.interact(nearest.id)){updateObjective();if(gameplay.snapshot().complete)toast(gameplay.completionMessage);}
      return;
    }
    if(stage===0&&nearest.type==='reception'){stage=1;objective('follow the circulation loop to the Wine Room');}
    else if(stage===1&&nearest.type==='wine'){stage=2;objective('enter the Pearl Office through its southeast opening');}
    else if(stage===2&&nearest.type==='pearl'){stage=3;objective('tour complete — explore freely');toast('Pearl Office console online. Tour complete.');}
  }
  const input=attachInput({canvas,buttons:[...document.querySelectorAll('[data-move]')],isStarted:()=>started,onNote:text=>note=text,onAction:code=>{
    if(code==='KeyE')interact();
    if(code==='KeyM')$('mapWrap').hidden=!$('mapWrap').hidden;
    if(code==='KeyR')reset();
    if(code==='KeyQ'){cinematic=!cinematic;qualityPending=true;toast(cinematic?'Cinematic detail enabled':'Balanced detail enabled');}
  }});
  reset();
  $('startTitle').textContent=config.project?.name||(pearl?'Pearl Office':'Virtual Space');
  $('eyebrow').textContent=pearl?'Pearl Office / V7 preserved scene':'Virtual Space / approved planning pack';
  $('startDescription').textContent=pearl?'Explore all 13 detailed zones with WASD and click-drag look. Check in at Reception, visit Wine, then reach the Pearl Office console. The movement pad helps diagnose keyboard focus.':gameplay.enabled?'Your space is ready. Walk with WASD, drag to look, and press E near objects to complete the objectives in order.':'Your approved plan is ready. Click Enter, use WASD to walk, drag to look, and click the minimap to place a destination marker.';
  $('enter').textContent='PREPARING FIRST FRAME…';
  $('enter').onclick=()=>{if(!diagnostics.ready)return;started=true;diagnostics.started=true;$('start').hidden=true;input.focus();toast('WASD move · drag look · E interact · M minimap · R reset');};
  $('interactButton').onclick=()=>{if(started){interact();input.focus();}};
  $('resetButton').onclick=()=>{reset();input.focus();};
  $('mapToggle').onclick=()=>{$('mapWrap').hidden=!$('mapWrap').hidden;input.focus();};
  const map=$('mapCanvas'),ctx=map.getContext('2d');
  const pts=navigation.polygons.flat(),minX=Math.min(...pts.map(p=>p[0]))-1,maxX=Math.max(...pts.map(p=>p[0]))+1,minZ=Math.min(...pts.map(p=>p[1]))-1,maxZ=Math.max(...pts.map(p=>p[1]))+1;
  const mapPoint=(x,z)=>[(x-minX)/(maxX-minX)*map.width,(z-minZ)/(maxZ-minZ)*map.height];
  function paintMap(){
    ctx.clearRect(0,0,map.width,map.height);ctx.fillStyle='#09131b';ctx.fillRect(0,0,map.width,map.height);
    for(const polygon of navigation.polygons){ctx.beginPath();polygon.forEach(([x,z],i)=>{const [a,b]=mapPoint(x,z);i?ctx.lineTo(a,b):ctx.moveTo(a,b);});ctx.closePath();ctx.fillStyle='#c8c2b5';ctx.fill();}
    for(const v of zones){ctx.save();const [x,z]=mapPoint(v.x,v.z);ctx.translate(x,z);ctx.rotate(-(v.rot||0));ctx.strokeStyle='#7c705e';ctx.lineWidth=1;ctx.strokeRect(-v.w/(maxX-minX)*map.width/2,-v.d/(maxZ-minZ)*map.height/2,v.w/(maxX-minX)*map.width,v.d/(maxZ-minZ)*map.height);ctx.restore();}
    ctx.strokeStyle='#246982';ctx.lineWidth=3;
    for(const s of navigation.segments){ctx.beginPath();ctx.moveTo(...mapPoint(...s.a));ctx.lineTo(...mapPoint(...s.b));ctx.stroke();}
    ctx.fillStyle='#516170';for(const b of navigation.blockers){const [x1,z1]=mapPoint(b.bounds[0],b.bounds[1]),[x2,z2]=mapPoint(b.bounds[2],b.bounds[3]);ctx.fillRect(x1,z1,x2-x1,z2-z1);}
    if(waypoint){const [x,z]=mapPoint(waypoint.x,waypoint.z);ctx.beginPath();ctx.arc(x,z,7,0,Math.PI*2);ctx.strokeStyle='#dc6a1f';ctx.stroke();}
    const [x,z]=mapPoint(camera.position.x,camera.position.z);ctx.save();ctx.translate(x,z);ctx.rotate(-yaw);ctx.fillStyle='#ff4d32';ctx.beginPath();ctx.moveTo(0,-9);ctx.lineTo(-6,6);ctx.lineTo(6,6);ctx.closePath();ctx.fill();ctx.restore();
  }
  map.addEventListener('click',e=>{
    const rect=map.getBoundingClientRect(),x=minX+(e.clientX-rect.left)/rect.width*(maxX-minX),z=minZ+(e.clientY-rect.top)/rect.height*(maxZ-minZ);
    if(!navigation.canMove(x,z)){toast('Choose a reachable floor location.');return;}
    waypoint={x,z};toast('Destination marked on the minimap.');paintMap();input.focus();
  });
  function currentZone(){
    if(pearl&&((camera.position.x/7.25)**2+((camera.position.z+.25)/4.15)**2)<.85)return 'Pearl Office';
    for(const v of zones){const dx=camera.position.x-v.x,dz=camera.position.z-v.z,c=Math.cos(v.rot||0),s=Math.sin(v.rot||0);if(Math.abs(dx*c-dz*s)<v.w/2&&Math.abs(dx*s+dz*c)<v.d/2)return v.name.replace(/^\d+\s+/,'');}
    return 'Circulation / entrance';
  }
  function updateHUD(){
    const best=findNearest();
    nearest=best;$('interaction').textContent=best?'Press E — '+best.label:'';
    $('interaction').classList.toggle('visible',!!best);
    $('zone').textContent='Current zone: '+currentZone();
    const state=input.snapshot();
    $('status').textContent=`x ${camera.position.x.toFixed(2)} / z ${camera.position.z.toFixed(2)} · physical: ${state.physical.join(',')||'—'} · pad: ${state.virtual.join(',')||'—'} · focus: ${document.activeElement===canvas?'canvas':document.activeElement?.tagName} · frame ${diagnostics.frames}\n${note}`;
    if(waypoint){const distance=Math.hypot(camera.position.x-waypoint.x,camera.position.z-waypoint.z);$('mapLabel').textContent=`Destination ${distance.toFixed(1)} m · click to change`;if(distance<.7){waypoint=null;toast('Destination reached');}}
    paintMap();
  }
  diagnostics.snapshot=()=>({ready:diagnostics.ready,started,buildId:build.buildId,planHash:build.planHash,runtimeHash:build.runtimeHash,version:build.version,actualPort:location.port,position:{x:camera.position.x,y:camera.position.y,z:camera.position.z},yaw,pitch,input:input.snapshot(),frames:diagnostics.frames,renderCount:diagnostics.renderCount,simulationTicks:diagnostics.simulationTicks,meshCount:sceneMeshCount,interactableCount:interactables.length,importedModels:imported.models,importedMeshes:imported.meshes,nearest:nearest?.label||null,nearestId:nearest?.id||null,gameplay:gameplay.snapshot(),errors:[...diagnostics.errors]});
  // Explicit test mode is only for local automated navigation/interaction smoke checks.
  if(new URLSearchParams(location.search).get('test')==='1')diagnostics.test={setPosition(x,z){if(!navigation.canMove(x,z))throw new Error('Test position is not walkable');camera.position.set(x,eyeHeight,z);},setYaw(value){if(!Number.isFinite(value))throw new Error('Test yaw must be finite');yaw=value;},canMove:navigation.canMove};
  addEventListener('resize',()=>resizePending=true);
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();input.reset('WebGL context lost');fatal(new Error('Graphics context was lost. Reload this build; try Balanced quality and close other GPU-heavy tabs.'));});
  updateHUD();
  function frame(time) {
    if(diagnostics.errors.length)return;
    try {
      const dt=Math.min(lastTime?(time-lastTime)/1000:0,.04);lastTime=time;
      if(resizePending){resizePending=false;camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
      if(qualityPending){qualityPending=false;renderer.setPixelRatio(Math.min(devicePixelRatio,cinematic?1.8:1.35));sun.shadow.mapSize.set(cinematic?2048:1024,cinematic?2048:1024);sun.shadow.map?.dispose();sun.shadow.map=null;renderer.shadowMap.needsUpdate=true;}
      if(started){
        const [dx,dy]=input.consumeLook();yaw-=dx*.0032;pitch-=dy*.0032;
        const turn=1.65*dt;
        yaw+=(Number(input.held('ArrowLeft'))-Number(input.held('ArrowRight')))*turn;
        pitch+=(Number(input.held('ArrowUp'))-Number(input.held('ArrowDown')))*turn*.55;
        pitch=Math.max(-1.28,Math.min(1.28,pitch));
        let f=Number(input.held('KeyW'))-Number(input.held('KeyS')),r=Number(input.held('KeyD'))-Number(input.held('KeyA'));
        if(f||r){const len=Math.hypot(f,r);f/=len;r/=len;const baseSpeed=config.runtime?.speed||3.05;const speed=baseSpeed*(input.held('ShiftLeft')||input.held('ShiftRight')?5.2/3.05:1)*dt;navigation.move(camera.position,(-Math.sin(yaw)*f+Math.cos(yaw)*r)*speed,(-Math.cos(yaw)*f-Math.sin(yaw)*r)*speed);diagnostics.simulationTicks++;}
      }
      camera.rotation.set(pitch,yaw,0);camera.position.y=eyeHeight;
      uiElapsed+=dt;glowElapsed+=dt;
      if(uiElapsed>=.08){uiElapsed=0;updateHUD();}
      if(glowElapsed>=1/30){glowElapsed=0;dynamicGlow.forEach((o,i)=>o.material.emissiveIntensity=2.2+Math.sin(time/1000*1.5+i)*.5);}
      // This is the only render call and RAF owner; input/resize/quality never render.
      renderer.render(scene,camera);renderer.getContext().flush();renderer.shadowMap.needsUpdate=false;
      diagnostics.frames++;diagnostics.renderCount++;
      // Asset preparation is insufficient: Enter becomes available only after
      // the first successful GPU render submission from this single RAF owner.
      if(!diagnostics.ready){diagnostics.firstFrameAt=performance.now();diagnostics.ready=true;$('enter').disabled=false;$('enter').textContent='ENTER WALK TOUR';}
      requestAnimationFrame(frame);
    }catch(error){fatal(error);}
  }
  requestAnimationFrame(frame);
}
boot().catch(fatal);
