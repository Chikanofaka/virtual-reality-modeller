import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validateAssetPath,inspectGLB,verifiedModelBytes} from '../runtime/assets.js';
function glb(json) {
  const body=new TextEncoder().encode(JSON.stringify(json));
  const n=Math.ceil(body.length/4)*4,bytes=new Uint8Array(20+n);bytes.fill(32,20);
  const view=new DataView(bytes.buffer);view.setUint32(0,0x46546c67,true);view.setUint32(4,2,true);view.setUint32(8,bytes.length,true);view.setUint32(12,n,true);view.setUint32(16,0x4e4f534a,true);bytes.set(body,20);return bytes.buffer;
}
test('model paths stay inside the served build',()=>{
  assert.equal(validateAssetPath('assets/office.glb'),'assets/office.glb');
  for(const path of ['../office.glb','assets/%2e%2e/office.glb','https://example.com/model.glb','/tmp/model.glb','assets\\model.glb','assets/model.glb?x=1','assets/model.gltf'])assert.throws(()=>validateAssetPath(path));
});
test('self-contained GLB accepted, external resources and unsupported compression rejected',()=>{
  assert.equal(inspectGLB(glb({asset:{version:'2.0'},scenes:[{}],meshes:[{primitives:[]}]})).asset.version,'2.0');
  for(const field of ['buffers','images'])assert.throws(()=>inspectGLB(glb({asset:{version:'2.0'},[field]:[{uri:'https://example.com/remote.bin'}]})),/External/);
  for(const extension of ['KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_texture_basisu'])assert.throws(()=>inspectGLB(glb({asset:{version:'2.0'},extensionsUsed:[extension]})),/decoder/);
  assert.throws(()=>inspectGLB(glb({asset:{version:'2.0'},images:[{uri:'data:image/svg+xml;base64,PHN2Zz4='}]})),/non-raster/);
  assert.throws(()=>inspectGLB(glb({asset:{version:'2.0'},buffers:[{byteLength:100}]})),/binary chunk/);
  assert.throws(()=>inspectGLB(new ArrayBuffer(20)),/glTF/);
  const broken=glb({asset:{version:'2.0'}});new DataView(broken).setUint32(8,40,true);assert.throws(()=>inspectGLB(broken),/length/);
});
test('loaded model bytes must match the planning-lock SHA-256',async()=>{
  const bytes=glb({asset:{version:'2.0'},scenes:[{}],meshes:[{primitives:[]}]});
  const sha=createHash('sha256').update(new Uint8Array(bytes)).digest('hex');
  const fetcher=async()=>({ok:true,arrayBuffer:async()=>bytes});
  assert.equal((await verifiedModelBytes({id:'sample',path:'assets/sample.glb',sha256:sha},fetcher)).byteLength,bytes.byteLength);
  await assert.rejects(verifiedModelBytes({id:'sample',path:'assets/sample.glb',sha256:'0'.repeat(64)},fetcher),/integrity/);
  await assert.rejects(verifiedModelBytes({id:'sample',path:'assets/sample.glb'},fetcher),/SHA-256/);
});
