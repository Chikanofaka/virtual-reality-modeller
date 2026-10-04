/** Optional real Chromium/WebKit smoke test. This is not physical Safari acceptance.
 * npm install; npx playwright install chromium; node tests/browser-smoke.mjs URL
 * BROWSER_EXECUTABLE can point at installed Chrome. PLAYWRIGHT_MODULE is a local
 * test-environment override, never embedded into the shipped runtime. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);
const playwright=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const supplied=process.argv[2];
if(!supplied)throw new Error('Usage: node tests/browser-smoke.mjs http://127.0.0.1:PORT/?build=BUILD_ID');
const url=new URL(supplied);assert.equal(url.hostname,'127.0.0.1','Test only an explicitly launched local build');
url.searchParams.set('test','1');
const browserName=process.env.TEST_BROWSER||'chromium';
const browser=await playwright[browserName].launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
const context=await browser.newContext({viewport:{width:1440,height:960},deviceScaleFactor:1});
const page=await context.newPage();
const errors=[],externalRequests=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
await context.route('**/*',async route=>{
  const u=new URL(route.request().url());
  if(u.hostname!=='127.0.0.1'&&!['data:','blob:'].includes(u.protocol)){externalRequests.push(u.origin);return route.abort();}
  return route.continue();
});
const snapshot=()=>page.evaluate(()=>window.__VSMVP.snapshot());
const distance=(a,b)=>Math.hypot(a.position.x-b.position.x,a.position.z-b.position.z);
const output=process.env.SMOKE_OUTPUT||'test-results/browser';
const results=[];
// Heading is set explicitly; translation is real keyboard input processed by the
// runtime's normal frame loop and collision checks. No position teleport is used.
async function walkTo(point) {
  const before=await snapshot(),distance=Math.hypot(before.position.x-point[0],before.position.z-point[1]);
  if(distance<.1)return;
  await page.evaluate(target=>{
    const current=window.__VSMVP.snapshot().position;
    window.__VSMVP.test.setYaw(Math.atan2(-(target[0]-current.x),-(target[1]-current.z)));
  },point);
  await page.keyboard.down('w');
  try {
    await page.waitForFunction(target=>{
      const current=window.__VSMVP.snapshot().position;
      return Math.hypot(current.x-target[0],current.z-target[1])<.16;
    },point,{timeout:30000});
  }finally{await page.keyboard.up('w');}
  const after=await snapshot();
  assert.ok(after.simulationTicks>before.simulationTicks,'Walking must run the movement simulation');
  assert.ok(Math.hypot(after.position.x-point[0],after.position.z-point[1])<.4,'Keyboard travel must reach the route waypoint');
}
async function playCustomRoutes(config) {
  let earlyInteractions=0,advanced=0,waypoints=0;
  for(const route of config.navigation.routes)for(const point of route.points) {
    await walkTo(point);waypoints++;
    const frame=(await snapshot()).frames;
    await page.waitForFunction(previous=>window.__VSMVP.snapshot().frames>=previous+6,frame);
    const before=await snapshot(),targetId=before.nearestId;
    if(!targetId)continue;
    const expected=before.gameplay.currentObjective?.targetId===targetId;
    const future=config.gameplay.objectives.slice(before.gameplay.index+1).some(objective=>objective.targetId===targetId);
    await page.keyboard.press('e');
    const after=await snapshot();
    assert.equal(after.gameplay.index,before.gameplay.index+Number(expected),'Interaction must only advance the current objective');
    if(expected)advanced++;else if(future)earlyInteractions++;
  }
  const final=await snapshot();
  assert.equal(final.gameplay.complete,true,'Approved route waypoints must support completing the custom game');
  assert.deepEqual(final.gameplay.completedObjectiveIds,config.gameplay.objectives.map(objective=>objective.id));
  assert.ok((await page.locator('#objective').textContent()).includes(config.gameplay.completionMessage||'All objectives complete — explore freely.'));
  return {advanced,earlyInteractions,waypoints};
}
try {
  await page.goto(url.href,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__VSMVP?.ready,{timeout:60000});
  assert.ok((await snapshot()).frames>=1,'Entry readiness must follow a completed first render');
  const config=await page.evaluate(()=>fetch('config.json').then(r=>r.json()));
  await page.locator('#enter').click();
  await page.waitForFunction(()=>window.__VSMVP?.snapshot().started);
  let before=await snapshot();assert.equal(before.buildId,url.searchParams.get('build'));
  assert.ok(before.meshCount>0);
  if(config.scene.mode==='pearl-v7')assert.ok(before.interactableCount>=13);
  for(const key of ['w','a','s','d']) {
    await page.keyboard.press('r');before=await snapshot();
    await page.keyboard.down(key);
    await page.waitForFunction(start=>{const s=window.__VSMVP.snapshot();return Math.hypot(s.position.x-start.x,s.position.z-start.z)>.12;},before.position,{timeout:15000});
    await page.keyboard.up(key);
    const after=await snapshot();assert.ok(distance(before,after)>.1);
    results.push({check:'keyboard '+key,displacement:distance(before,after)});
  }
  await page.keyboard.press('r');
  const canvas=page.locator('#gameCanvas');
  const rect=await canvas.boundingBox();
  const beforeImage=await canvas.screenshot();before=await snapshot();
  await page.mouse.move(rect.x+rect.width*.52,rect.y+rect.height*.6);await page.mouse.down();
  await page.mouse.move(rect.x+rect.width*.74,rect.y+rect.height*.52,{steps:12});await page.mouse.up();
  await page.waitForFunction(y=>Math.abs(window.__VSMVP.snapshot().yaw-y)>.1,before.yaw);
  const afterImage=await canvas.screenshot();
  assert.notEqual(createHash('sha256').update(beforeImage).digest('hex'),createHash('sha256').update(afterImage).digest('hex'));
  results.push({check:'drag-look + distinct rendered canvas',passed:true});
  await page.keyboard.press('r');before=await snapshot();
  const pad=await page.locator('[data-move="KeyW"]').boundingBox();
  await page.mouse.move(pad.x+pad.width/2,pad.y+pad.height/2);await page.mouse.down();
  await page.waitForFunction(start=>{const s=window.__VSMVP.snapshot();return Math.hypot(s.position.x-start.x,s.position.z-start.z)>.12;},before.position,{timeout:15000});
  await page.mouse.move(rect.width*.5,rect.height*.8);await page.mouse.up();
  await page.waitForFunction(()=>window.__VSMVP.snapshot().input.virtual.length===0);
  results.push({check:'virtual pad moves + release outside clears hold',passed:true});
  await page.keyboard.down('w');await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  assert.equal((await snapshot()).input.physical.length,0);await page.keyboard.up('w');
  await page.keyboard.press('m');assert.equal(await page.locator('#mapWrap').isVisible(),false);
  await page.keyboard.press('m');assert.equal(await page.locator('#mapWrap').isVisible(),true);
  await page.keyboard.press('q');await page.setViewportSize({width:1366,height:900});
  await page.waitForFunction(()=>window.__VSMVP.snapshot().frames>30);
  if(config.scene.mode==='pearl-v7') {
    for(const [position,needle] of [[[-8.7,.55],'Reception'],[[13.3,3.2],'Wine'],[[0,-2.65],'Pearl']]) {
      await page.evaluate(([x,z])=>window.__VSMVP.test.setPosition(x,z),position);
      await page.waitForFunction(name=>(window.__VSMVP.snapshot().nearest||'').includes(name),needle,{timeout:10000});
      await page.keyboard.press('e');
    }
    await page.waitForFunction(()=>document.querySelector('#objective').textContent.includes('tour complete'));
    results.push({check:'reception → wine → Pearl console interaction progression',passed:true});
  }
  if(config.gameplay) {
    await page.keyboard.press('r');
    assert.equal((await snapshot()).gameplay.index,0);
    assert.equal((await snapshot()).interactableCount,config.furniture.filter(item=>item.interaction).length);
    const first=await playCustomRoutes(config);
    if(config.project.id==='external-user-game')assert.ok(first.earlyInteractions>0,'External-user fixture must exercise an out-of-order interaction');
    results.push({check:'custom game completed by keyboard movement along approved routes',passed:true,...first});
    await page.keyboard.press('r');
    const reset=await snapshot();
    assert.equal(reset.gameplay.index,0);assert.equal(reset.gameplay.complete,false);
    assert.deepEqual(reset.gameplay.completedObjectiveIds,[]);
    assert.equal(reset.gameplay.currentObjective.id,config.gameplay.objectives[0].id);
    assert.ok((await page.locator('#objective').textContent()).includes(config.gameplay.objectives[0].label));
    const replay=await playCustomRoutes(config);
    results.push({check:'reset restores first objective and the complete game can be replayed',passed:true,...replay});
    if(config.scene.mode==='imported-glb')results.push({check:'imported model retains all planned interaction targets and ordered gameplay',passed:true});
  }
  const final=await snapshot();assert.equal(final.frames,final.renderCount);assert.deepEqual(final.errors,[]);
  const modelAssets=(config.assets||[]).filter(a=>a.type==='model');
  if(modelAssets.length){assert.equal(final.importedModels,modelAssets.length);assert.ok(final.importedMeshes>0);results.push({check:'hash-verified local GLB imported before Enter',models:final.importedModels,meshes:final.importedMeshes});}
  assert.deepEqual(errors,[]);assert.deepEqual(externalRequests,[]);
  await mkdir(output,{recursive:true});
  await canvas.screenshot({path:output+'/scene.png'});
  await page.screenshot({path:output+'/tour.png'});
  const stale=new URL(url);stale.searchParams.set('build','intentionally-stale');
  const response=await page.request.get(stale.href);assert.equal(response.status(),409);
  const indexResponse=await page.request.get(url.href);assert.match(indexResponse.headers()['cache-control'],/no-store/);
  results.push({check:'stale URL rejected; no-store; no external requests; single render owner',passed:true});
  const metadata=await page.evaluate(()=>window.__VSMVP.build);
  assert.equal(final.planHash,metadata.planHash);assert.equal(final.runtimeHash,metadata.runtimeHash);
  const report={passed:true,browser:browserName,browserVersion:browser.version(),buildId:final.buildId,planHash:metadata.planHash,runtimeHash:metadata.runtimeHash,checks:results,final,errors,externalRequests,limitations:['Automated key delivery, not a physical hardware keyboard.','Headless rendering is not macOS window-compositor certification.']};
  await writeFile(output+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}finally{await browser.close();}
