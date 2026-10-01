import * as THREE from 'three';

// -----------------------------------------------------------------------------
// PEARL OFFICE — SAFARI WASD HARDENED V7
// Topology basis: finalized v1.5 planning image + approved corrections.
// Three.js world: X = left/right, Y = up, Z = plan vertical (top is negative Z).
// -----------------------------------------------------------------------------

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x09131b);
scene.fog = new THREE.FogExp2(0x09131b, 0.018);

const camera = new THREE.PerspectiveCamera(66, innerWidth / innerHeight, 0.05, 120);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.35));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.22;
document.body.appendChild(renderer.domElement);
// Keep the WebGL canvas on its own compositor layer. This does not change resolution.
renderer.domElement.style.willChange = 'transform';
renderer.domElement.style.transform = 'translateZ(0)';

const start = document.getElementById('start');
const enterButton = document.getElementById('enter');
let started = false;
let dragging = false;
let lastPointerX = 0, lastPointerY = 0;
let pendingLookX = 0, pendingLookY = 0;
let yaw = -0.95, pitch = 0;
const LOOK_SENSITIVITY = 0.0032;
let lastInputNote = 'waiting for input';
let lastKeyEventAt = 0;
let lastKeyRaw = 'none';
let simTickCount = 0;
camera.rotation.order = 'YXZ';

function applyLook(){
  pitch = Math.max(-1.28, Math.min(1.28, pitch));
  camera.rotation.set(pitch, yaw, 0);
}
function startPlayer(){
  started = true;
  start.style.display = 'none';
  try { renderer.domElement.focus({preventScroll:true}); } catch(_) { renderer.domElement.focus(); }
  lastInputNote = 'player started / canvas focused';
  showToast('V7 active — WASD move, click-drag look.');
}
enterButton.onclick = startPlayer;
renderer.domElement.style.cursor = 'grab';
renderer.domElement.style.touchAction = 'none';
renderer.domElement.addEventListener('pointerdown', e => {
  if(!started) return;
  try { renderer.domElement.focus({preventScroll:true}); } catch(_) { renderer.domElement.focus(); }
  try { renderer.domElement.setPointerCapture(e.pointerId); } catch(_) {}
  dragging = true;
  lastPointerX = e.clientX; lastPointerY = e.clientY;
  renderer.domElement.style.cursor = 'grabbing';
  lastInputNote = 'pointer down / canvas focused';
});
renderer.domElement.addEventListener('pointermove', e => {
  if(!started || !dragging) return;
  const dx = e.clientX-lastPointerX, dy = e.clientY-lastPointerY;
  lastPointerX=e.clientX; lastPointerY=e.clientY;
  // Buffer input only. Camera orientation is consumed in the SAME animation tick
  // as WASD movement and rendering, so view + movement can never be one frame apart.
  pendingLookX += dx; pendingLookY += dy;
});
function endDrag(e){
  dragging=false;
  renderer.domElement.style.cursor='grab';
}
renderer.domElement.addEventListener('pointerup',endDrag);
renderer.domElement.addEventListener('pointercancel',endDrag);
renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());

const zoneEl = document.getElementById('zone');
const objectiveEl = document.getElementById('objective');
const toastEl = document.getElementById('toast');
const interactionEl = document.getElementById('interaction');
const mapWrap = document.getElementById('mapWrap');
const playerDot = document.getElementById('playerDot');

const PLAYER_HEIGHT = 1.68;
const PLAYER_RADIUS = 0.22;
const ENTRY_CENTER = new THREE.Vector2(-10.25, 1.15);
const SPAWN = new THREE.Vector3(-11.75, PLAYER_HEIGHT, 2.35);
const SPAWN_YAW = -0.95;

// ---------- Materials ---------------------------------------------------------
function std(color, rough = 0.55, metal = 0.0, extra = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
}
function emissive(color, intensity = 2.0, base = 0x101010) {
  return new THREE.MeshStandardMaterial({ color: base, roughness: 0.30, metalness: 0.15, emissive: color, emissiveIntensity: intensity });
}
const M = {
  shell: std(0x273039, .48, .25),
  shellDark: std(0x111923, .38, .42),
  floor: std(0xc8c2b5, .74, .03),
  corridor: std(0xe6ddcc, .62, .02),
  officeFloor: std(0xd7d1c4, .68, .02),
  wood: std(0x8b5b36, .48, .03),
  woodDark: std(0x4c2c1b, .44, .04),
  white: std(0xeceae3, .43, .02),
  black: std(0x151a1f, .34, .35),
  navy: std(0x1f4564, .44, .05),
  blueLeather: std(0x1e5c82, .39, .02),
  orangeLeather: std(0xb55c27, .41, .02),
  gold: std(0xb68a36, .30, .65),
  tea: std(0x70462b, .48, .03),
  green: std(0x3f7744, .72, .00),
  screen: emissive(0x4ed8ff, 3.0, 0x0b1720),
  warmScreen: emissive(0xffb154, 2.3, 0x25140a),
  redGlow: emissive(0xff5b43, 2.5, 0x2b0805),
};
const glassMat = new THREE.MeshPhysicalMaterial({
  color: 0x99e2ef, roughness: 0.14, metalness: 0.04,
  transparent: true, opacity: 0.28, transmission: 0.55, thickness: 0.08,
  clearcoat: 1.0, clearcoatRoughness: 0.12, side: THREE.DoubleSide
});

// ---------- Scene utilities ---------------------------------------------------
const colliders = [];
const interactables = [];
const zoneVolumes = [];
const dynamicGlow = [];

function addCollider(obj, sx, sz, rotY = 0, padding = 0.0) {
  colliders.push({ obj, hx: sx / 2 + padding, hz: sz / 2 + padding, rotY });
}
function box(name, sx, sy, sz, x, y, z, material, rotY = 0, collide = false, padding = 0.0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), material);
  mesh.name = name;
  mesh.position.set(x, y, z);
  mesh.rotation.y = rotY;
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  if (collide) addCollider(mesh, sx, sz, rotY, padding);
  return mesh;
}
function cyl(name, r, h, x, y, z, material, segments = 32, collide = false) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, segments), material);
  mesh.name = name;
  mesh.position.set(x, y, z);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  if (collide) addCollider(mesh, r * 2, r * 2, 0, .05);
  return mesh;
}
function wallSegment(name, ax, az, bx, bz, height = 3.25, thickness = .24, material = M.shell) {
  const dx = bx - ax, dz = bz - az;
  const len = Math.hypot(dx, dz);
  const angle = Math.atan2(dz, dx);
  return box(name, len, height, thickness, (ax + bx) / 2, height / 2, (az + bz) / 2, material, -angle, true, .02);
}
function floorRect(name, w, d, x, z, material, rotY = 0, y = 0.015) {
  return box(name, w, .03, d, x, y, z, material, rotY, false);
}
function labelSprite(text, x, y, z, accent = '#ffffff', scale = 2.2) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(7,14,20,.82)';
  ctx.roundRect(8, 8, 496, 112, 20); ctx.fill();
  ctx.strokeStyle = accent; ctx.lineWidth = 3; ctx.stroke();
  ctx.fillStyle = '#fff'; ctx.font = '700 34px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(text, 256, 64);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
  const s = new THREE.Sprite(mat); s.position.set(x, y, z); s.scale.set(scale * 2.5, scale * .625, 1); scene.add(s); return s;
}
function plant(x, z, s = 1) {
  cyl('PlantPot', .24*s, .36*s, x, .18*s, z, std(0xeee5d7,.6,.02), 20, true);
  const stem = cyl('PlantStem', .035*s, .72*s, x, .66*s, z, M.green, 10, false);
  for (let i=0;i<8;i++) {
    const a=i/8*Math.PI*2;
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(.22*s,12,8), M.green);
    leaf.scale.set(.65,1.7,.45); leaf.position.set(x+Math.cos(a)*.18*s, .82*s+(i%2)*.12*s, z+Math.sin(a)*.18*s); leaf.rotation.z=a*.25; scene.add(leaf);
  }
  return stem;
}
function chair(x,z,rot=0,colorMat=M.black) {
  box('ChairSeat', .55,.12,.55,x,.48,z,colorMat,rot,true);
  box('ChairBack', .55,.72,.10,x+Math.sin(rot)*.23,.83,z+Math.cos(rot)*.23,colorMat,rot,true);
  cyl('ChairStem', .06,.38,x,.25,z,M.black,12,false);
}
function desk(x,z,w=2.2,d=.8,rot=0,material=M.wood) {
  box('DeskTop',w,.10,d,x,.78,z,material,rot,true);
  const sin=Math.sin(rot), cos=Math.cos(rot);
  for(const sx of [-1,1]) for(const sz of [-1,1]) {
    const lx=sx*(w/2-.14), lz=sz*(d/2-.13);
    const wx=x+lx*cos+lz*sin, wz=z-lx*sin+lz*cos;
    box('DeskLeg',.09,.72,.09,wx,.38,wz,M.black,rot,false);
  }
}
function monitor(x,z,rot=0,wide=.54) {
  const screen = box('Monitor',wide,.34,.045,x,1.13,z,M.screen,rot,false);
  box('MonitorStem',.05,.22,.05,x,.94,z,M.black,rot,false);
  return screen;
}
function sofa(x,z,w=2.1,rot=0,material=M.blueLeather) {
  box('SofaSeat',w,.32,.78,x,.38,z,material,rot,true);
  const dx=Math.sin(rot)*.32, dz=Math.cos(rot)*.32;
  box('SofaBack',w,.78,.20,x+dx,.82,z+dz,material,rot,true);
  const sideOffset=w/2-.12;
  const cos=Math.cos(rot), sin=Math.sin(rot);
  for(const s of [-1,1]) {
    const wx=x+s*sideOffset*cos, wz=z-s*sideOffset*sin;
    box('SofaArm',.24,.46,.82,wx,.54,wz,material,rot,true);
  }
}
function roundTable(x,z,r=.55,mat=M.wood) {
  cyl('RoundTable',r,.10,x,.68,z,mat,40,true); cyl('RoundTableStem',.08,.65,x,.34,z,M.black,14,false);
}
function shelf(x,z,w=2.6,h=2.2,rot=0,mat=M.woodDark) {
  box('ShelfBack',w,h,.18,x,h/2,z,mat,rot,true);
  for(let i=0;i<4;i++) box('ShelfBoard',w,.07,.45,x,.38+i*.5,z-.08, M.wood,rot,false);
}
function displayPedestal(x,z,label,type='award') {
  const p=box('DisplayPedestal',.55,.78,.55,x,.39,z,M.white,0,true);
  const artifact = type==='award' ? cyl('Award',.13,.38,x,.98,z,M.gold,10,false) : box('CharityArtifact',.25,.34,.18,x,.98,z,M.warmScreen,0,false);
  interactables.push({obj:artifact,label,type});
  return p;
}
function addPoint(x,y,z,color,intensity=35,dist=8){const l=new THREE.PointLight(color,intensity,dist,2);l.position.set(x,y,z);l.castShadow=false;scene.add(l);return l;}

// ---------- Pearl-shaped floor + outer shell ---------------------------------
const outer2 = [
  new THREE.Vector2(-14.6, 7.8), new THREE.Vector2(-16.0, 6.2),
  new THREE.Vector2(-14.2, 2.0), new THREE.Vector2(-8.2,-4.8),
  new THREE.Vector2(-1.6,-9.6), new THREE.Vector2(0,-10.55),
  new THREE.Vector2(1.6,-9.6), new THREE.Vector2(8.2,-4.8),
  new THREE.Vector2(14.2,2.0), new THREE.Vector2(16.0,6.2),
  new THREE.Vector2(14.6,7.8), new THREE.Vector2(-14.6,7.8)
];
const floorShape = new THREE.Shape();
floorShape.moveTo(-14.6,7.8);
floorShape.quadraticCurveTo(-16.2,7.2,-16.0,6.2);
floorShape.quadraticCurveTo(-14.9,3.0,-14.2,2.0);
floorShape.lineTo(-8.2,-4.8); floorShape.lineTo(-1.6,-9.6);
floorShape.quadraticCurveTo(0,-10.9,1.6,-9.6);
floorShape.lineTo(8.2,-4.8); floorShape.lineTo(14.2,2.0);
floorShape.quadraticCurveTo(16.2,7.2,14.6,7.8); floorShape.closePath();
const floor = new THREE.Mesh(new THREE.ShapeGeometry(floorShape, 24), M.floor);
floor.rotation.x = -Math.PI/2; floor.position.y = -0.006; floor.receiveShadow = true; scene.add(floor);

// Entry apron, aligned near the left-side entry gap.
const entryAngle = -0.72;
floorRect('EntryApron',3.2,2.5,-10.95,1.92,M.floor,entryAngle,-.005);

// Outer wall segments; explicit gap between Awards and Charity.
const shellPts = [
  [-14.6,7.8],[-16.0,6.2],[-14.2,2.0],[-8.2,-4.8],[-1.6,-9.6],[0,-10.55],[1.6,-9.6],[8.2,-4.8],[14.2,2.0],[16.0,6.2],[14.6,7.8]
];
// left lower and upper sections with entry gap from roughly (-11.05,1.95) to (-9.75,.55)
wallSegment('Outer_BottomLeft',-14.6,7.8,-16.0,6.2);
wallSegment('Outer_LeftLower',-16.0,6.2,-11.25,1.93);
wallSegment('Outer_LeftUpperA',-9.65,.45,-8.2,-4.8);
wallSegment('Outer_LeftUpperB',-8.2,-4.8,-1.6,-9.6);
wallSegment('Outer_TopL',-1.6,-9.6,0,-10.55);
wallSegment('Outer_TopR',0,-10.55,1.6,-9.6);
wallSegment('Outer_RightUpper',1.6,-9.6,8.2,-4.8);
wallSegment('Outer_RightMid',8.2,-4.8,14.2,2.0);
wallSegment('Outer_RightLowerA',14.2,2.0,16.0,6.2);
wallSegment('Outer_BottomRight',16.0,6.2,14.6,7.8);
wallSegment('Outer_Bottom',14.6,7.8,-14.6,7.8);

// Entry light pylons visually mark the actual external entry.
for(const [x,z] of [[-11.15,1.72],[-9.78,.42]]) { box('EntryPylon',.28,2.65,.28,x,1.33,z,M.shellDark,entryAngle,true); box('EntryGlow',.10,1.8,.08,x,1.48,z,M.screen,entryAngle,false); }
labelSprite('ENTRY / EXIT',-11.2,2.7,1.45,'#67dfff',1.55);

// ---------- Central Pearl Office ---------------------------------------------
const pearlCx=0, pearlCz=-.25, pearlRx=7.25, pearlRz=4.15;
const pearlFloor = new THREE.Mesh(new THREE.CircleGeometry(1,96), M.officeFloor);
pearlFloor.scale.set(pearlRx,pearlRz,1); pearlFloor.rotation.x=-Math.PI/2; pearlFloor.position.set(pearlCx,.018,pearlCz); pearlFloor.receiveShadow=true; scene.add(pearlFloor);

// Glass ellipse, with the only entry gap on lower-right at Wine / Manager 1 junction.
const panelCount=44;
for(let i=0;i<panelCount;i++){
  const a0=i/panelCount*Math.PI*2, a1=(i+1)/panelCount*Math.PI*2, ac=(a0+a1)/2;
  // gap around lower-right: angle ~0.65 radians (positive X, positive Z)
  if(ac>0.42 && ac<0.91) continue;
  const x0=pearlCx+pearlRx*Math.cos(a0), z0=pearlCz+pearlRz*Math.sin(a0);
  const x1=pearlCx+pearlRx*Math.cos(a1), z1=pearlCz+pearlRz*Math.sin(a1);
  const dx=x1-x0,dz=z1-z0,len=Math.hypot(dx,dz),ang=Math.atan2(dz,dx);
  const g=box('PearlGlass',len,2.55,.075,(x0+x1)/2,1.275,(z0+z1)/2,glassMat,-ang,true,.01);
  if(i%4===0) box('PearlMullion',.08,2.7,.10,(x0+x1)/2,1.35,(z0+z1)/2,M.shellDark,-ang,true);
}
// Entry markers at pearl opening
box('PearlEntryPostA',.12,2.75,.12,5.72,1.38,2.30,M.shellDark,0,true);
box('PearlEntryPostB',.12,2.75,.12,4.70,1.38,3.15,M.shellDark,0,true);
labelSprite('ONLY ENTRY → PEARL OFFICE',6.2,2.45,2.85,'#ff694f',1.30);

// Pearl Office work islands
for(const [x,z,r] of [[-3.35,-.65,-.40],[3.35,-.65,.40],[0,2.15,0]]){
  desk(x,z,3.3,.9,r,M.white);
  for(const s of [-1,1]){
    const dx=Math.cos(r)*s*.85, dz=-Math.sin(r)*s*.85;
    monitor(x+dx,z+dz,r,.48);
    chair(x+dx,z+dz+.62*Math.cos(r),r,M.black);
  }
}
// Shared console near top of central office
const pearlConsole = desk(0,-2.65,1.9,.75,0,M.white); monitor(0,-2.63,0,.72);
interactables.push({obj:pearlConsole,label:'Pearl Office shared console',type:'pearl'});
for(const p of [[-5.5,-2.6],[-5.7,1.1],[-4.8,2.4],[4.9,-2.8],[5.6,.7],[4.5,2.5],[-1.8,3.1],[1.8,3.1]]) plant(...p,.82);

// ---------- Room construction helpers ----------------------------------------
function roomPad(name,x,z,w,d,rot,colorMat, label, opts={}){
  floorRect(name+'Floor',w,d,x,z,colorMat,rot,.025);
  if(label) labelSprite(label,x,2.55,z,'#e8f6ff',1.18);
  zoneVolumes.push({name:label||name,x,z,w,d,rot});
  // four perimeter walls with one inner-facing door gap if enclosed
  if(opts.open) return;
  const h=2.8,t=.15,door=opts.door||1.25;
  const side=opts.doorSide||'south';
  const addLocalWall=(lname,cx,cz,sx,sz)=>{
    const c=Math.cos(rot),s=Math.sin(rot); const wx=x+cx*c+cz*s,wz=z-cx*s+cz*c;
    box(name+lname,sx,h,sz,wx,h/2,wz,M.shell,rot,true);
  };
  if(side==='south'){
    addLocalWall('N',0,-d/2,w,t);
    addLocalWall('W',-w/2,0,t,d);
    addLocalWall('E',w/2,0,t,d);
    const seg=(w-door)/2; addLocalWall('S1',-(door+seg)/2,d/2,seg,t); addLocalWall('S2',(door+seg)/2,d/2,seg,t);
  }else if(side==='north'){
    addLocalWall('S',0,d/2,w,t);addLocalWall('W',-w/2,0,t,d);addLocalWall('E',w/2,0,t,d);
    const seg=(w-door)/2;addLocalWall('N1',-(door+seg)/2,-d/2,seg,t);addLocalWall('N2',(door+seg)/2,-d/2,seg,t);
  }else if(side==='west'){
    addLocalWall('N',0,-d/2,w,t);addLocalWall('S',0,d/2,w,t);addLocalWall('E',w/2,0,t,d);
    const seg=(d-door)/2;addLocalWall('W1',-w/2,-(door+seg)/2,t,seg);addLocalWall('W2',-w/2,(door+seg)/2,t,seg);
  }else{
    addLocalWall('N',0,-d/2,w,t);addLocalWall('S',0,d/2,w,t);addLocalWall('W',-w/2,0,t,d);
    const seg=(d-door)/2;addLocalWall('E1',w/2,-(door+seg)/2,t,seg);addLocalWall('E2',w/2,(door+seg)/2,t,seg);
  }
}

// 1 Reception — open, facing the external entry, outside Pearl Office.
roomPad('Reception',-7.55,.40,3.7,3.0,-.16,std(0xd8c7a6,.62,.02),'1  RECEPTION',{open:true});
const receptionDesk = box('ReceptionDesk',2.8,.85,.72,-7.25,.43,.55,M.white,-.16,true);
box('ReceptionDeskFront',2.7,.65,.08,-7.14,.48,.91,M.gold,-.16,false);
chair(-6.6,-.32,-.16,M.orangeLeather); roundTable(-5.95,-.22,.38,M.white); plant(-8.8,-.25,.8);
interactables.push({obj:receptionDesk,label:'Reception desk — guest check-in',type:'reception'});

// 10 Tea Room — closed and directly below Reception, outside Pearl Office.
roomPad('TeaRoom',-7.20,4.25,3.6,2.45,0,M.officeFloor,'10  TEA ROOM',{doorSide:'north'});
desk(-7.2,4.35,2.1,.75,0,M.tea); for(const x of [-7.85,-6.55]) chair(x,5.02,Math.PI,M.black);
const teaService=box('TeaService',.82,.10,.38,-7.2,.90,4.34,M.gold,0,false); interactables.push({obj:teaService,label:'Tea service',type:'tea'});

// 13 Awards Section — open-ended gallery above external entry.
roomPad('Awards',-9.55,-2.30,4.0,3.5,-.55,std(0xd2c3a2,.65,.02),'13  AWARDS',{open:true});
shelf(-10.05,-2.95,2.2,1.9,-.55,M.woodDark);
for(const p of [[-9.1,-2.0],[-10.65,-1.6],[-8.8,-3.2]]) displayPedestal(...p,'Awards display','award');
interactables.push({obj:scene.getObjectByName('ShelfBack'),label:'Awards wall',type:'awards'});

// 12 Charity Gallery — open corridor below entry; no enclosing walls.
roomPad('Charity',-12.2,2.85,4.3,3.9,-.48,std(0xd8c9ab,.68,.01),'12  CHARITY GALLERY',{open:true});
for(const p of [[-12.9,1.6],[-13.35,2.7],[-12.5,3.9],[-11.35,3.0]]) displayPedestal(...p,'Charity display','charity');

// 2 Trading Office at top-left.
roomPad('Trading',-4.20,-7.55,5.0,2.8,-.03,std(0xc9d7dc,.64,.03),'2  TRADING OFFICE',{doorSide:'south'});
desk(-4.25,-7.55,3.65,.85,0,M.wood); for(const x of [-5.25,-4.25,-3.25]) {monitor(x,-7.52,0,.48);chair(x,-6.95,Math.PI,M.black);}

// 3 Executive Office, top-right of apex.
roomPad('Executive',2.45,-7.55,4.2,2.9,.04,std(0xd7cfc0,.63,.02),'3  EXECUTIVE OFFICE',{doorSide:'south'});
desk(3.15,-7.35,1.75,.78,.05,M.wood); monitor(3.15,-7.34,.05,.52); sofa(1.50,-7.35,1.65,0,M.orangeLeather);roundTable(2.0,-6.85,.42,M.white);

// 4 Meeting Room — long right-upper space.
roomPad('Meeting',8.00,-4.95,5.5,3.15,-.43,std(0xd7d0c5,.63,.02),'4  MEETING ROOM',{doorSide:'west'});
desk(8.05,-4.92,3.45,1.15,-.43,M.wood); for(let i=-2;i<=2;i++){const u=i*.68;chair(8.05+u*Math.cos(-.43),-4.92-u*Math.sin(-.43)+.90,-.43+Math.PI,M.black);chair(8.05+u*Math.cos(-.43),-4.92-u*Math.sin(-.43)-.90,-.43,M.black);} const meetingScreen=box('MeetingScreen',1.8,1.0,.07,9.95,1.55,-3.82,M.screen,-.43,false);interactables.push({obj:meetingScreen,label:'Meeting Room presentation screen',type:'meeting'});

// 5 Director Office — right-mid.
roomPad('Director',11.30,-.70,3.25,2.85,-.18,std(0xc8d0d5,.64,.02),'5  DIRECTOR OFFICE',{doorSide:'west'});
desk(11.55,-1.2,1.65,.75,-.18,M.wood);monitor(11.55,-1.18,-.18,.45);sofa(11.05,.18,1.65,-.18,M.blueLeather);roundTable(11.55,.25,.38,M.white);

// 6 Wine Room — right-lower pearl corner.
roomPad('Wine',12.30,4.20,4.05,4.35,.30,std(0x5a3522,.45,.02),'6  WINE ROOM',{doorSide:'west'});
sofa(13.25,4.75,2.1,.30,M.orangeLeather);roundTable(12.15,3.85,.58,M.wood);shelf(13.3,3.25,2.2,2.25,.30,M.woodDark); const wineGlow=box('WineFeature',1.7,1.15,.06,13.0,1.65,2.32,M.warmScreen,.30,false);interactables.push({obj:wineGlow,label:'Wine display',type:'wine'});

// 7,8,9 Manager Offices along lower edge.
for(const [id,x] of [[7,8.65],[8,3.70],[9,-1.00]]){
  roomPad('Manager'+id,x,6.62,3.6,2.15,0,std(0xcbd6dc,.67,.02),`${id}  MANAGER OFFICE ${id-6}`,{doorSide:'north'});
  desk(x,6.70,1.6,.70,0,M.wood);monitor(x,6.68,0,.46);chair(x,7.20,Math.PI,M.black);
}

// 11 Back Office — bottom-left corner, directly connected to Charity side.
roomPad('BackOffice',-12.50,6.15,5.0,3.1,-.18,std(0xc7d0d2,.68,.02),'11  BACK OFFICE',{doorSide:'north'});
desk(-12.5,6.2,2.6,.85,-.18,M.white);monitor(-13.05,6.18,-.18,.44);monitor(-11.95,6.18,-.18,.44);chair(-13.0,6.85,Math.PI-.18,M.black);chair(-12.0,6.85,Math.PI-.18,M.black);

// ---------- Architectural rhythm, corridor lamps, and wayfinding ------------
for(let i=0;i<20;i++){
  const a=i/20*Math.PI*2; const rx=8.5, rz=5.1;
  const x=rx*Math.cos(a), z=-.25+rz*Math.sin(a);
  if(x<-7.0 && z>-1 && z<5.5) continue; // keep left reception/tea zone readable
  cyl('CorridorLight',.045,.06,x,.06,z,M.screen,10,false);
}

scene.add(new THREE.HemisphereLight(0xd7edff,0x5d4330,1.25));
const sun=new THREE.DirectionalLight(0xfff0d5,2.6);sun.position.set(-5,10,-7);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);scene.add(sun);
addPoint(-8,2.6,-1.5,0xffd99a,42,9);addPoint(8,2.8,-4.0,0xb8dcff,32,8);addPoint(11,2.5,3.5,0xffa34f,38,8);addPoint(0,3.2,-.2,0x9ee8ff,36,10);addPoint(-12,2.4,4.5,0xffd7a6,28,7);

// Static scene: render the shadow atlas once, then reuse it while the player moves.
// Visual quality is unchanged; this removes a large per-frame GPU cost.
renderer.shadowMap.autoUpdate = false;
renderer.shadowMap.needsUpdate = true;

// ---------- Interactions / gameplay ------------------------------------------
const keys=Object.create(null); let mapVisible=true; let stage=0; let nearestInteractive=null; let cinematic=false;
const statusEl=document.getElementById('status');
renderer.domElement.tabIndex=0;

// Safari-hardened keyboard normalization. We accept code, key, and legacy keyCode/which.
const LEGACY_KEYCODE = {87:'KeyW',65:'KeyA',83:'KeyS',68:'KeyD',16:'ShiftLeft',37:'ArrowLeft',38:'ArrowUp',39:'ArrowRight',40:'ArrowDown',69:'KeyE',77:'KeyM',82:'KeyR',81:'KeyQ'};
function normalizedCode(e){
  const allowed = new Set(['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','KeyE','KeyM','KeyR','KeyQ']);
  if(e.code && allowed.has(e.code)) return e.code;
  const k=(e.key||'').toLowerCase();
  if(k==='w') return 'KeyW'; if(k==='a') return 'KeyA'; if(k==='s') return 'KeyS'; if(k==='d') return 'KeyD';
  if(k==='shift') return e.location===2?'ShiftRight':'ShiftLeft';
  if(k==='arrowleft') return 'ArrowLeft'; if(k==='arrowright') return 'ArrowRight';
  if(k==='arrowup') return 'ArrowUp'; if(k==='arrowdown') return 'ArrowDown';
  if(k==='e') return 'KeyE'; if(k==='m') return 'KeyM'; if(k==='r') return 'KeyR'; if(k==='q') return 'KeyQ';
  return LEGACY_KEYCODE[e.which||e.keyCode||0] || '';
}
function shouldIgnoreKeyboardTarget(t){
  if(!t) return false;
  const tag=(t.tagName||'').toLowerCase();
  return tag==='input'||tag==='textarea'||tag==='select'||t.isContentEditable;
}
function movementKey(c){return ['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(c);}
function setKeyState(e,down){
  if(shouldIgnoreKeyboardTarget(e.target)) return;
  const c=normalizedCode(e); if(!c) return;
  keys[c]=down;
  lastKeyEventAt=performance.now();
  lastKeyRaw=`${down?'down':'up'} key=${e.key||'?'} code=${e.code||'?'} legacy=${e.which||e.keyCode||0} -> ${c}`;
  lastInputNote=lastKeyRaw;
  if(movementKey(c) || ['KeyE','KeyM','KeyR','KeyQ'].includes(c)) e.preventDefault();
  if(down && !e.repeat){
    if(c==='KeyE') interact();
    if(c==='KeyM'){mapVisible=!mapVisible;mapWrap.classList.toggle('hidden',!mapVisible);}
    if(c==='KeyR') resetPlayer();
    if(c==='KeyQ') toggleCinematic();
  }
}

// Use a WeakSet because the same physical event traverses window/document/canvas.
const seenKeyEvents=new WeakSet();
function onKeyDown(e){ if(seenKeyEvents.has(e)) return; seenKeyEvents.add(e); setKeyState(e,true); }
function onKeyUp(e){ if(seenKeyEvents.has(e)) return; seenKeyEvents.add(e); setKeyState(e,false); }
window.addEventListener('keydown',onKeyDown,true);
window.addEventListener('keyup',onKeyUp,true);
document.addEventListener('keydown',onKeyDown,true);
document.addEventListener('keyup',onKeyUp,true);
renderer.domElement.addEventListener('keydown',onKeyDown,true);
renderer.domElement.addEventListener('keyup',onKeyUp,true);

// Clicking anywhere on the renderer always returns keyboard focus to the game.
renderer.domElement.addEventListener('click',()=>{
  if(started){ try{renderer.domElement.focus({preventScroll:true});}catch(_){renderer.domElement.focus();} }
});
window.addEventListener('blur',()=>{ for(const k of Object.keys(keys)) keys[k]=false; dragging=false; lastInputNote='window blur — keys cleared'; });
document.addEventListener('visibilitychange',()=>{ if(document.hidden){for(const k of Object.keys(keys)) keys[k]=false; lastInputNote='document hidden — keys cleared';} });
window.addEventListener('pagehide',()=>{for(const k of Object.keys(keys)) keys[k]=false;});

// On-screen D-pad is a diagnostic + emergency fallback. It uses the SAME movement state
// as physical WASD, so if these buttons move the player but keyboard does not, the only
// remaining fault is Safari key delivery/focus rather than navmesh or rendering.
for(const btn of document.querySelectorAll('[data-move]')){
  const c=btn.dataset.move;
  const down=(e)=>{e.preventDefault();keys[c]=true;lastInputNote='virtual '+c+' down';try{renderer.domElement.focus({preventScroll:true});}catch(_){}};
  const up=(e)=>{e.preventDefault();keys[c]=false;lastInputNote='virtual '+c+' up';};
  btn.addEventListener('pointerdown',down);
  btn.addEventListener('pointerup',up);
  btn.addEventListener('pointercancel',up);
  btn.addEventListener('pointerleave',e=>{if(e.buttons===0)up(e);});
}

function showToast(text,ms=2100){toastEl.textContent=text;toastEl.style.opacity=1;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toastEl.style.opacity=0,ms);}
function setObjective(text){objectiveEl.textContent='Objective: '+text;}
function advance(type){
  if(stage===0 && type==='reception'){stage=1;setObjective('follow the clockwise loop toward the Wine Room');showToast('Checked in. Follow the blue circulation loop clockwise.');}
  else if(stage===1 && type==='wine'){stage=2;setObjective('find the single opening into the Pearl Office');showToast('Wine Room reached. The Pearl Office opening is beside this corner.');}
  else if(stage===2 && type==='pearl'){stage=3;setObjective('explore freely — planning-to-game loop complete');showToast('Pearl Office console online. You have completed the first tour loop.',3200);}
}
function interact(){
  if(!nearestInteractive){showToast('Move closer to an interactive object.');return;}
  const it=nearestInteractive;
  if(it.type==='reception') showToast('Reception: guest check-in complete.');
  if(it.type==='awards') showToast('Awards Section: photo-derived display wall and trophy zone.');
  if(it.type==='charity') showToast('Charity Gallery: open-ended display corridor — no room enclosure.');
  if(it.type==='tea') showToast('Tea Room: enclosed hospitality room beside Reception.');
  if(it.type==='meeting'){it.obj.material.emissiveIntensity=it.obj.material.emissiveIntensity>4?3:6;showToast('Meeting Room screen toggled.');}
  if(it.type==='wine'){it.obj.material.emissiveIntensity=it.obj.material.emissiveIntensity>4?2.3:5.5;showToast('Wine display lighting toggled.');}
  if(it.type==='pearl'){showToast('Pearl Office shared console: central workspace synchronized.');}
  advance(it.type);
}

function toggleCinematic(){
  cinematic=!cinematic;
  renderer.setPixelRatio(Math.min(devicePixelRatio, cinematic?1.8:1.35));
  sun.shadow.mapSize.set(cinematic?2048:1024,cinematic?2048:1024);
  sun.shadow.map?.dispose?.(); sun.shadow.map=null; renderer.shadowMap.needsUpdate=true;
  showToast(cinematic?'Cinematic quality enabled.':'Balanced detail mode enabled.');
  renderNow();
}
function resetPlayer(){camera.position.copy(SPAWN);yaw=SPAWN_YAW;pitch=0;pendingLookX=pendingLookY=0;applyLook();stage=0;setObjective('enter between Awards and Charity');showToast('Player reset to entry.');renderNow();}
resetPlayer();

function pointInPolygon(x,z,pts){let inside=false;for(let i=0,j=pts.length-1;i<pts.length;j=i++) {const xi=pts[i].x,zi=pts[i].y,xj=pts[j].x,zj=pts[j].y;const intersect=((zi>z)!==(zj>z))&&(x<(xj-xi)*(z-zi)/(zj-zi+1e-9)+xi);if(intersect)inside=!inside;}return inside;}
function inEntryApron(x,z){
  // local rectangle around the external left-side door
  const cx=-10.92,cz=1.93,a=entryAngle,c=Math.cos(a),s=Math.sin(a),dx=x-cx,dz=z-cz,lx=dx*c-dz*s,lz=dx*s+dz*c;
  return Math.abs(lx)<1.7 && Math.abs(lz)<1.8;
}
// -----------------------------------------------------------------------------
// V7 FAIL-SAFE CONNECTED NAVIGATION
// The visual model remains the main repo. Navigation is now a separate continuous
// walkable surface: outer circulation ring + rooms + Pearl interior + entry apron.
// This prevents decorative/partition geometry from silently sealing the route.
// -----------------------------------------------------------------------------
function inRotRect(x,z,v,margin=.0){
  const dx=x-v.x,dz=z-v.z,c=Math.cos(v.rot||0),si=Math.sin(v.rot||0);
  const lx=dx*c-dz*si,lz=dx*si+dz*c;
  return Math.abs(lx)<v.w/2+margin && Math.abs(lz)<v.d/2+margin;
}
function pearlQ(x,z,rx=pearlRx,rz=pearlRz){ return ((x-pearlCx)/rx)**2 + ((z-pearlCz)/rz)**2; }
function inPearlPortal(x,z){
  // generous portal around the one approved opening at Wine / Manager 1 junction
  return Math.hypot(x-5.22,z-2.72) < 1.45;
}
function inMainCorridor(x,z){
  // continuous elliptical circulation band surrounding the Pearl Office
  const inner=((x)/7.45)**2 + ((z+.25)/4.35)**2;
  const outer=((x)/11.65)**2 + ((z+.25)/7.35)**2;
  return inner>0.92 && outer<1.12 && pointInPolygon(x,z,outer2);
}
function inAnyRoom(x,z){
  for(const v of zoneVolumes) if(inRotRect(x,z,v,.10)) return true;
  return false;
}
function canMove(x,z){
  // V7 fail-safe navigation: the entire physical office shell is one connected walkable
  // surface. We only block the outer envelope and the Pearl glass ring (except portal).
  // This deliberately removes room-by-room nav islands as a possible source of dead zones.
  if(inEntryApron(x,z)) return true;
  if(!pointInPolygon(x,z,outer2)) return false;
  const q=pearlQ(x,z);
  if(q>=0.86 && q<=1.05 && !inPearlPortal(x,z)) return false;
  return true;
}

// Sub-step + axis sliding. This is intentionally independent of the detailed
// furniture/room meshes so visual density cannot freeze player locomotion.
function movePlayer(dx,dz){
  simTickCount++;
  const dist=Math.hypot(dx,dz);
  const steps=Math.max(1,Math.ceil(dist/0.035));
  const sx=dx/steps, sz=dz/steps;
  for(let i=0;i<steps;i++){
    const x0=camera.position.x, z0=camera.position.z;
    const nx=x0+sx, nz=z0+sz;
    if(canMove(nx,nz)){camera.position.x=nx;camera.position.z=nz;continue;}
    if(canMove(nx,z0)) camera.position.x=nx;
    if(canMove(camera.position.x,nz)) camera.position.z=nz;
  }
  camera.position.y=PLAYER_HEIGHT;
}

function zoneName(x,z){
  // Pearl interior first, excluding separate left Reception/Tea placement.
  const q=((x-pearlCx)/pearlRx)**2+((z-pearlCz)/pearlRz)**2;
  if(q<.92 && !(x<-5.2 && z>-1.2)) return 'Pearl Office';
  for(const v of zoneVolumes){const dx=x-v.x,dz=z-v.z,c=Math.cos(v.rot),s=Math.sin(v.rot),lx=dx*c-dz*s,lz=dx*s+dz*c;if(Math.abs(lx)<v.w/2&&Math.abs(lz)<v.d/2)return v.name.replace(/^\d+\s+/,'');}
  if(inEntryApron(x,z)) return 'Entry / Exterior';
  return 'Clockwise Circulation';
}
function updateNearest(){
  let best=null,bd=2.15;
  const cp=camera.position;
  for(const it of interactables){
    // All interactable meshes are static direct children of the scene, so local = world position.
    const d=Math.hypot(cp.x-it.obj.position.x,cp.z-it.obj.position.z);
    if(d<bd){bd=d;best=it;}
  }
  if(best!==nearestInteractive){
    nearestInteractive=best;
    interactionEl.classList.toggle('visible',!!best);
    if(best) interactionEl.textContent='Press E — '+best.label;
  }
}
function updateMap(){
  // map world [-16,16]x[-10.8,8.5] into cropped reference-image percentages.
  const x=camera.position.x,z=camera.position.z;
  const px=14 + ((x+16)/32)*72; const py=13 + ((z+10.8)/19.3)*70;
  playerDot.style.left=px+'%';playerDot.style.top=py+'%';
}

const clock=new THREE.Clock();
let uiAccumulator=0, glowAccumulator=0, lastZone='';
function renderNow(){
  renderer.render(scene,camera);
  // Explicitly submit commands to the browser compositor. Useful on macOS/Chrome
  // where a complex WebGL scene can otherwise appear to update only after UI events.
  renderer.getContext().flush();
}
function animate(){
  requestAnimationFrame(animate);
  const dt=Math.min(clock.getDelta(),.04);
  const t=performance.now()/1000;
  if(started){
    // Consume mouse input in the render loop, before movement, so look/WASD/presentation are synchronized.
    if(pendingLookX || pendingLookY){
      yaw -= pendingLookX*LOOK_SENSITIVITY;
      pitch -= pendingLookY*LOOK_SENSITIVITY;
      pendingLookX=0; pendingLookY=0;
      applyLook();
    }
    const turnSpeed=1.65*dt;
    if(keys.ArrowLeft) yaw += turnSpeed;
    if(keys.ArrowRight) yaw -= turnSpeed;
    if(keys.ArrowUp) pitch += turnSpeed*.55;
    if(keys.ArrowDown) pitch -= turnSpeed*.55;
    if(keys.ArrowLeft||keys.ArrowRight||keys.ArrowUp||keys.ArrowDown) applyLook();

    const speed=((keys.ShiftLeft||keys.ShiftRight)?5.2:3.05)*dt;
    let f=(keys.KeyW?1:0)-(keys.KeyS?1:0), r=(keys.KeyD?1:0)-(keys.KeyA?1:0);
    if(f||r){
      const len=Math.hypot(f,r)||1; f/=len; r/=len;
      const fx=-Math.sin(yaw), fz=-Math.cos(yaw);
      const rx=Math.cos(yaw), rz=-Math.sin(yaw);
      movePlayer((fx*f + rx*r)*speed,(fz*f + rz*r)*speed);
    }

    // HUD / minimap / proximity checks do not need 60–120 updates per second.
    // 12.5 Hz feels instant to a player while avoiding DOM/layout work in the render path.
    uiAccumulator += dt;
    if(uiAccumulator >= 0.08){
      uiAccumulator=0;
      const zn=zoneName(camera.position.x,camera.position.z);
      if(zn!==lastZone){ zoneEl.textContent='Current zone: '+zn; lastZone=zn; }
      if(stage===0 && pointInPolygon(camera.position.x,camera.position.z,outer2) && !inEntryApron(camera.position.x,camera.position.z)) setObjective('check in at Reception (press E)');
      const active=[keys.KeyW&&'W',keys.KeyA&&'A',keys.KeyS&&'S',keys.KeyD&&'D'].filter(Boolean).join('');
      statusEl.textContent=`Safari V7 · ${active?'HELD '+active:'WASD ready'} · x ${camera.position.x.toFixed(2)} / z ${camera.position.z.toFixed(2)} · focus=${document.activeElement===renderer.domElement?'canvas':(document.activeElement?.tagName||'none')} · ${lastInputNote}`;
      updateNearest(); updateMap();
    }
  }

  // Keep the subtle glow animation, but 30 Hz is visually indistinguishable here.
  glowAccumulator += dt;
  if(glowAccumulator >= 1/30){
    glowAccumulator=0;
    dynamicGlow.forEach((o,i)=>o.material.emissiveIntensity=2.2+Math.sin(t*1.5+i)*.5);
  }
  renderNow();
  renderer.shadowMap.needsUpdate=false;
}
animate();

addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);renderNow();});
