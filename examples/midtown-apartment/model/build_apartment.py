"""Local authored apartment, using the owner's accepted V1 and clearance fixes.
Run Blender --background --python this_file -- --output OUTPUT_DIRECTORY.
No downloaded assets, reference-photo pixels, paid services or network access.
"""
import argparse, hashlib, json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--renders',action='store_true')
opts=parser.parse_args(args);OUT=Path(opts.output).resolve();OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'apartment.blend').exists() or (OUT/'apartment.glb').exists():raise RuntimeError('Use a fresh output directory; keep prior assets immutable.')
D=json.loads((ROOT/'layout-build.json').read_text());H=D['scale']['height'];random.seed(21)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
def rgb(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)
def mat(name,color,rough=.55,metal=0,emit=0,alpha=1):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');c=rgb(color)
    p.inputs['Base Color'].default_value=(*c,alpha);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
    p.inputs['Alpha'].default_value=alpha
    if alpha<1:
        m.surface_render_method='DITHERED'
        if hasattr(m,'use_transparent_shadow'):m.use_transparent_shadow=True
    m.diffuse_color=(*c,alpha);return m
M={n:mat(n,c,r,met) for n,c,r,met in [
    ('wall','#e0e3df',.85,0),('ceiling','#f2f0e8',.85,0),('trim','#f3f2eb',.6,0),
    ('wood','#ac8058',.55,0),('darkwood','#685341',.6,0),('oak','#c5a77f',.65,0),
    ('fabric','#b7baad',.9,0),('linen','#e9e2d1',.95,0),('blanket','#688b84',.92,0),
    ('pillow','#f6f1e5',.95,0),('cushion','#b96e49',.9,0),('stone','#edeae0',.35,0),
    ('tile','#cbd0ca',.65,0),('metal','#aab2b2',.3,.8),('black','#222c30',.4,.4),
    ('porcelain','#eeeae2',.25,0),('basin','#80989a',.3,.2),('leaf','#42735d',.8,0),
    ('pot','#b38864',.7,0),('rug','#d8c8ad',.95,0),('rubber','#3b4847',.7,0)]}
M['glass']=mat('window-glass','#c0d8dd',.15,.0,0,.12)
M['screen']=mat('TV inactive screen','#050b10',.3,0,0)
M['bulb']=mat('Bedside inactive shade','#ddd2af',.8,0,0)
M['fixture']=mat('warm ceiling diffuser','#fff0ca',.7,0,.5)
CURRENT='';groups={};shell_objects=[];ceiling_objects=[];opening_audit=[]
def tag(o,name,material):
    o.name=name
    if material:o.data.materials.append(material)
    if CURRENT:o['furnitureId']=CURRENT;groups.setdefault(CURRENT,[]).append(o)
    return o
def box(name,x,z,y,w,d,h,material,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-z,y));o=tag(bpy.context.object,name,material);o.dimensions=(w,d,h)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('soft edges','BEVEL');mod.width=min(bevel,w/4,d/4,h/4);mod.segments=2
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
        o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return o
def cyl(name,x,z,y,r,depth,material,axis='y',vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=(x,-z,y));o=tag(bpy.context.object,name,material)
    if axis=='z':o.rotation_euler[0]=math.pi/2
    if axis=='x':o.rotation_euler[1]=math.pi/2
    for p in o.data.polygons:p.use_smooth=True
    return o
def ball(name,x,z,y,sx,sz,sy,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=(x,-z,y));o=tag(bpy.context.object,name,material);o.scale=(sx,sz,sy)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o
def tube(name,a,b,r,material):
    aa=Vector((a[0],-a[1],a[2]));bb=Vector((b[0],-b[1],b[2]));v=bb-aa
    o=cyl(name,(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2,r,v.length,material)
    o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o
def slab(name,poly,y,thickness,material):
    n=len(poly);verts=[(x,-z,y+v) for v in (0,-thickness) for x,z in poly]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);tag(o,name,material)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
    return o
def cut(wall,center,size,label):
    x,z,y=center;w,d,h=size;c=box('Cutter_'+label,x,z,y,w,d,h,None)
    bpy.context.view_layer.objects.active=wall;m=wall.modifiers.new(label,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c
    bpy.ops.object.modifier_apply(modifier=m.name)
    if CURRENT:groups[CURRENT].remove(c)
    bpy.data.objects.remove(c,do_unlink=True)
    opening_audit.append({'id':label,'wall':wall.name,'center':center,'dimensions':size,'appliedBoolean':True})
def wall_run(name,a,b,doors=(),windows=()):
    axis='x' if abs(a[1]-b[1])<.001 else 'z';length=math.dist(a,b)
    w=length if axis=='x' else .12;d=.12 if axis=='x' else length
    o=box(name,(a[0]+b[0])/2,(a[1]+b[1])/2,H/2,w,d,H,M['wall']);shell_objects.append(o)
    for opening in doors:
        x,z=opening['center'];width=opening['width'];height=opening['height']
        cut(o,[x,z,height/2],[width if axis=='x' else .4,.4 if axis=='x' else width,height+.01],opening['id'])
        # Frames sit outside the clear aperture; they never shrink the planned gap.
        for s in (-1,1):
            box(opening['id']+' jamb',x+s*(width/2+.025) if axis=='x' else x,z if axis=='x' else z+s*(width/2+.025),height/2,.05 if axis=='x' else .16,.16 if axis=='x' else .05,height,M['trim'],.008)
        box(opening['id']+' lintel',x,z,height+.025,width+.10 if axis=='x' else .16,.16 if axis=='x' else width+.10,.05,M['trim'],.008)
    for i,(lo,hi,sill,head) in enumerate(windows):
        cx=(lo+hi)/2;cut(o,[cx,a[1],(sill+head)/2],[hi-lo,.4,head-sill],name+' window '+str(i))
        for x in (lo,hi,(lo+hi)/2):box('Window mullion',x,a[1],(sill+head)/2,.045,.10,head-sill,M['black'])
        for y in (sill,head):box('Window rail',cx,a[1],y,hi-lo+.07,.11,.045,M['black'])
        box('Window sill',cx,a[1]+.035,sill-.025,hi-lo+.12,.24,.05,M['trim'],.01)
        box('Window glazing',cx,a[1]-.015,(sill+head)/2,hi-lo,.01,head-sill,M['glass'])
    return o

# Sealed substrates. Plank seams are shallow surface geometry, not open flooring.
slab('Interior floor substrate',D['interiorOutline'],0,.12,M['oak'])
slab('Balcony slab',D['balconyOutline'],-.005,.15,M['tile'])
ceil=slab('Ceiling substrate',D['interiorOutline'],H+.12,.12,M['ceiling']);ceiling_objects.append(ceil)
def inside(x,z,poly):
    odd=False
    for i,a in enumerate(poly):
        b=poly[i-1]
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:odd=not odd
    return odd
plank_materials=[mat('Oak tone '+str(i),c,.72) for i,c in enumerate(['#bea17e','#c7ac89','#b99c79','#ccb291'])]
for j in range(49):
    z=.10+j*.195
    for i in range(10):
        x=.52+i*1.3+(j%3)*.42
        if all(inside(x+sx*.64,z+sz*.09,D['interiorOutline']) for sx in (-1,1) for sz in (-1,1)):
            tone=random.choice(plank_materials)
            box('Oak floorboard',x,z,.003,1.28,.187,.006,tone,.002)
for room in D['rooms']:
    if room['id'] not in ('primary-bath','bath','kitchen'):continue
    x1,z1,x2,z2=room['bounds']
    box(room['id']+' floor', (x1+x2)/2,(z1+z2)/2,.008,x2-x1,z2-z1,.016,M['tile'])
    for i in range(math.ceil((x2-x1)/.48)):
        for j in range(math.ceil((z2-z1)/.48)):
            w=min(.472,x2-x1-i*.48-.008);d=min(.472,z2-z1-j*.48-.008)
            if min(w,d)>0:box('Tile',x1+i*.48+w/2+.004,z1+j*.48+d/2+.004,.02,w,d,.012,M['stone'])
doors=D['openings'];get=lambda i:next(d for d in doors if d['id']==i)
wall_run('North facade',[.75,0],[11.7,0],[get('balcony-door')],[(.8,3.1,.82,2.38),(3.9,6.55,.82,2.38),(7.8,10.15,.82,2.38)])
outline=D['interiorOutline']
for i,a in enumerate(outline):
    b=outline[(i+1)%len(outline)]
    if a[1]==b[1]==0:continue
    wall_run('Exterior '+str(i),a,b,[get('entry')] if a[1]==b[1]==9.6 else [])
runs=[('Primary east',[3.6,0],[3.6,6.4],[]),('Primary entrance',[1.65,6.4],[3.6,6.4],[get('primary-door')]),
      ('Bedroom east',[7.45,0],[7.45,6.0],[]),('Bedroom entrance',[3.6,5.1],[7.45,5.1],[get('bedroom-door')]),
      ('Living return',[6.85,6.0],[7.6,6.0],[]),('Primary bath north',[1.05,7.45],[3.6,7.45],[get('primary-bath-door')]),
      ('Primary bath east',[3.6,7.45],[3.6,9.2],[]),('Bath north',[3.8,7.45],[6.15,7.45],[get('bath-door')]),
      ('Bath west',[3.8,7.45],[3.8,9.2],[]),('Bath east',[6.15,7.45],[6.15,9.2],[])]
for name,a,b,op in runs:wall_run(name,a,b,op)
# Baseboards use exactly the collision wall spans and keep every door gap clear.
for s in D['navigation']['segments']:
    if s['id'].startswith('railing'):continue
    a,b=s['a'],s['b'];axis='x' if abs(a[1]-b[1])<.001 else 'z'
    box('Skirting '+s['id'],(a[0]+b[0])/2,(a[1]+b[1])/2,.065,math.dist(a,b) if axis=='x' else .15,.15 if axis=='x' else math.dist(a,b),.13,M['trim'])
box('Closed entrance door',7.85,9.59,1.065,.98,.06,2.13,M['darkwood'],.01)
cyl('Entrance handle',8.20,9.54,1.04,.035,.08,M['metal'],'z')
for i,a in enumerate(D['balconyOutline']):
    b=D['balconyOutline'][(i+1)%len(D['balconyOutline'])]
    if a[1]==b[1]==0:continue
    tube('Balcony handrail',[*a,1.1],[*b,1.1],.035,M['metal']);tube('Balcony lower rail',[*a,.12],[*b,.12],.02,M['black'])
    steps=max(1,math.ceil(math.dist(a,b)/.30))
    for j in range(steps+1):
        x=a[0]+(b[0]-a[0])*j/steps;z=a[1]+(b[1]-a[1])*j/steps;tube('Balcony baluster',[x,z,.1],[x,z,1.1],.014,M['black'])

def legs(name,x,z,w,d,h,material):
    for sx in (-1,1):
        for sz in (-1,1):box(name+' leg',x+sx*(w/2-.065),z+sz*(d/2-.065),h/2,.045,.045,h,material,.005)
def table(name,x,z,w,d,h):
    box(name+' top',x,z,h-.045,w,d,.09,M['wood'],.025);legs(name,x,z,w,d,h-.09,M['black'])
def chair(name,x,z,w,d,h,back):
    seat=.44;box(name+' cushion',x,z,seat,w,d,.10,M['fabric'],.04);legs(name,x,z,w-.035,d-.035,seat-.05,M['darkwood'])
    if back in ('w','e'):box(name+' back',x+(-1 if back=='w' else 1)*(w/2-.035),z,(seat+h)/2,.07,d,h-seat,M['fabric'],.03)
    else:box(name+' back',x,z+(-1 if back=='n' else 1)*(d/2-.035),(seat+h)/2,w,.07,h-seat,M['fabric'],.03)
def cabinet(name,x,z,w,d,h,front='s',material=None):
    material=material or M['darkwood'];box(name+' carcass',x,z,h/2,w,d,h,material,.018)
    n=max(1,round((w if front in ('s','n') else d)/.55))
    for i in range(n):
        if front in ('s','n'):
            xx=x-w/2+(i+.5)*w/n;zz=z+(1 if front=='s' else -1)*(d/2+.004)
            box(name+' panel',xx,zz,h*.53,w/n-.018,.018,h*.85,material,.01)
            box(name+' handle',xx+w/n*.32,zz+(1 if front=='s' else -1)*.02,h*.62,.016,.022,.13,M['metal'],.006)
        else:
            zz=z-d/2+(i+.5)*d/n;xx=x+(1 if front=='e' else -1)*(w/2+.004)
            box(name+' panel',xx,zz,h*.53,.018,d/n-.018,h*.85,material,.008)
            box(name+' handle',xx+(1 if front=='e' else -1)*.02,zz+d/n*.31,h*.62,.02,.016,.13,M['metal'],.005)
def plant(name,x,z,h):
    cyl(name+' pot',x,z,.16,.17,.32,M['pot']);cyl(name+' soil',x,z,.322,.155,.01,M['darkwood'])
    for i in range(10):
        a=i*2.4;r=.05+(i%3)*.04;y=.4+(h-.5)*i/10
        tube(name+' stem',[x,z,.31],[x+r*math.cos(a),z+r*math.sin(a),y],.008,M['leaf'])
        o=ball(name+' leaf',x+r*math.cos(a),z+r*math.sin(a),y,.14,.055,.045,M['leaf']);o.rotation_euler[2]=a
for f in D['furniture']:
    CURRENT=f['id'];name=CURRENT;kind=f['kind'];x,_,z=f['position'];w,h,d=f['size']
    if kind=='bed':
        legs(name,x,z,w-.08,d-.08,.16,M['darkwood']);box(name+' upholstered frame',x,z,.25,w,d,.25,M['fabric'],.055)
        box(name+' mattress',x,z,.46,w-.06,d-.06,.22,M['linen'],.055)
        west=f['frontYaw']<0;hx=x+(-1 if west else 1)*(w/2-.04)
        box(name+' headboard',hx,z,.68,.11,d+.015,1.05,M['fabric'],.04)
        for s in (-1,1):box(name+' pillow',hx+(1 if west else -1)*.34,z+s*d*.24,.64,.44,d*.41,.15,M['pillow'],.06)
        box(name+' folded duvet',x+( .25 if west else -.25),z,.608,w*.58,d-.045,.075,M['blanket'],.03)
        for j in range(6):box(name+' linen seam',x+( .25 if west else -.25),z-d*.44+j*d*.175,.648,w*.55,.012,.008,M['linen'])
    elif kind=='sofa':
        legs(name,x,z,w,d,.14,M['black']);box(name+' base',x,z,.28,w,d,.3,M['fabric'],.05)
        box(name+' back',x-w/2+.1,z,.60,.20,d,.52,M['fabric'],.06)
        for s in (-1,1):box(name+' arm',x,z+s*(d/2-.095),.49,w,.19,.46,M['fabric'],.06)
        for i in range(3):box(name+' seat',x+.04,z-d/2+.27+(i+.5)*(d-.54)/3,.48,w-.24,(d-.58)/3,.16,M['linen'],.05)
        for zz in (-.85,.8):box(name+' scatter cushion',x-.19,z+zz,.69,.22,.43,.40,M['cushion'],.06)
    elif kind in ('table','desk'):
        table(name,x,z,w,d,h)
        if 'nightstand' in name:
            box(name+' drawer',x,z,h-.19,w-.03,d-.03,.20,M['wood'],.015)
            if name=='primary-nightstand-s':
                cyl('Lamp base',x,z,h+.025,.12,.05,M['metal']);cyl('Lamp stem',x,z,h+.20,.018,.32,M['metal'])
                bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.18,radius2=.12,depth=.24,location=(x,-z,h+.45));tag(bpy.context.object,'BedsideBulb',M['bulb'])
            else:cyl(name+' ceramic vase',x,z,h+.10,.06,.20,M['porcelain'])
        if name=='secondary-desk':
            box('Notebook',x,z,h+.017,.40,.30,.034,M['blanket'],.008);cyl('Pencil pot',x,z+.36,h+.08,.05,.16,M['pot'])
        if name=='coffee-table':
            box('Coffee book',x,z+.18,h+.02,.35,.28,.04,M['blanket']);cyl('Coffee cup',x,z-.20,h+.05,.046,.10,M['porcelain'])
        if name=='dining-table':
            for zz in (-.16,.16):cyl('Dinner plate',x,z+zz,h+.014,.13,.02,M['porcelain'])
            cyl('Dining centerpiece',x+.36,z,h+.10,.07,.20,M['pot'])
    elif kind=='chair':
        back={'secondary-chair':'e','dining-chair-n':'n','dining-chair-s':'s','dining-chair-w':'w','dining-chair-e':'e','balcony-chair-w':'w','balcony-chair-e':'e'}.get(name,'s')
        chair(name,x,z,w,d,h,back)
    elif kind in ('cabinet','wardrobe'):
        front='w' if name in ('tv-console','primary-dresser') else 'e' if name in ('primary-wardrobe','entry-closet','hall-closet') else 's'
        cabinet(name,x,z,w,d,h,front)
    elif kind=='tv':
        box('TV frame',x-.018,z,1.28,.09,d,.83,M['black'],.014)
        screen=box('TVScreen',x-.067,z,1.28,.012,d-.08,.74,M['screen'],.004)
        tube('TV wall bracket',[x+.012,z,1.28],[11.65,z,1.28],.025,M['black'])
        # Welcome lettering is authored local mesh geometry, not an external image.
        curve=bpy.data.curves.new('Welcome label','FONT');curve.body='WELCOME\nHOME';curve.align_x='CENTER';curve.size=.105;curve.space_line=1.15;curve.extrude=.0008
        text=bpy.data.objects.new('TV welcome lettering',curve);bpy.context.collection.objects.link(text);text.location=(x-.079,-z,1.37);text.rotation_euler=(math.pi/2,0,-math.pi/2);text.data.materials.append(M['trim'])
        bpy.ops.object.select_all(action='DESELECT');text.select_set(True);bpy.context.view_layer.objects.active=text;bpy.ops.object.convert(target='MESH');groups.setdefault(CURRENT,[]).append(bpy.context.object)
    elif kind=='rug':box(name,x,z,.018,w,d,.012,M['rug'],.01)
    elif kind=='hvac':
        box(name,x,z,h/2,w,d,h,M['trim'],.02)
        for i in range(9):box(name+' vent',x-w*.42+i*w*.105,z+d/2+.005,.23,w*.065,.01,.18,M['rubber'])
        box(name+' upper grille',x,z,h+.003,w-.10,d-.07,.006,M['rubber'])
    elif kind=='counter':
        cabinet(name,x,z,w,d,h-.045,'n');box(name+' quartz',x,z,h-.015,w+.04,d+.045,.05,M['stone'],.01)
    elif kind=='range':
        cabinet(name,x,z,w,d,h,'s',M['metal']);box('Oven glass',x,z+d/2+.024,.48,w-.11,.02,.45,M['black'],.02)
        box('Range cooktop',x,z,h+.012,w-.025,d-.025,.024,M['black'])
        for sx in (-1,1):
            for sz in (-1,1):
                xx=x+sx*w*.25;zz=z+sz*d*.24;cyl('Burner',xx,zz,h+.035,.09,.025,M['metal'])
                box('Burner grate',xx,zz,h+.06,.23,.022,.025,M['black']);box('Burner grate',xx,zz,h+.06,.022,.23,.025,M['black'])
        for i in range(4):cyl('Range dial',x-w*.32+i*w*.21,z+d/2+.035,h-.1,.034,.026,M['black'],'z')
        cabinet('Microwave cabinet',x,z,w,.40,.52,'s');o=groups[CURRENT][-1]
        # Upper cabinet built separately above the stove; avoid a second floor-level box.
        for o in list(groups[CURRENT]):
            if o.name.startswith('Microwave cabinet'):o.location.z+=1.70
        box('Microwave front',x,z+.22,1.98,w-.08,.08,.35,M['metal'],.015);box('Microwave window',x-.06,z+.265,1.98,w-.24,.012,.25,M['black'])
    elif kind=='fridge':
        box(name+' body',x,z,h/2,w,d,h,M['metal'],.025)
        for sx in (-1,1):
            box(name+' upper door',x+sx*w*.245,z-d/2-.013,h*.68,w*.485,.036,h*.61,M['metal'],.015)
            box(name+' handle',x+sx*.045,z-d/2-.048,h*.68,.022,.05,h*.38,M['black'],.008)
        box(name+' freezer',x,z-d/2-.017,h*.18,w-.025,.04,h*.31,M['metal'],.015)
        box(name+' freezer handle',x,z-d/2-.055,h*.26,w*.67,.035,.025,M['black'],.006)
    elif kind in ('dishwasher','sink'):
        cabinet(name,x,z,w,d,h-.035,'n',M['metal'] if kind=='dishwasher' else M['darkwood'])
        box(name+' counter',x,z,h,w+.015,d+.02,.045,M['stone'],.01)
        if kind=='sink':
            top=groups[CURRENT][-1];cut(top,[x,z,h],[.49,.36,.12],'Kitchen sink cutout')
            carcass=next(o for o in groups[CURRENT] if o.name.startswith(name+' carcass'))
            cut(carcass,[x,z,h-.07],[.49,.36,.25],'Kitchen cabinet sink recess')
            box('Sink well',x,z,h-.09,.48,.35,.06,M['basin'],.025)
            tube('Kitchen tap riser',[x,z+.21,h],[x,z+.21,h+.30],.018,M['metal']);tube('Kitchen tap spout',[x,z+.21,h+.30],[x,z+.03,h+.30],.018,M['metal'])
            cabinet('Kitchen upper',x,z,w,.31,.63,'n')
            for o in groups[CURRENT]:
                if o.name.startswith('Kitchen upper'):o.location.z+=1.72
    elif kind=='laundry':
        for y in (.47,1.42):
            box(name+' machine',x,z,y,w,d,.91,M['trim'],.025)
            # Machines face east toward the foyer.
            cyl(name+' door rim',x+w/2+.012,z,y-.04,.26,.026,M['metal'],'x',24)
            cyl(name+' door glass',x+w/2+.030,z,y-.04,.21,.028,M['black'],'x',24)
            box(name+' controls',x+w/2+.015,z,y+.31,.023,.55,.10,M['metal']);cyl(name+' dial',x+w/2+.035,z+.15,y+.31,.037,.026,M['black'],'x')
    elif kind=='tub':
        body=box(name,x,z,h/2,w,d,h,M['porcelain'],.035);cut(body,[x,z,h/2+.12],[w-.16,d-.20,h],'Bath interior')
        box(name+' bottom',x,z,.12,w-.15,d-.19,.075,M['porcelain'],.04)
        cyl(name+' drain',x,z-d*.3,.16,.027,.012,M['metal']);tube(name+' faucet',[x,z+d*.39,h],[x,z+d*.39,h+.18],.015,M['metal'])
    elif kind=='vanity':
        cabinet(name,x,z,w,d,h-.03,'n');top=box(name+' basin top',x,z,h-.015,w+.015,d+.025,.06,M['porcelain'],.035)
        cut(top,[x,z,h],[w*.6,d*.6,.12],name+' basin cutout')
        carcass=next(o for o in groups[CURRENT] if o.name.startswith(name+' carcass'))
        cut(carcass,[x,z,h-.07],[w*.6,d*.6,.25],name+' cabinet recess')
        box(name+' basin',x,z,h-.07,w*.59,d*.59,.06,M['basin'],.02)
        tube(name+' tap',[x,z+.15,h],[x,z+.15,h+.14],.012,M['metal'])
        box(name+' mirror frame',x,z+.24,1.5,w+.08,.055,.76,M['darkwood'],.02);box(name+' mirror',x,z+.207,1.5,w,.008,.68,M['metal'])
    elif kind=='toilet':
        ball(name+' pedestal',x,z,.18,.16,.21,.18,M['porcelain']);ball(name+' bowl',x,z-.06,.41,w*.49,d*.39,.15,M['porcelain'])
        box(name+' cistern',x,z+d*.31,.48,w*.82,.18,.50,M['porcelain'],.025);cyl(name+' flush',x+.11,z+d*.31,.735,.022,.016,M['metal'])
        ball(name+' seat rim',x,z-.10,.53,.21,.25,.025,M['trim']);ball(name+' seat inset',x,z-.10,.547,.13,.17,.006,M['basin'])
    elif kind=='plant':plant(name,x,z,h)
    elif kind=='round-table':
        cyl(name+' top',x,z,h-.025,w/2,.05,M['wood'],vertices=24);cyl(name+' stem',x,z,h/2,.035,h-.06,M['black']);cyl(name+' foot',x,z,.035,.18,.07,M['black'])
    else:box(name,x,z,h/2,w,d,h,M['wood'])
CURRENT=''

# Authored wall art, lighting fixtures and abstract city context.
box('Living art frame',7.53,3.1,1.61,.045,1.35,.76,M['darkwood'],.01)
box('Living artwork',7.557,3.1,1.61,.008,1.23,.64,M['blanket'])
for i in range(3):box('Abstract art mark',7.564,2.75+i*.34,1.58+.10*(i%2),.006,.14,.32,M['linen'])
for room in D['rooms']:
    if room['id']=='balcony':continue
    x1,z1,x2,z2=room['bounds'];x=(x1+x2)/2;z=(z1+z2)/2
    rose=cyl('Ceiling rose '+room['id'],x,z,H-.014,.18,.028,M['trim'],vertices=24);diff=cyl('Ceiling diffuser '+room['id'],x,z,H-.042,.15,.035,M['fixture'],vertices=24);ceiling_objects.extend([rose,diff])
    light=bpy.data.lights.new('Preview light '+room['id'],'AREA');light.energy=110 if room['id'] not in ('primary-bath','bath') else 65;light.shape='DISK';light.size=2.0
    ob=bpy.data.objects.new(light.name,light);bpy.context.collection.objects.link(ob);ob.location=(x,-z,H-.13)
sky=mat('Context sky','#b8cfda',1,0,.8);box('Context sky backdrop',5,-75,25,140,1,100,sky)
cityM=[mat('City facade '+str(i),c,.8) for i,c in enumerate(['#8f9ca2','#a8afa9','#6a8089','#b0a599'])]
for i in range(18):
    x=-25+(i%9)*7.2;z=-14-(i//9)*19;hh=random.uniform(16,40);w=random.uniform(4,6)
    box('Context building '+str(i),x,z,hh/2-15,w,6,hh,cityM[i%4])
    for floor in range(int(hh/2.5)):
        for col in range(3):box('Context window',x-w*.30+col*w*.30,z+3.006,-13+floor*2.5,w*.16,.025,1.25,M['basin'])

# Merge static per-furniture pieces; retain the two independently addressed meshes.
protected={'TVScreen','BedsideBulb'}
for name,objects in groups.items():
    objects=[o for o in objects if o.name in bpy.data.objects and o.type=='MESH' and o.name not in protected]
    if not objects:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name='Furniture_'+name
    bpy.context.object['furnitureId']=name
# Merge surface tiles/planks to reduce scene graph cost, retaining material colours.
for prefix in ('Oak floorboard','Tile','Context window','Balcony baluster','Skirting'):
    objects=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(prefix)]
    if not objects:continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name=prefix+' assembly'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(*rgb('#c6d9e3'),1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for engine in ['BLENDER_EEVEE','BLENDER_EEVEE_NEXT']:
    try:scene.render.engine=engine;break
    except TypeError:pass
scene.render.resolution_x=1100;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
def camera(name,position,target,ortho=None):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    x,z,y=position;tx,tz,ty=target;ob.location=(x,-z,y);ob.rotation_euler=(Vector((tx,-tz,ty))-ob.location).to_track_quat('-Z','Y').to_euler()
    data.lens=21;data.clip_start=.04;data.clip_end=200
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return ob
cameras={
 'living':camera('Living room view',[10.65,6.15,1.65],[9.7,2.3,1.15]),
 'primary':camera('Primary bedroom view',[3.0,5.05,1.65],[1.0,2.8,.95]),
 'kitchen':camera('Kitchen view',[7.9,7.8,1.65],[10.6,8.25,1.15]),
 'ceiling':camera('Ceiling view',[9.7,3.5,1.65],[9.7,3.5,2.65]),
 'floorplan':camera('Orthographic furnished plan',[5.85,4.0,22],[5.85,4.0,0],14.1),
}
scene.camera=cameras['living']
bpy.ops.object.select_all(action='DESELECT')
for name in protected:
    o=bpy.data.objects.get(name)
    if not o or o.type!='MESH':raise RuntimeError('Missing interactive mesh '+name)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'apartment.blend'))
allowed={p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
export=dict(filepath=str(OUT/'apartment.glb'),export_format='GLB',export_yup=True,export_apply=True,export_lights=False,export_cameras=False,export_extras=True)
bpy.ops.export_scene.gltf(**{k:v for k,v in export.items() if k in allowed})
deps=bpy.context.evaluated_depsgraph_get();meshcount=0;triangles=0
for o in scene.objects:
    if o.type=='MESH':
        meshcount+=1;e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();triangles+=len(m.loop_triangles);e.to_mesh_clear()
audit={'blender':bpy.app.version_string,'layoutSha256':hashlib.sha256((ROOT/'layout-build.json').read_bytes()).hexdigest(),
       'glbSha256':hashlib.sha256((OUT/'apartment.glb').read_bytes()).hexdigest(),'meshObjects':meshcount,'triangles':triangles,
       'furnitureIds':sorted(groups),'interactiveMeshes':sorted(protected),'appliedOpeningCuts':opening_audit,
       'coordinateMapping':'Blender (x,-planZ,height), glTF Y-up => runtime (x,height,planZ)',
       'assets':'Entirely locally authored geometry and materials; no photo pixels or external assets',
       'knownLimits':['accepted approximate dimensions','context buildings are an abstract city backdrop','GLB uses material colour variation rather than photo textures']}
(OUT/'model-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
if opts.renders:
    for name,cam in cameras.items():
        scene.camera=cam
        if name=='floorplan':
            scene.render.resolution_x=1400;scene.render.resolution_y=1400
            for o in ceiling_objects:o.hide_render=True
            for o in scene.objects:
                if o.name.startswith('Context'):o.hide_render=True
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print(json.dumps(audit,ensure_ascii=False),flush=True)
