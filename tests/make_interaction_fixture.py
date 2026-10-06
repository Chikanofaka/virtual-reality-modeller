"""Create synthetic GLB test inputs, never a real apartment or owner approval."""
import hashlib
import json
from pathlib import Path
import struct
import sys


def create_fixture(project):
    root=Path(__file__).resolve().parents[1]
    project=Path(project).resolve()
    if not (project/'project.json').is_file():
        raise ValueError('Initialize the synthetic test project first')
    model=project/'interaction-fixture.glb'
    plan_path=project/'fixture-plan.json'
    if model.exists() or plan_path.exists():
        raise ValueError('Refuse to overwrite fixture inputs')
    vertices=[-.5,0,-.5,.5,0,-.5,.5,1,-.5,-.5,1,-.5,-.5,0,.5,.5,0,.5,.5,1,.5,-.5,1,.5]
    indices=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,3,7,6,3,6,2,0,4,7,0,7,3,1,2,6,1,6,5]
    binary=struct.pack('<24f',*vertices)+struct.pack('<36H',*indices)
    nodes=[
        {'name':'FixtureTVScreen','mesh':0,'translation':[-1.7,0,-1.6],'scale':[2.2,.8,.8]},
        {'name':'FixtureLampShade','mesh':0,'translation':[2.8,0,1.8],'scale':[.65,.9,.65]},
        {'name':'FixtureWall','mesh':0,'translation':[-.5,0,-1.6],'scale':[.12,2.8,1.4]},
    ]
    gltf={'asset':{'version':'2.0','generator':'Harness synthetic interaction regression fixture'},
          'buffers':[{'byteLength':len(binary)}],
          'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':96},{'buffer':0,'byteOffset':96,'byteLength':72}],
          'accessors':[{'bufferView':0,'componentType':5126,'count':8,'type':'VEC3','min':[-.5,0,-.5],'max':[.5,1,.5]},
                       {'bufferView':1,'componentType':5123,'count':36,'type':'SCALAR'}],
          'materials':[{'pbrMetallicRoughness':{'baseColorFactor':[.24,.40,.55,1],'roughnessFactor':.8},'emissiveFactor':[.01,.01,.01]}],
          'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],
          'nodes':nodes,'scenes':[{'nodes':list(range(len(nodes)))}],'scene':0}
    raw=json.dumps(gltf,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
    body=struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary
    model.write_bytes(struct.pack('<4sII',b'glTF',2,len(body)+12)+body)
    plan=json.loads((root/'templates/external-user-game.json').read_text())
    plan['project']={'id':'interaction-effects-fixture','name':'Synthetic interaction visibility and reset test'}
    plan['provenance']['notes']+=' Only synthetic cuboids; no real apartment approval, modelling or fidelity claim.'
    plan['scene']={'mode':'imported-glb','assetId':'interaction-fixture'}
    plan['runtime'].update(browsers=['chrome'],interactionOcclusion='structural-segments')
    plan['assets']=[{'id':'interaction-fixture','type':'model','path':model.name,'sha256':hashlib.sha256(model.read_bytes()).hexdigest()}]
    plan['navigation']['segments'].append({'id':'interaction-wall','a':[-.5,-2.3],'b':[-.5,-.9],'thickness':.12})
    plan['navigation']['routes']=[{'id':'early-chair-then-visible-desk-chair',
        'points':[[0,2.2],[2,1],[2,0],[0,0],[-1.7,-.5],[-1.7,.3],[2,1],[0,2.2]]}]
    for item,name,color in zip(plan['furniture'],['FixtureTVScreen','FixtureLampShade'],['#286cff','#ffbb55']):
        item['interaction']['effects']=[{'objectName':name,'emissive':color,'intensity':3}]
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    print(plan_path)


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 tests/make_interaction_fixture.py INITIALIZED_SYNTHETIC_PROJECT')
    create_fixture(sys.argv[1])
