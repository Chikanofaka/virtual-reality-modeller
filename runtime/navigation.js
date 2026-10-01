/** Pure navigation: explicit walkable surfaces and intentional barriers only.
 * No scene meshes, raycasts, render loops or browser globals are required. */
export const PEARL_BOUNDARY = [[-14.6,7.8],[-16,6.2],[-14.2,2],[-8.2,-4.8],[-1.6,-9.6],[0,-10.55],[1.6,-9.6],[8.2,-4.8],[14.2,2],[16,6.2],[14.6,7.8]];
export function rotatedRectangle(x,z,w,d,a=0) {
  return [[-w/2,-d/2],[w/2,-d/2],[w/2,d/2],[-w/2,d/2]].map(([lx,lz])=>[x+lx*Math.cos(a)+lz*Math.sin(a),z-lx*Math.sin(a)+lz*Math.cos(a)]);
}
export function pointInPolygon(x,z,vertices) {
  let inside=false;
  for(let i=0,j=vertices.length-1;i<vertices.length;j=i++) {
    const [ax,az]=vertices[i], [bx,bz]=vertices[j];
    if(distanceToSegment(x,z,[ax,az],[bx,bz]) < 1e-8) return true;
    if((az>z)!==(bz>z) && x<(bx-ax)*(z-az)/(bz-az)+ax) inside=!inside;
  }
  return inside;
}
export function distanceToSegment(x,z,a,b) {
  const dx=b[0]-a[0], dz=b[1]-a[1], d=dx*dx+dz*dz;
  const t=d ? Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/d)) : 0;
  return Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz);
}
export function pearlNavigationConfig() {
  const segments=[];
  for(let i=0;i<44;i++) {
    const a=i/44*Math.PI*2,b=(i+1)/44*Math.PI*2;
    if((a+b)/2>.42 && (a+b)/2<.91) continue;
    segments.push({a:[7.25*Math.cos(a),-.25+4.15*Math.sin(a)],b:[7.25*Math.cos(b),-.25+4.15*Math.sin(b)],thickness:.075});
  }
  return {runtime:{playerRadius:.22},navigation:{polygons:[{id:'shell',vertices:PEARL_BOUNDARY},{id:'entry',vertices:rotatedRectangle(-10.95,1.92,3.2,2.5,-.72)}],segments}};
}
export function createNavigation(config={}) {
  const nav=config.navigation||{}, radius=config.runtime?.playerRadius??.22;
  const polygons=(nav.polygons||[]).map(p=>p.vertices||p);
  const blockers=nav.blockers||[], segments=nav.segments||[];
  if(!polygons.length) throw new Error('No explicit navigation polygons supplied.');
  function onSurface(x,z) { return polygons.some(p=>pointInPolygon(x,z,p)); }
  function canMove(x,z) {
    if(!Number.isFinite(x)||!Number.isFinite(z)||!onSurface(x,z)) return false;
    // Test the union, so adjoining polygons do not acquire false seams.
    for(let i=0;i<16;i++) {
      const a=i*Math.PI/8;
      if(!onSurface(x+Math.cos(a)*radius,z+Math.sin(a)*radius)) return false;
    }
    for(const blocker of blockers) {
      const [x1,z1,x2,z2]=blocker.bounds;
      const cx=Math.max(x1,Math.min(x2,x)),cz=Math.max(z1,Math.min(z2,z));
      if(Math.hypot(x-cx,z-cz)<=radius) return false;
    }
    for(const s of segments) if(distanceToSegment(x,z,s.a,s.b)<=radius+(s.thickness||0)/2) return false;
    return true;
  }
  function move(position,dx,dz) {
    if(![position.x,position.z,dx,dz].every(Number.isFinite)) throw new Error('Non-finite movement.');
    const distance=Math.hypot(dx,dz);
    // Collision checks every <= 3.5 cm prevent fast sprint / slow frame tunnelling.
    const steps=Math.max(1,Math.ceil(distance/Math.min(.035,Math.max(.005,radius/3))));
    const sx=dx/steps,sz=dz/steps;
    let moved=false;
    for(let i=0;i<steps;i++) {
      const x=position.x,z=position.z;
      if(canMove(x+sx,z+sz)) { position.x+=sx;position.z+=sz;moved=true;continue; }
      if(canMove(x+sx,z)) {position.x+=sx;moved=true;}
      if(canMove(position.x,z+sz)) {position.z+=sz;moved=true;}
    }
    return moved;
  }
  return {canMove,move,polygons,blockers,segments,radius};
}
