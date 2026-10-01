/** Pure identity policy, shared with smoke tests. Hash expected in launcher URL. */
export function verifyBuildIdentity(build,location) {
  if(!build || !build.buildId || !build.version) return {ok:false,reason:'Missing build identity. Rebuild using the harness.'};
  const expected=new URLSearchParams(location.search||'').get('build');
  if(!expected) return {ok:false,reason:'Missing expected build ID in the URL. Open the exact URL printed by play or the one-click launcher.'};
  if(expected!==build.buildId) return {ok:false,reason:`Wrong build: requested ${expected}; server returned ${build.buildId}. Stop and launch the intended build.`};
  if(build.expectedPort && String(build.expectedPort)!==String(location.port)) return {ok:false,reason:`Wrong port: expected ${build.expectedPort}, reached ${location.port}.`};
  return {ok:true,reason:'Build ID verified'};
}
