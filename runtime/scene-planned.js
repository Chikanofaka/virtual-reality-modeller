/** Deterministic planning-pack scene. Uploaded assets are never silently fabricated.
 * Pearl uses the preserved detailed scene in scene-pearl.js instead. */
export function createPlannedScene(THREE,config) {
  const imported=config.scene?.mode==='imported-glb';
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x09131b);
  scene.fog=new THREE.FogExp2(0x09131b,.008);
  const zones=[],interactables=[];
  const material=(color,roughness=.55)=>new THREE.MeshStandardMaterial({color,roughness});
  const wallMat=material(config.materials?.wall||'#c7cdd1');
  const wood=material('#8b5b36'),metal=material('#18232c');
  function box(name,w,h,d,x,y,z,mat=wood,rotation=0) {
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);mesh.name=name;mesh.position.set(x,y,z);mesh.rotation.y=rotation;mesh.castShadow=true;mesh.receiveShadow=true;scene.add(mesh);return mesh;
  }
  // ShapeGeometry triangulates the supplied polygon in XY. Map plan Z to -Y,
  // then rotate -PI/2: correct X/Z footprint with an upward-facing front face.
  for(const polygon of config.navigation.polygons) {
    const shape=new THREE.Shape(polygon.vertices.map(([x,z])=>new THREE.Vector2(x,-z)));
    const floor=new THREE.Mesh(new THREE.ShapeGeometry(shape),material(config.materials?.floor||'#c8c2b5'));
    floor.name='NavigationBaseFloor_'+polygon.id;floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
  }
  const height=config.shell?.height||2.8;
  function wallRun(room,axis,fixed,min,max) {
    const doors=(config.doors||[]).filter(d=>d.roomIds?.includes(room.id) && d.axis===axis && Math.abs(d.center[axis==='x'?1:0]-fixed)<.15);
    const cuts=doors.map(d=>[Math.max(min,d.center[axis==='x'?0:1]-d.width/2),Math.min(max,d.center[axis==='x'?0:1]+d.width/2)]).sort((a,b)=>a[0]-b[0]);
    let cursor=min;
    const wall=(a,b)=>{if(b-a<.02)return;const mid=(a+b)/2;box(room.id+'Wall',axis==='x'?b-a:.12,height,axis==='x'?.12:b-a,axis==='x'?mid:fixed,height/2,axis==='x'?fixed:mid,wallMat);};
    for(const [a,b] of cuts){wall(cursor,a);cursor=Math.max(cursor,b);}wall(cursor,max);
    for(const door of doors) if(door.height && door.height<height) {
      const y=door.height+(height-door.height)/2;
      box(door.id+'Header',axis==='x'?door.width:.12,height-door.height,axis==='x'?.12:door.width,door.center[0],y,door.center[1],wallMat);
    }
  }
  for(const room of config.rooms||[]) {
    const [x1,z1,x2,z2]=room.bounds,x=(x1+x2)/2,z=(z1+z2)/2,w=x2-x1,d=z2-z1;
    zones.push({name:room.name,x,z,w,d,rot:0});
    if(imported)continue; // Detailed imported shell owns its room geometry.
    box(room.id+'Floor',w,.022,d,x,(room.floorY||0)+.013,z,material(room.color||'#d7d1c4'));
    if(!room.open){wallRun(room,'x',z1,x1,x2);wallRun(room,'x',z2,x1,x2);wallRun(room,'z',x1,z1,z2);wallRun(room,'z',x2,z1,z2);}
  }
  for(const item of imported?[]:(config.furniture||[])) {
    const [x,y,z]=item.position,[w,h,d]=item.size,rot=item.rotation||0,mat=material(item.color||'#8b5b36');
    let object;
    if(['desk','table'].includes(item.type)) {
      object=box(item.id,w,.1,d,x,y+h-.05,z,mat,rot);
      for(const sx of [-1,1])for(const sz of [-1,1]){const lx=sx*(w/2-.1),lz=sz*(d/2-.1);box(item.id+'Leg',.08,h-.1,.08,x+lx*Math.cos(rot)+lz*Math.sin(rot),y+(h-.1)/2,z-lx*Math.sin(rot)+lz*Math.cos(rot),metal,rot);}
    } else if(['chair','sofa'].includes(item.type)) {
      object=box(item.id,w,h*.4,d,x,y+h*.35,z,mat,rot);
      box(item.id+'Back',w,h*.65,.13,x+Math.sin(rot)*(d/2-.065),y+h*.675,z+Math.cos(rot)*(d/2-.065),mat,rot);
    } else if(item.type==='shelf') {
      object=box(item.id,w,h,.08,x,y+h/2,z,mat,rot);
      for(let i=0;i<4;i++)box(item.id+'Shelf',w,.05,d,x,y+.05+i*(h-.1)/3,z,mat,rot);
    } else object=box(item.id,w,h,d,x,y+h/2,z,mat,rot);
    if(item.interaction)interactables.push({obj:object,label:item.interaction.label||item.id,type:'generic',message:item.interaction.message||item.id});
  }
  for(const room of config.rooms||[]) {
    const [x1,z1,x2,z2]=room.bounds;
    const light=new THREE.PointLight(0xffe6c5,22,Math.max(x2-x1,z2-z1)*1.8);light.position.set((x1+x2)/2,height-.15,(z1+z2)/2);scene.add(light);
  }
  scene.add(new THREE.HemisphereLight(0xd7edff,0x5d4330,1.25));
  const sun=new THREE.DirectionalLight(0xfff0d5,2.6);sun.position.set(-5,10,-7);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);scene.add(sun);
  return {scene,zones,interactables,sun,dynamicGlow:[],legacyVisualColliderCount:0};
}
