// Adapted from the supplied Pearl Office Safari WASD V7, app_v7.js.
// All 13 room layouts, furniture, glass, materials, lighting and detail are retained.
// Navigation does not consume the legacy visual colliders collected by these helpers.
export function createPearlScene(THREE, config={}) {
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x09131b);
scene.fog = new THREE.FogExp2(0x09131b, 0.018);
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
  const top = box('DeskTop',w,.10,d,x,.78,z,material,rot,true);
  const sin=Math.sin(rot), cos=Math.cos(rot);
  for(const sx of [-1,1]) for(const sz of [-1,1]) {
    const lx=sx*(w/2-.14), lz=sz*(d/2-.13);
    const wx=x+lx*cos+lz*sin, wz=z-lx*sin+lz*cos;
    box('DeskLeg',.09,.72,.09,wx,.38,wz,M.black,rot,false);
  }
  return top; // V7 repair: interactions must reference an actual mesh.
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
// Preserve plan X/Z coordinates AND upward-facing winding. The V7 -PI/2
// transform fixed the normal but reflected Z, leaving the actual shell uncovered.
const floorGeometry = new THREE.ShapeGeometry(floorShape, 24);
floorGeometry.rotateX(Math.PI / 2);
const floorIndices = floorGeometry.getIndex();
for (let i = 0; i < floorIndices.count; i += 3) {
  const b = floorIndices.getX(i + 1);
  floorIndices.setX(i + 1, floorIndices.getX(i + 2));
  floorIndices.setX(i + 2, b);
}
floorGeometry.computeVertexNormals();
const floor = new THREE.Mesh(floorGeometry, M.floor);
floor.name = 'ConnectedBaseFloor';
floor.position.y = -0.006; floor.receiveShadow = true; scene.add(floor);

// Fill the explicitly approved walkable union beneath the retained curved floor.
// V7's coarse nav envelope and Bezier visual outline also differed at the tip/right
// edge. This supporting surface prevents any valid navigation point floating over
// an empty patch while preserving the detailed scene above it.
for (const polygon of config.navigation?.polygons || []) {
  const shape = new THREE.Shape(polygon.vertices.map(([x,z]) => new THREE.Vector2(x,-z)));
  const surface = new THREE.Mesh(new THREE.ShapeGeometry(shape), M.floor);
  surface.name = 'NavigationFloor_' + polygon.id;
  surface.rotation.x = -Math.PI / 2;
  surface.position.y = -0.012;
  surface.receiveShadow = true;
  scene.add(surface);
}

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


return { scene, interactables, zones:zoneVolumes, sun, dynamicGlow, legacyVisualColliderCount:colliders.length, floor };
}
