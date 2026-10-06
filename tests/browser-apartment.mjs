/** Real keyboard traversal and delivery acceptance for the authored apartment. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createNavigation} from '../runtime/navigation.js';
const require=createRequire(import.meta.url),{chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const url=new URL(process.argv[2]);assert.equal(url.hostname,'127.0.0.1');url.searchParams.set('test','1');
const out=process.env.APARTMENT_OUTPUT||'test-results/apartment-browser';await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});const page=await context.newPage();
const errors=[],externalRequests=[],checks=[];let config,nav,actualNav,grid,gridOrigin,gridStep=.11,walkingDistance=0;
page.on('pageerror',e=>errors.push(e.message));page.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
await context.route('**/*',async route=>{const u=new URL(route.request().url());if(u.hostname!=='127.0.0.1'&&!['data:','blob:'].includes(u.protocol)){externalRequests.push(u.href);return route.abort();}return route.continue();});
const snap=()=>page.evaluate(()=>window.__VSMVP.snapshot());
const point=s=>[s.position.x,s.position.z];const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
async function frames(n=4){const f=(await snap()).frames;await page.waitForFunction(v=>window.__VSMVP.snapshot().frames>=v.f+v.n,{f,n});}
function clear(a,b,policy=nav){const n=Math.max(1,Math.ceil(dist(a,b)/.03));for(let i=0;i<=n;i++)if(!policy.canMove(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n))return false;return true;}
function makeGrid(){
 const ps=config.navigation.polygons.flatMap(p=>p.vertices),xs=ps.map(p=>p[0]),zs=ps.map(p=>p[1]);gridOrigin=[Math.min(...xs),Math.min(...zs)];grid=new Map();
 for(let i=0;i<=Math.ceil((Math.max(...xs)-gridOrigin[0])/gridStep);i++)for(let j=0;j<=Math.ceil((Math.max(...zs)-gridOrigin[1])/gridStep);j++){
  const p=[gridOrigin[0]+i*gridStep,gridOrigin[1]+j*gridStep];if(nav.canMove(...p))grid.set(i+','+j,p);
 }
}
function nearest(p){let best=null,d=Infinity;const i=Math.round((p[0]-gridOrigin[0])/gridStep),j=Math.round((p[1]-gridOrigin[1])/gridStep);for(let a=i-3;a<=i+3;a++)for(let b=j-3;b<=j+3;b++){const k=a+','+b,v=grid.get(k);if(v&&dist(p,v)<d&&clear(p,v,actualNav)){best=k;d=dist(p,v);}}assert.ok(best,'Navigation grid reaches '+p);return best;}
function path(a,b){
 if(clear(a,b))return[b];const start=nearest(a),end=nearest(b),queue=[start],previous=new Map([[start,null]]);
 for(let h=0;h<queue.length&&!previous.has(end);h++){
  const k=queue[h],[i,j]=k.split(',').map(Number);
  for(const [ii,jj] of [[i-1,j],[i+1,j],[i,j-1],[i,j+1]]){const n=ii+','+jj;if(grid.has(n)&&!previous.has(n)&&clear(grid.get(k),grid.get(n))){previous.set(n,k);queue.push(n);}}
 }
 assert.ok(previous.has(end),'Target connected through player-clear navigation');const raw=[b];for(let k=end;k;k=previous.get(k))raw.push(grid.get(k));raw.push(a);raw.reverse();
 const result=[];for(let i=0;i<raw.length-1;){let j=raw.length-1;while(j>i+1&&!clear(raw[i],raw[j]))j--;result.push(raw[j]);i=j;}return result;
}
async function segment(target){
 const before=await snap(),start=point(before);if(dist(start,target)<.075)return;
 // Continuous steering corrects small key-release latency at narrow corners.
 await page.evaluate(t=>{window.__walkTarget=t;window.__steering=true;const steer=()=>{if(!window.__steering)return;const p=window.__VSMVP.snapshot().position;window.__VSMVP.test.setYaw(Math.atan2(-(t[0]-p.x),-(t[1]-p.z)));requestAnimationFrame(steer);};steer();},target);
 await page.keyboard.down('w');
 try{await page.waitForFunction(t=>{const p=window.__VSMVP.snapshot().position;return Math.hypot(p.x-t[0],p.z-t[1])<.035;},target,{timeout:45000});}
 finally{await page.keyboard.up('w');await page.evaluate(()=>{window.__steering=false;});}
 const after=await snap();assert.ok(after.simulationTicks>before.simulationTicks);assert.ok(dist(point(after),target)<.24);walkingDistance+=dist(start,point(after));
}
async function walk(target){assert.ok(nav.canMove(...target),'Requested point is walkable');console.log('Walk to',target);let pts=path(point(await snap()),target);for(const p of pts){console.log('  waypoint',p);await segment(p);}await frames();}
async function look(target,pitch=-.14){
 await page.evaluate(t=>{const p=window.__VSMVP.snapshot().position;window.__VSMVP.test.setYaw(Math.atan2(-(t[0]-p.x),-(t[1]-p.z)));},target);
 const s=await snap();if(Math.abs(s.pitch-pitch)>.025){const key=s.pitch>pitch?'ArrowDown':'ArrowUp';await page.keyboard.down(key);try{await page.waitForFunction(v=>{const p=window.__VSMVP.snapshot().pitch;return v.down?p<=v.pitch:p>=v.pitch;},{pitch,down:key==='ArrowDown'});}finally{await page.keyboard.up(key);}}
 await frames();
}
function assertReset(s){assert.equal(s.gameplay.index,0);assert.equal(s.gameplay.complete,false);assert.ok(dist(point(s),[config.entrance.position[0],config.entrance.position[2]])<.001);for(const t of s.interactionEffects.targets){assert.equal(t.active,false);for(const e of t.effects)for(const m of e.materials)assert.deepEqual(m.current,m.initial);}}
async function screenshot(name){await page.screenshot({path:out+'/'+name+'.png'});}
async function activate(id,approach,capture){
 await walk(approach);const item=config.furniture.find(f=>f.id===id);await look([item.position[0],item.position[2]],-.25);
 const before=await snap();assert.equal(before.nearestId,id);assert.equal(before.gameplay.currentObjective.targetId,id);
 const canvas=page.locator('#gameCanvas'),oldPixels=await canvas.screenshot();await page.keyboard.press('e');await frames();const after=await snap();
 assert.equal(after.gameplay.index,before.gameplay.index+1);
 const target=after.interactionEffects.targets.find(t=>t.targetId===id);
 if(target){assert.equal(target.active,true);for(const e of target.effects)for(const m of e.materials)assert.deepEqual(m.current,{emissive:e.planned.emissive.toLowerCase(),intensity:e.planned.intensity});const newPixels=await canvas.screenshot();assert.notEqual(createHash('sha256').update(oldPixels).digest('hex'),createHash('sha256').update(newPixels).digest('hex'));}
 await page.keyboard.press('e');assert.equal((await snap()).gameplay.index,after.gameplay.index,'Repeat E cannot duplicate progress');
 if(capture)await screenshot(capture);
}
async function play(prefix){
 await activate('welcome-tv',[10.6,2.8],prefix+'-tv');await activate('bedroom-lamp',[1.25,4.7],prefix+'-bedroom');await activate('balcony-view',[10.9,-.65],prefix+'-balcony');
 const s=await snap();assert.equal(s.gameplay.complete,true);assert.equal(s.gameplay.index,3);assert.ok((await page.locator('#objective').textContent()).includes(config.gameplay.completionMessage));
}
try{
 await page.goto(url.href,{waitUntil:'networkidle'});await page.waitForFunction(()=>window.__VSMVP?.ready,{timeout:90000});config=await page.evaluate(()=>fetch('config.json').then(r=>r.json()));
 assert.equal(config.project.id,process.env.APARTMENT_PROJECT_ID||'photo-game-intake');actualNav=createNavigation(config);nav=createNavigation({...config,runtime:{...config.runtime,playerRadius:config.runtime.playerRadius+.04}});makeGrid();await page.locator('#enter').click();assertReset(await snap());
 const metadata=await page.evaluate(()=>window.__VSMVP.build);assert.equal(metadata.buildId,url.searchParams.get('build'));assert.ok((await snap()).importedMeshes>40);
 for(const key of ['w','a','s','d']){await page.keyboard.press('r');const before=await snap();await page.keyboard.down(key);try{await page.waitForFunction(p=>{const s=window.__VSMVP.snapshot().position;return Math.hypot(s.x-p.x,s.z-p.z)>.10;},before.position,{timeout:15000});}finally{await page.keyboard.up(key);}}
 await page.keyboard.press('r');checks.push({check:'WASD input moves player through normal simulation',passed:true});
 await walk([10.9,-.65]);assert.equal((await snap()).nearestId,'balcony-view');await page.keyboard.press('e');assert.equal((await snap()).gameplay.index,0);assert.ok((await snap()).interactionEffects.targets.every(t=>!t.active));
 checks.push({check:'early balcony visit cannot skip objectives or light fixtures',passed:true});
 const visited=[];
 for(const room of config.rooms){await walk(room.accessPoint);visited.push(room.id);if(['kitchen','bedroom','primary-bath','bath','living'].includes(room.id)){await look(room.id==='kitchen'?[11.0,8.8]:[(room.bounds[0]+room.bounds[2])/2,(room.bounds[1]+room.bounds[3])/2],-.16);await screenshot('room-'+room.id);}}
 checks.push({check:'all planned room access points reached by actual keyboard walking',passed:true,visited});
 await walk([3.1,4.7]);await look([4.4,4.7],0);await page.keyboard.down('w');try{await page.waitForTimeout(1200);}finally{await page.keyboard.up('w');}
 const collision=await snap();assert.ok(collision.position.x<3.33);assert.ok(collision.position.x>3.1);checks.push({check:'keyboard movement stops at primary-bedroom structural wall',passed:true,position:collision.position});
 for(const [label,p] of [['bed',[1.2,3]],['sofa',[8.15,2.8]],['wardrobe',[6.7,8.11]],['balcony exterior',[10.5,-1.85]]])assert.equal(await page.evaluate(p=>window.__VSMVP.test.canMove(...p),p),false,label+' blocks navigation');
 checks.push({check:'bed, sofa, wardrobe and balcony exterior reject standing positions',passed:true});
 // The balcony is nearby, but the sight line crosses the solid wall left of its doorway.
 await walk([9.8,.75]);assert.ok(Math.hypot(9.8-10.9,.75+.95)<2.15);assert.equal((await snap()).nearestId,null);
 await page.keyboard.press('e');assert.equal((await snap()).gameplay.index,0);checks.push({check:'balcony target within range is unavailable across the solid facade',passed:true});
 await page.keyboard.press('r');assertReset(await snap());await play('first');checks.push({check:'TV, bedroom lamp, balcony ordered completion; visible effects; duplicate input stable',passed:true});
 await page.keyboard.press('r');assertReset(await snap());await play('replay');checks.push({check:'R restores player, tasks and original emissive materials; all three goals replayed',passed:true});
 const final=await snap();assert.equal(final.frames,final.renderCount);assert.deepEqual(final.errors,[]);assert.deepEqual(errors,[]);assert.deepEqual(externalRequests,[]);
 const stale=new URL(url);stale.searchParams.set('build','stale');assert.equal((await page.request.get(stale.href)).status(),409);assert.match((await page.request.get(url.href)).headers()['cache-control'],/no-store/);
 const report={passed:true,browser:'chromium',browserVersion:browser.version(),buildId:metadata.buildId,planHash:metadata.planHash,runtimeHash:metadata.runtimeHash,checks,final,errors,externalRequests,walkingDistanceMeters:walkingDistance,limitations:['Automated keyboard events, not physical hardware or Safari acceptance.','Estimated architectural dimensions; no measurement or photo-level fidelity certification.']};
 await writeFile(out+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,buildId:report.buildId,checks:checks.length,walkingDistanceMeters:walkingDistance,output:out}));
}catch(error){await page.screenshot({path:out+'/failure.png'}).catch(()=>{});await writeFile(out+'/failure.json',JSON.stringify({error:String(error),errors,state:await snap().catch(()=>null)},null,2));throw error;}
finally{await browser.close();}
