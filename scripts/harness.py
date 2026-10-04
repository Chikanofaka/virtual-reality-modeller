#!/usr/bin/env python3
"""Virtual Space MVP: local, dependency-free planning and delivery CLI."""
from __future__ import annotations
import argparse, copy, hashlib, http.server, json, math, mimetypes, os, pathlib, re, shutil, stat, sys, tempfile, threading, time, urllib.parse, webbrowser, zipfile
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = '0.1.0'
MAX_ARCHIVE_BYTES = 1_000_000_000
MAX_ARCHIVE_FILES = 10000
MAX_INGEST_BYTES = 1_000_000_000

def fail(message): raise ValueError(message)
def read(path):
    with open(path, encoding='utf-8') as f: return json.load(f)
def write(path, data):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def sha(path):
    h=hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def digest(data): return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def project(path):
    p=pathlib.Path(path).expanduser().resolve()
    if not (p/'project.json').is_file(): fail(f'Not a project: {p}; use init first')
    return p

def safe_relative(name):
    name=name.replace('\\','/')
    pp=pathlib.PurePosixPath(name)
    if not name or name.startswith('/') or re.match(r'^[A-Za-z]:',name) or '..' in pp.parts or '\x00' in name: fail(f'Unsafe path: {name!r}')
    return pp

def local_file(root,name):
    relative=safe_relative(name); p=root.joinpath(*relative.parts)
    if p.is_symlink() or any(a.is_symlink() for a in p.parents if a!=root and root in a.parents): fail(f'Symlink is not allowed: {name}')
    if not p.resolve().is_relative_to(root.resolve()) or not p.is_file(): fail(f'Missing or escaped local file: {name}')
    return p

def inspect_zip(path):
    entries=[]; total=0; seen=set()
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)>MAX_ARCHIVE_FILES: fail('Archive has too many entries')
        for info in infos:
            safe_relative(info.filename)
            if info.filename in seen: fail('Archive contains duplicate paths')
            seen.add(info.filename)
            if stat.S_ISLNK(info.external_attr>>16): fail('Archive symlinks are not allowed')
            total+=info.file_size
            if total>MAX_ARCHIVE_BYTES: fail('Archive expands beyond 1 GB safety limit')
            if info.flag_bits&1: fail('Encrypted archives are not supported')
            if info.file_size>10_000_000 and info.file_size/max(1,info.compress_size)>200: fail('Archive compression ratio is excessive')
            if info.is_dir(): continue
            h=hashlib.sha256()
            with z.open(info) as f:
                for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
            entries.append({'path':info.filename,'bytes':info.file_size,'sha256':h.hexdigest()})
    return {'files':entries,'totalBytes':total,'execution':'never','extraction':'inventory only'}

def inspect_glb(path):
    """Accept self-contained GLB 2.0 only; never follow resource URIs."""
    import struct, base64
    if pathlib.Path(path).stat().st_size>256_000_000: fail('GLB exceeds the 256 MB per-asset limit')
    data=pathlib.Path(path).read_bytes()
    if len(data)<20 or data[:4]!=b'glTF': fail('Model must be a binary glTF .glb file')
    version,length=struct.unpack_from('<II',data,4)
    if version!=2 or length!=len(data): fail('GLB version or declared length is invalid')
    offset=12; chunks=[]
    while offset<len(data):
        if offset+8>len(data): fail('Truncated GLB chunk header')
        size,kind=struct.unpack_from('<II',data,offset);offset+=8
        if size%4 or offset+size>len(data): fail('Invalid or truncated GLB chunk')
        chunks.append((kind,data[offset:offset+size]));offset+=size
    if not chunks or chunks[0][0]!=0x4e4f534a or len([x for x in chunks if x[0]==0x4e4f534a])!=1: fail('GLB requires a single first JSON chunk')
    document=json.loads(chunks[0][1].decode('utf-8').rstrip(' \x00'))
    if document.get('asset',{}).get('version')!='2.0': fail('glTF asset.version must be 2.0')
    unsupported={'KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_texture_basisu'}
    if unsupported.intersection(document.get('extensionsUsed',[])+document.get('extensionsRequired',[])): fail('Compressed GLB decoder extensions are not supported by this offline release')
    def check_uris(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in unsupported: fail('Compressed GLB decoder extensions are not supported by this offline release')
                if key=='uri':
                    if not isinstance(item,str) or not re.fullmatch(r'data:(?:application/(?:octet-stream|gltf-buffer)|image/(?:png|jpeg|webp));base64,[A-Za-z0-9+/=\r\n]*',item): fail('GLB external URIs and non-raster data URIs are forbidden; embed buffers and PNG/JPEG/WebP textures')
                    try:base64.b64decode(item.split(',',1)[1],validate=True)
                    except Exception:fail('GLB contains malformed base64 data')
                check_uris(item)
        elif isinstance(value,list):
            for item in value:check_uris(item)
    check_uris(document)
    binary=[payload for kind,payload in chunks if kind==0x004e4942]
    if len(binary)>1: fail('GLB contains multiple binary chunks')
    for index,buffer in enumerate(document.get('buffers',[])):
        if not isinstance(buffer.get('byteLength'),int) or buffer['byteLength']<0: fail('Invalid GLB buffer byteLength')
        if 'uri' not in buffer and (index!=0 or not binary or buffer['byteLength']>len(binary[0])): fail('GLB embedded buffer exceeds its binary chunk')
    for view in document.get('bufferViews',[]):
        index=view.get('buffer');offset=view.get('byteOffset',0);length=view.get('byteLength')
        if not isinstance(index,int) or not 0<=index<len(document.get('buffers',[])): fail('GLB bufferView references a missing buffer')
        if not isinstance(offset,int) or offset<0 or not isinstance(length,int) or length<0 or offset+length>document['buffers'][index]['byteLength']: fail('GLB bufferView exceeds its buffer')
    if not document.get('meshes'): fail('GLB must contain at least one mesh')
    return {'format':'glTF 2.0 binary','meshes':len(document['meshes']),'bytes':len(data),'externalResources':False}

def mutate(p):
    for name in ('approval.json','current-build.json'):
        (p/name).unlink(missing_ok=True)

def inputs(p):
    data={name:read(p/name) for name in ('project.json','intake.json','sources.json','planning.json')}
    for source in data['sources.json']['files']:
        if sha(local_file(p,source['path']))!=source['sha256']: fail(f"Ingested content changed: {source['name']}")
    for asset in data['planning.json'].get('assets',[]):
        asset_file=local_file(p,asset['path'])
        if sha(asset_file)!=asset['sha256']: fail(f"Asset content changed: {asset['id']}")
        if asset['type']=='model': inspect_glb(asset_file)
    return data

def plan_hash(p): return digest(inputs(p))

def finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def vector(value,n,label):
    if not isinstance(value,list) or len(value)!=n or not all(finite(x) for x in value): fail(f'{label} must contain {n} finite numbers')
def bounds(value,label):
    vector(value,4,label)
    if value[0]>=value[2] or value[1]>=value[3]: fail(f'{label} must have positive width and depth')
def in_polygon(x,z,pts):
    inside=False
    for i,a in enumerate(pts):
        b=pts[i-1]
        if distance_segment(x,z,a,b)<1e-8: return True
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]: inside=not inside
    return inside

def distance_segment(x,z,a,b):
    dx=b[0]-a[0]; dz=b[1]-a[1]; denom=dx*dx+dz*dz
    t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/denom)) if denom else 0
    return math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)

def walkable(config,x,z):
    nav=config['navigation']; radius=config['runtime']['playerRadius']
    # Sample the disk against the UNION, so shared polygon seams remain traversable.
    points=[(x,z)]+[(x+radius*math.cos(i*math.tau/16),z+radius*math.sin(i*math.tau/16)) for i in range(16)]
    if not all(any(in_polygon(px,pz,p['vertices']) for p in nav['polygons']) for px,pz in points): return False
    for block in nav.get('blockers',[]):
        a,b,c,d=block['bounds']; nearest_x=max(a,min(c,x)); nearest_z=max(b,min(d,z))
        if math.hypot(x-nearest_x,z-nearest_z)<=radius: return False
    for seg in nav.get('segments',[]):
        if distance_segment(x,z,seg['a'],seg['b'])<=radius+seg['thickness']/2: return False
    return True

def segment_walkable(config,a,b,spacing=.06):
    count=max(1,math.ceil(math.dist(a,b)/spacing))
    return all(walkable(config,a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count+1))

def planned_walls(c):
    """Compile simple structural intent, independently of the rendered meshes."""
    for room in c['rooms']:
        if room.get('open'): continue
        x1,z1,x2,z2=room['bounds']
        for axis,fixed,start,end in [('x',z1,x1,x2),('x',z2,x1,x2),('z',x1,z1,z2),('z',x2,z1,z2)]:
            doors=[d for d in c['doors'] if room['id'] in d['roomIds'] and d['axis']==axis and abs(d['center'][1 if axis=='x' else 0]-fixed)<.15]
            cuts=sorted((max(start,d['center'][0 if axis=='x' else 1]-d['width']/2),min(end,d['center'][0 if axis=='x' else 1]+d['width']/2)) for d in doors)
            cursor=start
            for a,b in cuts+[(end,end)]:
                if a>cursor:
                    yield ([cursor,fixed],[a,fixed]) if axis=='x' else ([fixed,cursor],[fixed,a])
                cursor=max(cursor,b)

def validate_structural_barriers(c):
    if c['scene']['mode']!='procedural' or c['navigation']['collisionPolicy']!='explicit-blockers': return
    nav=c['navigation']
    for a,b in planned_walls(c):
        n=max(1,math.ceil(math.dist(a,b)/.1))
        for i in range(n+1):
            x=a[0]+(b[0]-a[0])*i/n;z=a[1]+(b[1]-a[1])*i/n
            barrier=any(block['bounds'][0]<=x<=block['bounds'][2] and block['bounds'][1]<=z<=block['bounds'][3] for block in nav.get('blockers',[])) or any(distance_segment(x,z,seg['a'],seg['b'])<=seg['thickness']/2+1e-6 for seg in nav.get('segments',[]))
            if not barrier: fail('A structural wall has no explicit navigation barrier; add wall segments, mark the room open, or explicitly choose permissive-visual-partitions')

def _validate_config(c, connectivity=True):
    if not isinstance(c,dict): fail('Planning pack must be a JSON object')
    for required in ('project','provenance','shell','rooms','doors','entrance','navigation','furniture','materials','assets','runtime','scene'):
        if required not in c: fail(f'Missing required planning field: {required}')
    for name in ('project','provenance','shell','entrance','navigation','materials','runtime','scene'):
        if not isinstance(c[name],dict): fail(f'{name} must be an object')
    for name in ('rooms','doors','furniture','assets'):
        if not isinstance(c[name],list) or not all(isinstance(item,dict) for item in c[name]): fail(f'{name} must be a list of objects')
    for name in ('polygons','blockers','segments','routes'):
        value=c['navigation'].get(name,[])
        if not isinstance(value,list) or not all(isinstance(item,dict) for item in value): fail(f'navigation.{name} must be a list of objects')
    if c.get('schema_version')!='1.0': fail('schema_version must be 1.0')
    if c.get('units')!='m': fail('Plans must be explicitly normalized to metres (units=m)')
    if not isinstance(c.get('project'),dict) or not c['project'].get('name') or not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}',c['project'].get('id','')): fail('project requires name and stable lowercase id')
    basis=c.get('provenance',{})
    if basis.get('scaleConfirmed') is not True or basis.get('entranceConfirmed') is not True or basis.get('layoutConfirmed') is not True: fail('Scale, entrance and layout must each be explicitly confirmed in provenance')
    if not isinstance(basis.get('basis'),str) or not basis['basis'].strip(): fail('provenance.basis must describe measured input or approved source')
    shell=c.get('shell',{})
    for key in ('width','depth','height'):
        if not finite(shell.get(key)) or not 0<shell[key]<=200: fail(f'shell.{key} must be > 0 and <= 200 metres')
    if shell['height']<1.8: fail('Ceiling is too low for the supported standing experience')
    rt=c.get('runtime',{})
    for key,low,high in [('playerRadius',.1,1),('eyeHeight',.5,2.5),('speed',.2,6)]:
        if not finite(rt.get(key)) or not low<=rt[key]<=high: fail(f'runtime.{key} must be between {low} and {high}')
    if rt['eyeHeight']>=shell['height']: fail('eyeHeight must be below ceiling')
    browsers=rt.get('browsers')
    if not isinstance(browsers,list) or not browsers or not all(isinstance(b,str) and b in {'safari','chrome','firefox','edge'} for b in browsers) or len(set(browsers))!=len(browsers): fail('Target browsers must be a nonempty list of unique supported names')
    rooms=c.get('rooms')
    if not isinstance(rooms,list) or not rooms: fail('At least one measured room is required')
    ids=set()
    for room in rooms:
        if not isinstance(room.get('id'),str) or not room['id'] or room['id'] in ids or not isinstance(room.get('name'),str) or not room['name'].strip(): fail('Rooms require unique ids and names')
        if 'open' in room and not isinstance(room['open'],bool): fail('room.open must be boolean')
        if 'color' in room and (not isinstance(room['color'],str) or not re.fullmatch('#[0-9a-fA-F]{6}',room['color'])): fail('room.color must be a hex color')
        if not finite(room.get('floorY',0)) or room.get('floorY',0)!=0: fail('This release supports a single connected floor at floorY=0; stairs and multiple levels require a navigation adapter')
        ids.add(room['id']); vector(room.get('accessPoint'),2,f"room {room['id']} accessPoint"); bounds(room.get('bounds'),f"room {room['id']} bounds")
        if room['bounds'][2]-room['bounds'][0]>shell['width']+.01 or room['bounds'][3]-room['bounds'][1]>shell['depth']+.01: fail('Room exceeds declared shell dimensions')
    entrance=c.get('entrance',{}); vector(entrance.get('position'),3,'entrance.position')
    if not finite(entrance.get('yaw')): fail('entrance.yaw must be radians')
    if entrance['position'][1]!=rt['eyeHeight']: fail('entrance eye height must match runtime.eyeHeight')
    nav=c.get('navigation',{})
    if 'constraints' in nav: fail('Unsupported navigation.constraints; express barriers as segments or blockers')
    if nav.get('collisionPolicy') not in ('explicit-blockers','permissive-visual-partitions'): fail('Declare navigation.collisionPolicy: explicit-blockers or permissive-visual-partitions')
    vector(nav.get('spawn'),3,'navigation.spawn')
    if nav['spawn']!=entrance['position']: fail('Spawn must equal the approved entrance position')
    polygons=nav.get('polygons',[])
    if not polygons: fail('A connected navigation polygon union is required')
    allpoints=[]
    for polygon in polygons:
        vertices=polygon.get('vertices',[])
        if len(vertices)<3: fail('Navigation polygons require at least three vertices')
        for p in vertices: vector(p,2,'nav vertex')
        area=abs(sum(vertices[i-1][0]*p[1]-p[0]*vertices[i-1][1] for i,p in enumerate(vertices)))/2
        if area<.1: fail('Navigation polygon has no meaningful area')
        allpoints.extend(vertices)
    minx=min(p[0] for p in allpoints); maxx=max(p[0] for p in allpoints); minz=min(p[1] for p in allpoints); maxz=max(p[1] for p in allpoints)
    if maxx-minx>shell['width']+4 or maxz-minz>shell['depth']+4: fail('Navigation exceeds shell dimensions plus entrance apron allowance')
    for b in nav.get('blockers',[]): bounds(b.get('bounds'),'navigation blocker')
    for seg in nav.get('segments',[]):
        vector(seg.get('a'),2,'segment.a');vector(seg.get('b'),2,'segment.b')
        if not finite(seg.get('thickness')) or not 0<seg['thickness']<2: fail('Segment thickness must be positive and below 2 m')
    for door in c.get('doors',[]):
        vector(door.get('center'),2,'door.center')
        if not finite(door.get('width')) or door['width']<2*rt['playerRadius']+.1: fail('Door must clear the player diameter plus 10 cm')
        if not finite(door.get('height')) or not rt['eyeHeight']<door['height']<=shell['height']: fail('Door height must clear player eye height within ceiling')
        if door.get('axis') not in ('x','z'): fail('door.axis is x or z')
        if not door.get('roomIds') or not set(door['roomIds'])<=ids: fail('Door roomIds must refer to existing rooms')
    furniture_ids=set()
    for item in c.get('furniture',[]):
        if not isinstance(item.get('id'),str) or not item['id'] or item['id'] in furniture_ids: fail('Furniture must have unique string ids')
        furniture_ids.add(item['id'])
        if not item.get('id') or item.get('type') not in ('desk','chair','sofa','shelf','table','plant','box'): fail('Furniture must have id and supported type')
        vector(item.get('position'),3,'furniture.position');vector(item.get('size'),3,'furniture.size')
        if not all(0<v<=200 for v in item['size']): fail('Furniture dimensions must be positive')
        if 'rotation' in item and not finite(item['rotation']): fail('Furniture rotation must be finite radians')
        if 'color' in item and (not isinstance(item['color'],str) or not re.fullmatch('#[0-9a-fA-F]{6}',item['color'])): fail('Furniture color must be a hex color')
        if 'interaction' in item:
            interaction=item['interaction']
            if not isinstance(interaction,dict) or not all(isinstance(interaction.get(key),str) and interaction[key].strip() for key in ('label','message')): fail('Furniture interaction requires non-empty label and message strings')
    materials=c.get('materials',{})
    for name in ('floor','wall'):
        value=materials.get(name)
        if not isinstance(value,str) or not re.fullmatch('#[0-9a-fA-F]{6}',value): fail(f'materials.{name} requires an explicit hex color')
    scene=c.get('scene',{})
    if scene.get('mode') not in ('pearl-v7','procedural','imported-glb'): fail('Scene mode must be pearl-v7, procedural, or imported-glb')
    if 'gameplay' in c:
        gameplay=c['gameplay']
        if scene['mode']=='pearl-v7': fail('Custom gameplay requires a procedural or imported-glb scene')
        if not isinstance(gameplay,dict) or set(gameplay)!={'objectives','completionMessage'}: fail('gameplay requires objectives and completionMessage only')
        if not isinstance(gameplay['completionMessage'],str) or not gameplay['completionMessage'].strip(): fail('gameplay.completionMessage must be a non-empty string')
        objectives=gameplay['objectives']
        if not isinstance(objectives,list) or not objectives: fail('gameplay.objectives must be a non-empty list')
        interactive_ids={item['id'] for item in c['furniture'] if 'interaction' in item}
        objective_ids=set()
        for objective in objectives:
            if not isinstance(objective,dict) or set(objective)!={'id','label','targetId'} or not all(isinstance(objective.get(k),str) and objective[k].strip() for k in ('id','label','targetId')): fail('Each gameplay objective requires id, label and targetId strings')
            if objective['id'] in objective_ids: fail('gameplay objective ids must be unique')
            objective_ids.add(objective['id'])
            if objective['targetId'] not in interactive_ids: fail('gameplay targetId must refer to furniture with an interaction')
    if scene.get('mode')=='imported-glb' and not any(a.get('id')==scene.get('assetId') and a.get('type')=='model' for a in c['assets']): fail('imported-glb scene.assetId must reference a selected model asset')
    asset_ids=set()
    for asset in c.get('assets',[]):
        if asset.get('id') in asset_ids: fail('Asset ids must be unique')
        asset_ids.add(asset.get('id'))
        if not isinstance(asset.get('id'),str) or not asset['id'] or asset.get('type') not in ('image','video','model','document'): fail('Asset requires id and type')
        safe_relative(asset.get('path',''))
        if not re.fullmatch('[a-f0-9]{64}',asset.get('sha256','')): fail('Asset sha256 is required')
        if asset['type']=='model' and not asset['path'].lower().endswith('.glb'): fail('Model assets must use self-contained .glb files')
        if 'placement' in asset:
            if not isinstance(asset['placement'],dict): fail('asset placement must be an object')
            for key in ('position','rotation','scale'): vector(asset['placement'].get(key),3,f'asset placement.{key}')
            if not all(0<v<=100 for v in asset['placement']['scale']): fail('Asset placement scale must be positive and <= 100')
    validate_structural_barriers(c)
    spawn=[nav['spawn'][0],nav['spawn'][2]]
    if not walkable(c,*spawn): fail('Spawn is not walkable with player-radius clearance')
    routes=nav.get('routes',[])
    if not routes: fail('At least one approved walkthrough route is required')
    targets=[]
    for room in rooms:
        pt=room['accessPoint'];a,b,d,e=room['bounds']
        if not a<=pt[0]<=d or not b<=pt[1]<=e: fail(f"Room {room['id']} accessPoint must be inside its declared bounds")
        if not walkable(c,*pt): fail(f"Room {room['id']} accessPoint is not radius-clear and reachable")
        targets.append(pt)
    for route in routes:
        if not route.get('id') or len(route.get('points',[]))<2: fail('A route requires id and at least two points')
        for pt in route['points']:
            vector(pt,2,'route point');targets.append(pt)
            if not walkable(c,*pt): fail(f"Route {route['id']} waypoint is blocked or outside the navigation union: {pt}")
        for a,b in zip(route['points'],route['points'][1:]):
            if not segment_walkable(c,a,b): fail(f"Route {route['id']} crosses a blocked boundary; add doorway waypoints")
    if not connectivity: return {'routePoints':len(targets)}
    step=max(.12,min(.25,rt['playerRadius']))
    nx=math.ceil((maxx-minx)/step)+1;nz=math.ceil((maxz-minz)/step)+1
    if nx*nz>200000: fail('Navigation validation grid exceeds 200,000 cells; split this oversized project')
    cells=set()
    for ix in range(nx):
        for iz in range(nz):
            if walkable(c,minx+ix*step,minz+iz*step): cells.add((ix,iz))
    def nearest(point):
        ix=round((point[0]-minx)/step);iz=round((point[1]-minz)/step)
        candidates=[(a,b) for a in range(ix-2,ix+3) for b in range(iz-2,iz+3) if (a,b) in cells and segment_walkable(c,point,[minx+a*step,minz+b*step])]
        if not candidates: fail(f'No radius-clear navigation grid cell reaches {point}')
        return min(candidates,key=lambda k:(minx+k[0]*step-point[0])**2+(minz+k[1]*step-point[1])**2)
    start=nearest(spawn); reached={start};queue=deque([start])
    while queue:
        a,b=queue.popleft()
        for n in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
            if n in cells and n not in reached:
                if not segment_walkable(c,[minx+a*step,minz+b*step],[minx+n[0]*step,minz+n[1]*step]): continue
                reached.add(n);queue.append(n)
    if len(reached)!=len(cells): fail(f'Navigation is disconnected: {len(cells)-len(reached)} clearance-valid cells cannot reach spawn')
    for pt in targets:
        if nearest(pt) not in reached: fail('An approved route point is unreachable')
    if 'gameplay' in c:
        # Match the runtime's horizontal proximity and first-in-list tie rule.
        # A connected floor alone cannot prove an objective can be activated.
        interactive=[item for item in c['furniture'] if 'interaction' in item]
        remaining={o['targetId'] for o in c['gameplay']['objectives']}
        for ix,iz in reached:
            x,z=minx+ix*step,minz+iz*step
            closest=None;distance=2.15
            for item in interactive:
                d=math.hypot(x-item['position'][0],z-item['position'][2])
                if d<distance: closest=item['id'];distance=d
            remaining.discard(closest)
            if not remaining: break
        if remaining: fail('Gameplay targets have no reachable nearest-interaction approach: '+', '.join(sorted(remaining)))
    return {'walkableCells':len(cells),'connectedCells':len(reached),'gridStepMeters':step,'routePoints':len(targets),'method':'radius-disk samples, segment samples and 4-neighbor grid flood-fill; browser QA still required'}

_VALIDATION_CACHE = {}
def validate_config(c, connectivity=True):
    # Cache only immutable geometry results in this process. Evidence files and
    # source/asset hashes are re-read separately for every lock/build operation.
    try: key=(digest(c),connectivity)
    except (ValueError,TypeError): return _validate_config(c,connectivity)
    if key not in _VALIDATION_CACHE:
        result=_validate_config(c,connectivity)
        if len(_VALIDATION_CACHE)>=16: _VALIDATION_CACHE.clear()
        _VALIDATION_CACHE[key]=result
    return copy.deepcopy(_VALIDATION_CACHE[key])

def cmd_init(args):
    p=pathlib.Path(args.project).expanduser().resolve()
    if p.exists() and any(p.iterdir()): fail('init requires an empty directory')
    p.mkdir(parents=True,exist_ok=True)
    write(p/'project.json',{'version':VERSION,'name':p.name,'example':args.example,'createdAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    write(p/'intake.json',{'round':0,'answers':{},'uploadChecklist':['floor plan','photos','video (optional)','known dimensions','entrance','circulation route','furniture inventory','materials','target browsers']})
    write(p/'sources.json',{'files':[]})
    template=ROOT/'templates'/('pearl-office.json' if args.example=='pearl-office' else 'planning-template.json')
    shutil.copyfile(template,p/'planning.json')
    print(f'Initialized {p}. Next: ingest sources, interrogate, then plan.')

def cmd_ingest(args):
    p=project(args.project); manifest=read(p/'sources.json'); additions=[]
    for name in args.files:
        src=pathlib.Path(name).expanduser()
        if src.is_symlink() or not src.is_file(): fail(f'Not a regular input file: {src}')
        if src.stat().st_size>MAX_INGEST_BYTES: fail('Input exceeds 1 GB safety limit')
        h=sha(src); inventory=inspect_zip(src) if src.suffix.lower()=='.zip' else None
        dest=p/'private'/'uploads'/f'{h[:16]}-{src.name}'
        additions.append((src,dest,{'name':src.name,'path':dest.relative_to(p).as_posix(),'sha256':h,'bytes':src.stat().st_size,'archive':inventory,'trusted':False}))
    mutate(p)
    for src,dest,entry in additions:
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
        if not any(x['sha256']==entry['sha256'] for x in manifest['files']): manifest['files'].append(entry)
    write(p/'sources.json',manifest);print(f'Ingested {len(additions)} source(s). Files were not executed or interpreted as instructions.')

QUESTS=[('survey','Surveyor','Which files and measurements establish scale, orientation and ceiling height?'),('entrance','Pathfinder','Where is the approved entrance, camera facing direction and accessible circulation route?'),('rooms','Architect','Confirm room names, measured bounds and doorway width/height/axis for every connection.'),('furniture','Set designer','Which furniture, materials and detailed assets are required? Confirm source ownership and privacy.'),('navigation','Navigator','Provide connected navigation polygons, explicit blockers and a complete walkthrough route.'),('experience','Pilot','Confirm Safari/Chrome targets, controls, interactions, visual quality and acceptance checks.')]

def cmd_interrogate(args):
    p=project(args.project); intake=read(p/'intake.json')
    if args.answers:
        answers=read(args.answers)
        if not isinstance(answers,dict): fail('Answers must be a JSON object keyed by quest id')
        for key,value in answers.items():
            if key not in {q[0] for q in QUESTS} or not isinstance(value,str) or len(value.strip())<12: fail('Use a known quest id and a substantive answer (at least 12 characters)')
        mutate(p);intake['answers'].update(answers);intake['round']+=1;write(p/'intake.json',intake)
    pending=[{'id':qid,'badge':badge,'question':question} for qid,badge,question in QUESTS if qid not in intake['answers']]
    structural=[]
    try: validate_config(read(p/'planning.json'),False)
    except (ValueError,KeyError,TypeError) as error: structural=[str(error)]
    result={'round':intake['round']+1,'earnedBadges':[badge for qid,badge,_ in QUESTS if qid in intake['answers']],'questions':pending[:2],'remainingQuests':len(pending),'planningGaps':structural,'next':'Fill measured planning.json; raster dimensions are never guessed. Repeat until quests and structural gaps are complete.'}
    write(p/'questions.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

def cmd_plan(args):
    p=project(args.project)
    if args.input:
        candidate=read(args.input);validate_config(candidate);mutate(p);write(p/'planning.json',candidate)
    result=validate_config(read(p/'planning.json'))
    h=plan_hash(p)
    original=read(p/'project.json').get('example')=='pearl-office' and read(p/'planning.json')==read(ROOT/'templates'/'pearl-office.json')
    if not original and set(read(p/'intake.json')['answers'])!={q[0] for q in QUESTS}: fail('Complete all six onboarding quests with interrogate --answers before planning lock')
    write(p/'planning-review.json',{'planHash':h,'validation':result,'approved':False,'review':'Review measured geometry, uploaded evidence, navigation, asset rights and browser targets before approve --accept.'})
    print(f'Planning pack valid. Review {p / "planning.json"}; hash {h}. Next: approve --accept')

def cmd_approve(args):
    p=project(args.project)
    if not args.accept: fail('Explicit approval is required: review planning.json then approve --accept')
    validate_config(read(p/'planning.json'));h=plan_hash(p)
    if not (p/'planning-review.json').exists() or read(p/'planning-review.json').get('planHash')!=h: fail('Run plan after all edits before approving')
    write(p/'approval.json',{'planHash':h,'approvedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'acceptance':'Explicit CLI approval of measured planning pack'})
    print(f'Planning locked: {h}')

def approved(p):
    h=plan_hash(p)
    if not (p/'approval.json').exists() or read(p/'approval.json').get('planHash')!=h: fail('Planning approval is absent or stale; run plan and approve --accept again')
    return h

def runtime_hash():
    files={}
    for path in sorted((ROOT/'runtime').rglob('*')):
        if path.is_symlink(): fail('Runtime symlinks are forbidden')
        if path.is_file(): files[path.relative_to(ROOT/'runtime').as_posix()]=sha(path)
    if not files: fail('Runtime is missing')
    return digest(files)

def build_manifest(directory):
    return {p.relative_to(directory).as_posix():sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p!=directory/'integrity.json'}

def cmd_build(args):
    p=project(args.project);h=approved(p);config=read(p/'planning.json');validate_config(config)
    rh=runtime_hash();build_id=digest({'plan':h,'runtime':rh,'version':VERSION})[:16]
    dest=p/'builds'/build_id
    if dest.exists():
        fail(f'Build already exists: {build_id}. Use play or validate; changed planning/runtime creates a new immutable build.')
    temp=pathlib.Path(tempfile.mkdtemp(prefix='build-',dir=p))
    try:
        shutil.copytree(ROOT/'runtime',temp,dirs_exist_ok=True)
        copied=digest({path.relative_to(temp).as_posix():sha(path) for path in sorted(temp.rglob('*')) if path.is_file()})
        if copied!=rh: fail('Runtime changed while building; retry after source edits finish')
        # Explicitly opt-in assets only: source uploads are never bulk copied.
        for asset in config.get('assets',[]):
            src=local_file(p,asset['path'])
            asset_name=re.sub(r'[^a-zA-Z0-9_-]+','-',asset['id']).strip('-') or 'asset'
            extension=src.suffix.lower() if re.fullmatch(r'\.[a-z0-9]{1,10}',src.suffix.lower()) else '.bin'
            target=temp/'assets'/f"{asset['sha256'][:16]}-{asset_name}{extension}"
            target.parent.mkdir(exist_ok=True);shutil.copyfile(src,target);asset['path']=target.relative_to(temp).as_posix()
        write(temp/'config.json',config)
        write(temp/'build.json',{'buildId':build_id,'planHash':h,'runtimeHash':rh,'version':VERSION,'createdAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
        write(temp/'integrity.json',{'files':build_manifest(temp)})
        verify_build(temp)
        if approved(p)!=h: fail('Planning inputs changed while building; review and approve the changed inputs')
        dest.parent.mkdir(exist_ok=True);temp.rename(dest)
    except Exception:
        shutil.rmtree(temp,ignore_errors=True);raise
    write(p/'current-build.json',{'buildId':build_id,'path':dest.relative_to(p).as_posix()})
    print(f'Built {dest}. Next: validate --build and play')

def current_build(p):
    approved(p)
    if not (p/'current-build.json').exists(): fail('No current build; run build first')
    record=read(p/'current-build.json');dest=(p/record['path']).resolve()
    if not dest.is_relative_to((p/'builds').resolve()) or not dest.is_dir(): fail('Invalid build path')
    metadata=read(dest/'build.json')
    if metadata.get('buildId')!=record.get('buildId') or dest.name!=metadata.get('buildId'): fail('Current build identity does not match its directory and pointer')
    if metadata['planHash']!=plan_hash(p): fail('Build no longer matches the planning lock')
    return dest

def verify_build(dest):
    for path in dest.rglob('*'):
        if path.is_symlink(): fail('Build contains a symlink')
    manifest=read(dest/'integrity.json')['files'];actual=build_manifest(dest)
    if manifest!=actual: fail('Build contents do not match integrity manifest')
    required=['index.html','config.json','build.json']
    for name in required:
        if not (dest/name).is_file(): fail(f'Build is missing {name}')
    config=read(dest/'config.json')
    for asset in config.get('assets',[]):
        path=local_file(dest,asset['path'])
        if sha(path)!=asset['sha256']: fail('Built asset SHA256 mismatch')
        if asset['type']=='model': inspect_glb(path)
    return validate_config(config)

def structural_validation(p,dest=None):
    """Fresh structural evidence, explicitly separate from browser acceptance."""
    config=read(p/'planning.json');result=validate_config(config);h=plan_hash(p);build_id=None
    if dest is not None:
        result['build']=verify_build(dest)
        metadata=read(dest/'build.json')
        if metadata['planHash']!=h: fail('Build no longer matches the planning lock')
        build_id=metadata['buildId']
    return {'passed':True,'evidenceType':'structural','scope':'planning-and-build' if dest is not None else 'planning-only',
            'buildId':build_id,'planHash':h,'generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'result':result,'targetBrowsers':config['runtime']['browsers'],'automatedBrowserEvidence':{'status':'not-supplied'},
            'browserAcceptance':'unverified until manual walkthroughs of declared target browsers are recorded'}

def supplied_browser_evidence(path,validation):
    """Check supplied report consistency; never claim to have rerun its checks."""
    path=pathlib.Path(path).expanduser().resolve()
    if path.stat().st_size>1_000_000: fail('Browser report exceeds the 1 MB limit')
    raw=path.read_bytes();report=json.loads(raw)
    if not isinstance(report,dict) or report.get('passed') is not True: fail('Browser report must declare passed: true')
    if report.get('buildId')!=validation['buildId']: fail('Browser report buildId does not match the packaged build')
    if 'planHash' in report and report['planHash']!=validation['planHash']: fail('Browser report planHash does not match the packaged build')
    checks=report.get('checks')
    if not isinstance(checks,list) or not checks: fail('Browser report must contain nonempty checks')
    for check in checks:
        if not isinstance(check,dict) or not isinstance(check.get('check'),str) or not check['check'].strip(): fail('Browser report contains an invalid check')
        if 'passed' in check and check['passed'] is not True: fail('Browser report contains a failed check')
    for field in ('errors','externalRequests'):
        if field in report and report[field]!=[]: fail(f'Browser report contains {field}')
    if 'final' in report:
        final=report['final']
        if not isinstance(final,dict): fail('Browser report final snapshot is invalid')
        if 'buildId' in final and final['buildId']!=validation['buildId']: fail('Browser report final buildId does not match the packaged build')
        if final.get('errors',[])!=[]: fail('Browser report final snapshot contains errors')
    metadata={'status':'supplied','evidenceType':'supplied-automated-browser-report',
              'file':'browser-report.json','sha256':hashlib.sha256(raw).hexdigest(),
              'buildId':report['buildId'],'planHashPresent':'planHash' in report,
              'limitations':['Supplied report checked for consistency; browser checks were not rerun by package.',
                             'Automated evidence does not establish manual acceptance for declared target browsers.']}
    for field in ('browser','browserVersion'):
        if field in report:
            if not isinstance(report[field],str) or not report[field].strip(): fail(f'Browser report {field} must be a nonempty string')
            metadata[field]=report[field]
    return raw,metadata

def cmd_validate(args):
    p=project(args.project);report=structural_validation(p,current_build(p) if args.build else None)
    write(p/'validation.json',report)
    print(json.dumps(report,indent=2))

class BuildHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript','.mjs':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def end_headers(self):
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path)
        if parsed.path=='/__build':
            data=json.dumps(self.server.metadata).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if parsed.path in ('/','/index.html'):
            expected=urllib.parse.parse_qs(parsed.query).get('build',[None])[0]
            if expected!=self.server.metadata['buildId']:
                self.send_error(409,'Build id absent or stale; open the exact launcher URL');return
        super().do_GET()
    def list_directory(self,path): self.send_error(403,'Directory listing disabled');return None
    def log_message(self,format,*args): pass

def make_server(dest,port=0):
    verify_build(dest)
    handler=lambda *a,**kw:BuildHandler(*a,directory=str(dest),**kw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),handler)
    server.metadata={**read(dest/'build.json'),'port':server.server_port}
    return server

def cmd_play(args):
    p=project(args.project);dest=current_build(p);server=make_server(dest,args.port)
    url=f"http://127.0.0.1:{server.server_port}/?build={server.metadata['buildId']}"
    print(f'Fresh server: {url}\nBuild {server.metadata["buildId"]}. Stop with Ctrl+C.',flush=True)
    if not args.no_open:
        if args.browser and sys.platform=='darwin':
            import subprocess
            subprocess.run(['open','-a','Safari' if args.browser=='safari' else 'Google Chrome',url],check=False)
        else: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

def cmd_package(args):
    p=project(args.project);dest=current_build(p)
    expected={**read(dest/'integrity.json')['files'],'integrity.json':sha(dest/'integrity.json')}
    report=structural_validation(p,dest)
    output=pathlib.Path(args.output).expanduser().resolve() if args.output else p/f'{dest.name}-playable.zip'
    if output.exists(): fail('Output exists; choose a new ZIP path')
    if output.is_relative_to(dest): fail('Package output must be outside the immutable build directory')
    browser_report=None
    if getattr(args,'browser_report',None):
        browser_report,report['automatedBrowserEvidence']=supplied_browser_evidence(args.browser_report,report)
    licenses=[local_file(ROOT,name) for name in ('LICENSE','THIRD_PARTY_NOTICES.md')]
    output.parent.mkdir(parents=True,exist_ok=True)
    handle,staging=tempfile.mkstemp(prefix='.playable-',suffix='.zip.tmp',dir=output.parent)
    os.close(handle);staging=pathlib.Path(staging)
    try:
        with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(dest.rglob('*')):
                if path.is_symlink(): fail('Cannot package symlinks')
                if path.is_file(): z.write(path,'runtime/'+path.relative_to(dest).as_posix())
            for license_file in licenses: z.write(license_file,license_file.name)
            z.writestr('validation.json',json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
            if browser_report is not None: z.writestr('browser-report.json',browser_report)
            z.writestr('README.txt','Local playable build. Requires Python 3.9+ and a WebGL-capable browser. Run python3 launch.py; open the exact printed URL. Use python3 launch.py --no-open to serve without opening a browser. Source uploads are excluded. Explicit assets in config are included: review ownership before sharing. validation.json contains fresh structural evidence and the declared target browsers for this exact build. Optional browser-report.json is supplied automated evidence; manual acceptance for declared target browsers remains unverified. See LICENSE and THIRD_PARTY_NOTICES.md for distribution terms.\n')
            launcher=ROOT/'scripts'/'package_launcher.py';z.write(launcher,'launch.py')
        entries=inspect_zip(staging)['files']
        packaged={entry['path'][len('runtime/'):]:entry['sha256'] for entry in entries if entry['path'].startswith('runtime/')}
        if packaged!=expected: fail('Build changed while packaging; package integrity verification failed')
        if current_build(p)!=dest: fail('Current build changed while packaging')
        # Publish complete bytes atomically without replacing a concurrently created file.
        os.link(staging,output)
    finally:
        staging.unlink(missing_ok=True)
    print(f'Packaged {output}. Private uploads excluded; explicitly selected assets included.')

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    for name in ('init','ingest','interrogate','plan','approve','build','validate','play','package'):
        s=sub.add_parser(name);s.add_argument('project');s.set_defaults(func=globals()['cmd_'+name])
        if name=='init':s.add_argument('--example',choices=['pearl-office'])
        if name=='ingest':s.add_argument('files',nargs='+')
        if name=='interrogate':s.add_argument('--answers')
        if name=='plan':s.add_argument('--input')
        if name=='approve':s.add_argument('--accept',action='store_true')
        if name=='validate':s.add_argument('--build',action='store_true')
        if name=='play':s.add_argument('--no-open',action='store_true');s.add_argument('--port',type=int,default=0);s.add_argument('--browser',choices=['safari','chrome'])
        if name=='package':
            s.add_argument('--output')
            s.add_argument('--browser-report',help='Include supplied automated browser evidence for this exact build')
    args=parser.parse_args(argv)
    try: args.func(args);return 0
    except (ValueError,KeyError,TypeError,OSError,zipfile.BadZipFile,json.JSONDecodeError) as error:
        print(f'ERROR: {error}',file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
