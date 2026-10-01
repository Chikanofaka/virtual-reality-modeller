/** Local, hash-verified, self-contained GLB adapter. Navigation stays explicit. */
const unsupportedExtensions=new Set(['KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_texture_basisu']);
export function validateAssetPath(path) {
  if(typeof path!=='string'||!path.trim())throw new Error('Model asset path is missing.');
  let decoded;try{decoded=decodeURIComponent(path);}catch{throw new Error('Malformed model asset path.');}
  if(/[:\\?#\0]/.test(decoded)||decoded.startsWith('/')||decoded.split('/').some(p=>p==='..'||p===''))throw new Error(`Model asset must use a local relative path: ${path}`);
  if(!/\.glb$/i.test(decoded))throw new Error('Only self-contained .glb models are supported.');
  return path;
}
export function inspectGLB(buffer) {
  if(!(buffer instanceof ArrayBuffer)||buffer.byteLength<20)throw new Error('Invalid GLB: missing header.');
  if(buffer.byteLength>256_000_000)throw new Error('GLB exceeds the 256 MB per-asset limit.');
  const view=new DataView(buffer);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2)throw new Error('Model must be glTF 2.0 binary (GLB).');
  if(view.getUint32(8,true)!==buffer.byteLength)throw new Error('Invalid GLB: declared length differs from file.');
  let json=null,offset=12,chunkCount=0,binaryLength=null;
  while(offset<buffer.byteLength){
    if(offset+8>buffer.byteLength)throw new Error('Invalid GLB chunk header.');
    const length=view.getUint32(offset,true),type=view.getUint32(offset+4,true);offset+=8;
    if(length%4!==0||offset+length>buffer.byteLength)throw new Error('Invalid GLB chunk length.');
    if(chunkCount++===0 && type!==0x4e4f534a)throw new Error('GLB first chunk must contain JSON.');
    if(type===0x4e4f534a){if(json)throw new Error('Duplicate GLB JSON chunk.');json=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,offset,length)).trim());}
    if(type===0x004e4942){if(binaryLength!==null)throw new Error('Multiple GLB binary chunks.');binaryLength=length;}
    offset+=length;
  }
  if(!json||json.asset?.version!=='2.0')throw new Error('Missing glTF 2.0 asset metadata.');
  for(const extension of [...(json.extensionsUsed||[]),...(json.extensionsRequired||[])])if(unsupportedExtensions.has(extension))throw new Error(`GLB extension ${extension} requires an unbundled decoder. Export an uncompressed GLB.`);
  function walk(value){
    if(!value||typeof value!=='object')return;
    for(const [key,item] of Object.entries(value)){
      if(unsupportedExtensions.has(key))throw new Error(`GLB extension ${key} requires an unbundled decoder.`);
      if(key==='uri'){
        if(typeof item!=='string'||!/^data:(?:application\/(?:octet-stream|gltf-buffer)|image\/(?:png|jpeg|webp));base64,[A-Za-z0-9+/=]*$/.test(item))throw new Error('External GLB resource or non-raster data URI rejected. Embed buffers and PNG/JPEG/WebP textures.');
        try{atob(item.split(',')[1]);}catch{throw new Error('Malformed GLB base64 resource.');}
      }
      walk(item);
    }
  }
  walk(json);
  for(const [index,buffer] of (json.buffers||[]).entries()){
    if(!Number.isInteger(buffer.byteLength)||buffer.byteLength<0)throw new Error('Invalid GLB buffer length.');
    if(!('uri' in buffer)&&(index!==0||binaryLength===null||buffer.byteLength>binaryLength))throw new Error('GLB embedded buffer exceeds its binary chunk.');
  }
  for(const view of json.bufferViews||[]){
    const offset=view.byteOffset||0,length=view.byteLength,buffer=json.buffers?.[view.buffer];
    if(!Number.isInteger(view.buffer)||!buffer||!Number.isInteger(offset)||offset<0||!Number.isInteger(length)||length<0||offset+length>buffer.byteLength)throw new Error('GLB buffer view exceeds its buffer.');
  }
  if(!json.meshes?.length)throw new Error('GLB must contain at least one mesh.');
  return json;
}
export async function verifiedModelBytes(asset,fetcher=fetch) {
  validateAssetPath(asset.path);
  if(!/^[a-f0-9]{64}$/i.test(asset.sha256||''))throw new Error(`Model ${asset.id} requires a SHA-256 digest in the locked plan.`);
  const response=await fetcher(asset.path,{cache:'no-store'});if(!response.ok)throw new Error(`Cannot load model ${asset.id}: HTTP ${response.status}`);
  const bytes=await response.arrayBuffer();
  const actual=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
  if(actual!==asset.sha256.toLowerCase())throw new Error(`Model ${asset.id} failed integrity verification. Re-ingest and approve the changed asset.`);
  inspectGLB(bytes);return bytes;
}
export async function loadModels(config,scene,onProgress=()=>{}) {
  const models=(config.assets||[]).filter(a=>a.type==='model');
  if(config.scene?.mode==='imported-glb'&&!models.some(a=>a.id===config.scene.assetId))throw new Error('Imported GLB scene requires scene.assetId to reference an approved model asset.');
  if(!models.length)return {models:0,meshes:0};
  const {GLTFLoader}=await import('./vendor/addons/loaders/GLTFLoader.js');
  const loader=new GLTFLoader();let meshes=0;
  for(const asset of models) {
    onProgress(`Verifying detailed model: ${asset.id}`);
    const bytes=await verifiedModelBytes(asset);
    const gltf=await new Promise((resolve,reject)=>loader.parse(bytes,'',resolve,reject));
    const model=gltf.scene;if(!model)throw new Error(`Model ${asset.id} has no default scene.`);
    const placement=asset.placement||{};
    model.position.fromArray(placement.position||[0,0,0]);model.rotation.fromArray([...(placement.rotation||[0,0,0]),'XYZ']);model.scale.fromArray(placement.scale||[1,1,1]);
    model.name='ImportedAsset_'+asset.id;
    model.traverse(object=>{if(object.isMesh){object.castShadow=true;object.receiveShadow=true;meshes++;}});
    scene.add(model);
  }
  return {models:models.length,meshes};
}
