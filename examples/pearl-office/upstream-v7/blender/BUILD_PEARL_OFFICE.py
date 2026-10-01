import bpy, math, os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)

# ---------- reset ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.color = (0.025,0.045,0.06)

# ---------- materials ----------
def mat(name, rgba, metallic=0.0, roughness=0.5, emission=None, emission_strength=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=rgba
    bsdf.inputs['Metallic'].default_value=metallic
    bsdf.inputs['Roughness'].default_value=roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value=emission
        bsdf.inputs['Emission Strength'].default_value=emission_strength
    return m

M={
 'shell':mat('Shell',(0.12,0.15,0.18,1),.22,.48),
 'floor':mat('Floor',(0.72,0.68,0.60,1),.02,.74),
 'office':mat('OfficeFloor',(0.78,0.75,0.68,1),.02,.68),
 'white':mat('White',(0.88,0.87,0.82,1),.02,.42),
 'wood':mat('Wood',(0.38,0.20,0.10,1),.03,.48),
 'wood2':mat('WoodDark',(0.18,0.08,0.04,1),.03,.42),
 'navy':mat('Navy',(0.08,0.20,0.31,1),.04,.42),
 'blue':mat('BlueLeather',(0.05,0.28,0.42,1),.02,.38),
 'orange':mat('OrangeLeather',(0.53,0.21,0.07,1),.02,.40),
 'black':mat('Black',(0.03,0.04,0.05,1),.38,.34),
 'gold':mat('Gold',(0.55,0.33,0.08,1),.65,.30),
 'cyan':mat('Cyan',(0.04,0.08,0.11,1),.10,.20,(0.13,0.75,1.0,1),5.0),
 'warm':mat('WarmGlow',(0.11,0.05,0.02,1),.05,.30,(1.0,0.35,0.05,1),3.0),
 'green':mat('Green',(0.07,0.30,0.09,1),0,.75),
}
GLASS=mat('Glass',(0.45,0.85,0.94,0.23),.05,.12)
GLASS.surface_render_method='DITHERED'

# ---------- primitives ----------
def cube(name, dims, loc, material, rot=(0,0,0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material: o.data.materials.append(material)
    if bevel>0:
        mod=o.modifiers.new('Bevel','BEVEL'); mod.width=bevel; mod.segments=3
    return o

def cyl(name,r,h,loc,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=h,location=loc)
    o=bpy.context.object;o.name=name
    if material:o.data.materials.append(material)
    return o

def wall(ax,az,bx,bz,h=3.2,t=.22,material=None):
    dx, dz = bx-ax, bz-az; L=(dx*dx+dz*dz)**0.5; ang=math.atan2(dz,dx)
    return cube('Wall',(L,t,h),((ax+bx)/2,(az+bz)/2,h/2),material or M['shell'],rot=(0,0,ang))

# Blender axes: X horizontal, Y plan vertical, Z up.
# ---------- floor ----------
# Approximate pearl shell floor as several overlapping slabs for a rounded triangular silhouette.
cube('FloorMain',(27,15,.14),(0,1.0,-.07),M['floor'],bevel=.35)
cube('FloorTop',(15,8,.14),(0,-5.3,-.07),M['floor'],bevel=.45)

# outer shell walls with left-side entry gap
pts=[(-14.6,7.8),(-16,6.2),(-11.25,1.93),(-9.65,.45),(-8.2,-4.8),(-1.6,-9.6),(0,-10.55),(1.6,-9.6),(8.2,-4.8),(14.2,2),(16,6.2),(14.6,7.8),(-14.6,7.8)]
for a,b in zip(pts,pts[1:]):
    # leave the explicit gap segment omitted
    if a==(-11.25,1.93) and b==(-9.65,.45):
        continue
    wall(*a,*b)

# central Pearl Office floor
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1, depth=.05, location=(0,-.25,.025))
pearl=bpy.context.object; pearl.name='PearlOfficeFloor'; pearl.scale=(7.25,4.15,1); pearl.data.materials.append(M['office'])

# curved glass wall, gap at lower-right
N=44
for i in range(N):
    a0=i/N*math.tau; a1=(i+1)/N*math.tau; ac=(a0+a1)/2
    if .42<ac<.91: continue
    x0,y0=7.25*math.cos(a0),-.25+4.15*math.sin(a0)
    x1,y1=7.25*math.cos(a1),-.25+4.15*math.sin(a1)
    dx,dy=x1-x0,y1-y0;L=(dx*dx+dy*dy)**.5;ang=math.atan2(dy,dx)
    cube('PearlGlass',(L,.06,2.55),((x0+x1)/2,(y0+y1)/2,1.275),GLASS,rot=(0,0,ang))

# furniture helpers
def desk(x,y,w=2.2,d=.8,rot=0,material=None):
    cube('DeskTop',(w,d,.10),(x,y,.78),material or M['wood'],rot=(0,0,rot),bevel=.04)
    for sx in (-1,1):
        cube('DeskLeg',(.08,.08,.70),(x+sx*(w/2-.15)*math.cos(rot), y+sx*(w/2-.15)*math.sin(rot),.38),M['black'])

def chair(x,y,rot=0,material=None):
    cube('ChairSeat',(.52,.52,.12),(x,y,.48),material or M['black'],rot=(0,0,rot),bevel=.05)
    cube('ChairBack',(.52,.10,.70),(x-.22*math.sin(rot),y+.22*math.cos(rot),.82),material or M['black'],rot=(0,0,rot),bevel=.05)

def sofa(x,y,w=2.0,rot=0,material=None):
    m=material or M['blue']; cube('SofaSeat',(w,.78,.30),(x,y,.38),m,rot=(0,0,rot),bevel=.09); cube('SofaBack',(w,.20,.78),(x-.30*math.sin(rot),y+.30*math.cos(rot),.82),m,rot=(0,0,rot),bevel=.10)

def plant(x,y,s=.8):
    cyl('PlantPot',.22*s,.34*s,(x,y,.17*s),M['white']); cyl('Plant',.28*s,.65*s,(x,y,.70*s),M['green'])

# central islands
for x,y,r in [(-3.35,-.65,-.40),(3.35,-.65,.40),(0,2.15,0)]:
    desk(x,y,3.3,.9,r,M['white']);chair(x-.8,y+.6,r);chair(x+.8,y+.6,r)
for x,y in [(-5.5,-2.6),(-5.7,1.1),(-4.8,2.4),(4.9,-2.8),(5.6,.7),(4.5,2.5)]: plant(x,y,.85)

# Reception
cube('ReceptionFloor',(3.7,3.0,.04),(-7.55,.40,.02),M['office'],rot=(0,0,-.16))
cube('ReceptionDesk',(2.8,.72,.85),(-7.25,.55,.43),M['white'],rot=(0,0,-.16),bevel=.09)
sofa(-6.2,-.25,1.2,0,M['orange'])

# Tea Room
cube('TeaFloor',(3.6,2.45,.04),(-7.2,4.25,.02),M['office'])
desk(-7.2,4.35,2.1,.75,0,M['wood']);chair(-7.85,5.0,math.pi);chair(-6.55,5.0,math.pi)

# Trading
desk(-4.2,-7.55,3.65,.85,0,M['wood'])
for x in (-5.25,-4.25,-3.25): chair(x,-6.95,math.pi)
# Executive
desk(3.15,-7.35,1.75,.78,.05,M['wood']);sofa(1.5,-7.35,1.65,0,M['orange'])
# Meeting
desk(8.05,-4.92,3.45,1.15,-.43,M['wood'])
for i in range(-2,3): chair(8.05+i*.62,-3.95-i*.18,-.43+math.pi)
# Director
sofa(11.0,.18,1.7,-.18,M['blue']);desk(11.55,-1.2,1.65,.75,-.18,M['wood'])
# Wine
sofa(13.25,4.75,2.1,.30,M['orange']);cyl('WineTable',.58,.10,(12.15,3.85,.68),M['wood']);cube('WineShelf',(2.2,.45,2.2),(13.3,3.25,1.1),M['wood2'],rot=(0,0,.30))
# Managers
for x in (8.65,3.70,-1.0): desk(x,6.70,1.6,.70,0,M['wood']);chair(x,7.20,math.pi)
# Back office
desk(-12.5,6.2,2.6,.85,-.18,M['white']);chair(-13.0,6.85,math.pi-.18);chair(-12.0,6.85,math.pi-.18)
# Awards + Charity open galleries
for x,y in [(-10.2,-2.8),(-9.1,-2.0),(-12.8,2.0),(-12.4,3.3)]:
    cube('DisplayPlinth',(.55,.55,.75),(x,y,.375),M['white']);cyl('DisplayItem',.14,.32,(x,y,1.0),M['gold'])

# lighting
bpy.ops.object.light_add(type='AREA', location=(0,0,8)); key=bpy.context.object; key.data.energy=1600; key.data.shape='DISK'; key.data.size=11
bpy.ops.object.light_add(type='AREA', location=(-8,-1,4)); fill=bpy.context.object; fill.data.energy=800; fill.data.size=6
bpy.ops.object.light_add(type='AREA', location=(10,2,4)); fill2=bpy.context.object; fill2.data.energy=900; fill2.data.size=6

# camera
bpy.ops.object.camera_add(location=(0,18,24), rotation=(math.radians(52),0,math.radians(180)))
cam=bpy.context.object;cam.name='OverviewCamera';scene.camera=cam
# point camera at origin
def look_at(obj, target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
look_at(cam,(0,0,0))

# render, save, export
scene.render.filepath=os.path.join(OUT,'pearl_office_preview.png')
try: bpy.ops.render.render(write_still=True)
except Exception as e: print('Render warning:',e)
blend_path=os.path.join(OUT,'pearl_office.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
try:
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'pearl_office.glb'), export_format='GLB')
except Exception as e:
    print('GLB export warning:',e)
print('Pearl Office build complete:', blend_path)
