import {distanceToSegment} from './navigation.js';

// Exact segment geometry, rather than sampled rays, keeps thin walls visible.
function cross(a,b,p) {
  return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);
}
function segmentDistance(a,b,c,d) {
  const ac=cross(a,b,c),ad=cross(a,b,d),ca=cross(c,d,a),cb=cross(c,d,b);
  const boundsOverlap=Math.max(Math.min(a[0],b[0]),Math.min(c[0],d[0]))<=Math.min(Math.max(a[0],b[0]),Math.max(c[0],d[0]))
    && Math.max(Math.min(a[1],b[1]),Math.min(c[1],d[1]))<=Math.min(Math.max(a[1],b[1]),Math.max(c[1],d[1]));
  // The bounds check distinguishes overlapping from disjoint collinear segments
  // and also handles a segment consisting of a single point.
  if(boundsOverlap&&ac*ad<=0&&ca*cb<=0)return 0;
  return Math.min(distanceToSegment(...a,c,d),distanceToSegment(...b,c,d),distanceToSegment(...c,a,b),distanceToSegment(...d,a,b));
}

/** Visibility in the horizontal XZ plane only. It is opt-in and tests structural
 * navigation segments as capsules of half their thickness. Furniture blockers,
 * player radius, mesh geometry and target elevation do not affect this test. */
export function interactionVisible(config,from2,to2) {
  if(config?.runtime?.interactionOcclusion!=='structural-segments')return true;
  for(const wall of config.navigation?.segments||[]) {
    if(segmentDistance(from2,to2,wall.a,wall.b)<=(wall.thickness||0)/2)return false;
  }
  return true;
}

/** Return the original nearest visible candidate, or null. Positions are
 * [x,y,z]; distance is horizontal, strictly less than radius, with first tie wins. */
export function selectNearestInteraction(config,position2,candidates,radius=2.15) {
  let nearest=null,distance=radius;
  for(const candidate of candidates) {
    const target=[candidate.position[0],candidate.position[2]];
    const nextDistance=Math.hypot(target[0]-position2[0],target[1]-position2[1]);
    if(nextDistance<distance&&interactionVisible(config,position2,target)) {
      nearest=candidate;
      distance=nextDistance;
    }
  }
  return nearest;
}
