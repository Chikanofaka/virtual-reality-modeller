"""Meaningful stdlib smoke/security tests; actual browser acceptance remains separate."""
import contextlib,copy,importlib.util,io,json,pathlib,runpy,shutil,stat,sys,tempfile,threading,unittest,urllib.error,urllib.request,zipfile
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import harness as h

class PlanningTests(unittest.TestCase):
    def setUp(self): self.plan=h.read(ROOT/'templates/measured-studio.json')
    def test_complete_measured_plan_is_connected(self):
        result=h.validate_config(self.plan)
        self.assertEqual(result['connectedCells'],result['walkableCells']);self.assertGreater(result['walkableCells'],100)
    def test_units_and_dimension_confirmation_required(self):
        for field,value in [('units','ft')]:
            p=copy.deepcopy(self.plan);p[field]=value
            with self.assertRaisesRegex(ValueError,'metres'):h.validate_config(p)
        self.plan['provenance']['scaleConfirmed']=False
        with self.assertRaisesRegex(ValueError,'confirmed'):h.validate_config(self.plan)
    def test_missing_dimensions_and_nonnumeric_coordinates_rejected(self):
        self.plan['shell']['width']=None
        with self.assertRaisesRegex(ValueError,'shell.width'):h.validate_config(self.plan)
        self.plan=h.read(ROOT/'templates/measured-studio.json');self.plan['navigation']['spawn'][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'finite'):h.validate_config(self.plan)
    def test_multilevel_floor_rejected(self):
        self.plan['rooms'][0]['floorY']=2
        with self.assertRaisesRegex(ValueError,'single connected floor'):h.validate_config(self.plan)
    def test_optional_visual_values_are_typed_before_planning_lock(self):
        for key,value in [('rotation','not-a-number'),('color','unknown-color'),('interaction',42),('interaction',{'label':'Desk','message':False})]:
            c=copy.deepcopy(self.plan);c['furniture'][0][key]=value
            with self.assertRaisesRegex(ValueError,'Furniture'):h.validate_config(c,False)
        self.plan['rooms'][0]['open']='false'
        with self.assertRaisesRegex(ValueError,'room.open'):h.validate_config(self.plan,False)
    def test_narrow_door_rejected(self):
        self.plan['doors'][0]['width']=.4
        with self.assertRaisesRegex(ValueError,'clear the player'):h.validate_config(self.plan)
    def test_clearance_rejects_spawn_at_boundary(self):
        self.plan['entrance']['position']=[3.99,1.65,0];self.plan['navigation']['spawn']=[3.99,1.65,0]
        with self.assertRaisesRegex(ValueError,'Spawn is not walkable'):h.validate_config(self.plan)
    def test_route_cannot_cross_furniture(self):
        self.plan['navigation']['routes'][0]['points']=[[0,0],[-3,-2.5]]
        with self.assertRaisesRegex(ValueError,'crosses a blocked boundary'):h.validate_config(self.plan)
    def test_disconnected_nav_is_rejected(self):
        self.plan['navigation']['polygons'].append({'id':'island','vertices':[[5,0],[6,0],[6,1],[5,1]]})
        with self.assertRaisesRegex(ValueError,'disconnected'):h.validate_config(self.plan)
    def test_room_destination_must_be_walkable(self):
        self.plan['rooms'][0]['accessPoint']=[-1.7,-1.6]
        with self.assertRaisesRegex(ValueError,'accessPoint'):h.validate_config(self.plan)
    def test_visual_wall_requires_explicit_nav_barrier(self):
        self.plan['navigation']['segments']=[]
        with self.assertRaisesRegex(ValueError,'structural wall'):h.validate_config(self.plan)
        self.plan['navigation']['collisionPolicy']='permissive-visual-partitions'
        h.validate_config(self.plan,False)
    def test_union_seams_are_walkable(self):
        self.plan['navigation']['polygons']=[{'id':'left','vertices':[[-4,-3],[0,-3],[0,3],[-4,3]]},{'id':'right','vertices':[[0,-3],[4,-3],[4,3],[0,3]]}]
        self.assertTrue(h.walkable(self.plan,0,0))
    def test_touching_collider_with_player_radius_is_blocked(self):
        self.plan['navigation']['blockers']=[{'id':'block','bounds':[0,-1,1,1]}]
        self.assertFalse(h.walkable(self.plan,-.22,0));self.assertTrue(h.walkable(self.plan,-.221,0))
    def test_unknown_ellipse_constraint_rejected(self):
        self.plan['navigation']['constraints']=[]
        with self.assertRaisesRegex(ValueError,'Unsupported'):h.validate_config(self.plan)
    def test_pearl_all_rooms_and_portal_are_reachable(self):
        c=h.read(ROOT/'templates/pearl-office.json');result=h.validate_config(c)
        self.assertEqual(result['connectedCells'],result['walkableCells']);self.assertEqual(result['routePoints'],20)

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=pathlib.Path(self.tmp.name);self.p=self.base/'project'
        self.call('init',self.p)
        h.write(self.p/'planning.json',h.read(ROOT/'templates/measured-studio.json'))
        self.call('interrogate',self.p,'--answers',ROOT/'templates/answers.example.json')
    def tearDown(self):self.tmp.cleanup()
    def call(self,*args,expected=0):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):result=h.main([str(a) for a in args])
        self.assertEqual(result,expected)
    def approve(self):self.call('plan',self.p);self.call('approve',self.p,'--accept')
    def build(self):self.approve();self.call('build',self.p);return h.current_build(self.p)
    def test_explicit_review_and_approval_required(self):
        self.call('approve',self.p,'--accept',expected=2);self.call('plan',self.p);self.call('approve',self.p,expected=2)
        self.call('build',self.p,expected=2);self.call('approve',self.p,'--accept');self.assertTrue(h.approved(self.p))
    def test_changed_plan_invalidates_approval(self):
        self.approve();c=h.read(self.p/'planning.json');c['runtime']['speed']=3;h.write(self.p/'planning.json',c)
        self.call('build',self.p,expected=2)
    def test_ingest_invalidates_lock_and_checks_content(self):
        self.approve();source=self.base/'survey.txt';source.write_text('Measured survey evidence')
        self.call('ingest',self.p,source);self.assertFalse((self.p/'approval.json').exists())
        self.approve();entry=h.read(self.p/'sources.json')['files'][0];(self.p/entry['path']).write_text('Changed survey')
        with self.assertRaisesRegex(ValueError,'content changed'):h.approved(self.p)
    def test_answer_change_invalidates_lock(self):
        self.approve();answers=self.base/'answers.json';h.write(answers,{'survey':'Updated measurements from site inspection.'})
        self.call('interrogate',self.p,'--answers',answers);self.assertFalse((self.p/'approval.json').exists())
    def test_incomplete_quests_cannot_lock_generic_project(self):
        h.write(self.p/'intake.json',{'round':0,'answers':{}});self.call('plan',self.p,expected=2)
    def test_build_integrity_and_private_upload_exclusion(self):
        source=self.base/'PRIVATE.txt';source.write_text('PRIVATE USER DATA')
        self.call('ingest',self.p,source);dest=self.build();self.call('validate',self.p,'--build')
        output=self.base/'playable.zip';self.call('package',self.p,'--output',output)
        with zipfile.ZipFile(output) as z:
            self.assertIn('runtime/build.json',z.namelist());self.assertIn('launch.py',z.namelist());self.assertFalse(any('PRIVATE' in n or 'uploads' in n for n in z.namelist()))
            for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):self.assertEqual(z.read(name),(ROOT/name).read_bytes())
        (dest/'index.html').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'integrity'):h.verify_build(dest)
    def test_standalone_launcher_no_open_serves_without_browser(self):
        dest=self.build();output=self.base/'standalone.zip';self.call('package',self.p,'--output',output)
        extracted=self.base/'extracted'
        with zipfile.ZipFile(output) as z:z.extractall(extracted)
        launcher=extracted/'launch.py'
        for flags,opens in [(['--no-open'],False),([],True)]:
            server=mock.Mock();server.server_port=51901
            with mock.patch.object(sys,'argv',[str(launcher),*flags]),mock.patch('http.server.ThreadingHTTPServer',return_value=server),mock.patch('webbrowser.open') as browser,contextlib.redirect_stdout(io.StringIO()) as printed:
                runpy.run_path(str(launcher),run_name='__main__')
            url=f'http://127.0.0.1:51901/?build={h.read(dest / "build.json")["buildId"]}'
            self.assertIn(url,printed.getvalue());server.serve_forever.assert_called_once();server.server_close.assert_called_once()
            if opens:browser.assert_called_once_with(url)
            else:browser.assert_not_called()
    def test_selected_glb_uses_url_safe_build_name_and_keeps_integrity(self):
        fixture=ModelAssetTests();fixture.setUp()
        try:
            fixture.save();src=self.p/'model #100%.glb';shutil.copyfile(fixture.path,src)
        finally:fixture.tearDown()
        config=h.read(self.p/'planning.json');config['assets']=[{'id':'detailed model #1','path':src.name,'type':'model','sha256':h.sha(src)}];h.write(self.p/'planning.json',config)
        dest=self.build();built=h.read(dest/'config.json')['assets'][0]
        self.assertNotIn('#',built['path']);self.assertNotIn('%',built['path']);self.assertEqual(h.sha(dest/built['path']),built['sha256']);h.verify_build(dest)
        src.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Asset content changed'):h.approved(self.p)
    def test_manifest_does_not_ignore_nested_integrity_named_asset(self):
        dest=self.build();asset=dest/'assets'/'integrity.json';asset.parent.mkdir();asset.write_text('untracked')
        with self.assertRaisesRegex(ValueError,'integrity'):h.verify_build(dest)
    def test_server_has_fresh_port_identity_and_no_cache(self):
        dest=self.build();server=h.make_server(dest);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            with urllib.request.urlopen(base+'/__build') as response:
                self.assertIn('no-store',response.headers['Cache-Control']);meta=json.load(response)
            self.assertEqual(meta['port'],server.server_port)
            with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(base+'/?build=stale')
            self.assertEqual(caught.exception.code,409)
            with urllib.request.urlopen(base+'/?build='+meta['buildId']) as response:self.assertEqual(response.status,200)
            server2=h.make_server(dest)
            try:self.assertNotEqual(server.server_port,server2.server_port)
            finally:server2.server_close()
        finally:server.shutdown();server.server_close();thread.join()

class IngestSafetyTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.tmp.name)/'sources.zip'
    def tearDown(self):self.tmp.cleanup()
    def test_zip_traversal_absolute_windows_and_symlink_rejected(self):
        for name in ['../escape.txt','/absolute.txt','C:/escape.txt','a\\..\\escape.txt']:
            with zipfile.ZipFile(self.p,'w') as z:z.writestr(name,'unsafe')
            with self.assertRaisesRegex(ValueError,'Unsafe'):h.inspect_zip(self.p)
        with zipfile.ZipFile(self.p,'w') as z:
            info=zipfile.ZipInfo('link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'../../secret')
        with self.assertRaisesRegex(ValueError,'symlinks'):h.inspect_zip(self.p)
    def test_bounded_archive_inventory_does_not_execute(self):
        with zipfile.ZipFile(self.p,'w') as z:z.writestr('RUN.command','touch NEVER_EXECUTE');z.writestr('plan.txt','floor plan')
        inventory=h.inspect_zip(self.p);self.assertEqual(len(inventory['files']),2);self.assertEqual(inventory['execution'],'never')
        previous=h.MAX_ARCHIVE_BYTES
        try:
            h.MAX_ARCHIVE_BYTES=2
            with self.assertRaisesRegex(ValueError,'safety limit'):h.inspect_zip(self.p)
        finally:h.MAX_ARCHIVE_BYTES=previous
    def test_manifest_uses_posix_paths_and_local_files_normalize_windows_paths(self):
        base=pathlib.Path(self.tmp.name);nested=base/'nested'/'asset.bin';nested.parent.mkdir();nested.write_bytes(b'asset')
        manifest=h.build_manifest(base)
        self.assertIn('nested/asset.bin',manifest);self.assertFalse(any('\\' in key for key in manifest))
        self.assertEqual(h.local_file(base,'nested\\asset.bin'),nested)
        self.assertEqual(h.BuildHandler.extensions_map['.js'],'text/javascript')
    def test_local_file_rejects_symlink_and_escaped_paths(self):
        base=pathlib.Path(self.tmp.name);(base/'file').write_text('ok');(base/'link').symlink_to(base/'file')
        with self.assertRaisesRegex(ValueError,'Symlink'):h.local_file(base,'link')
        with self.assertRaisesRegex(ValueError,'Unsafe'):h.local_file(base,'../file')

class ModelAssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'triangle.glb'
        self.document={'asset':{'version':'2.0'},'buffers':[{'byteLength':36}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36}],'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[1,1,0]}],'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        import struct
        text=json.dumps(self.document,separators=(',',':')).encode();text+=b' '*((-len(text))%4)
        binary=struct.pack('<9f',0,0,0,1,0,0,0,1,0)
        body=struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary
        self.path.write_bytes(struct.pack('<4sII',b'glTF',2,len(body)+12)+body)
    def test_self_contained_glb_accepted(self):
        self.save();result=h.inspect_glb(self.path);self.assertEqual(result['meshes'],1);self.assertFalse(result['externalResources'])
    def test_external_resources_and_decoder_extensions_rejected(self):
        self.document['images']=[{'uri':'https://example.invalid/private.png'}];self.save()
        with self.assertRaisesRegex(ValueError,'external URIs'):h.inspect_glb(self.path)
        del self.document['images'];self.document['extensionsUsed']=['KHR_draco_mesh_compression'];self.save()
        with self.assertRaisesRegex(ValueError,'decoder extensions'):h.inspect_glb(self.path)
    def test_bad_length_buffer_bounds_and_svg_rejected(self):
        self.save();self.path.write_bytes(self.path.read_bytes()+b'junk')
        with self.assertRaisesRegex(ValueError,'length'):h.inspect_glb(self.path)
        self.document['bufferViews'][0]['byteLength']=100;self.save()
        with self.assertRaisesRegex(ValueError,'bufferView exceeds'):h.inspect_glb(self.path)
        self.document['bufferViews'][0]['byteLength']=36;self.document['images']=[{'uri':'data:image/svg+xml;base64,PHN2Zy8+'}];self.save()
        with self.assertRaisesRegex(ValueError,'non-raster'):h.inspect_glb(self.path)
    def test_imported_scene_requires_selected_model(self):
        c=h.read(ROOT/'templates/measured-studio.json');c['scene']={'mode':'imported-glb','assetId':'survey-model'}
        with self.assertRaisesRegex(ValueError,'assetId'):h.validate_config(c,False)
        self.save();c['assets']=[{'id':'survey-model','path':'model.glb','type':'model','sha256':h.sha(self.path),'placement':{'position':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1]}}]
        h.validate_config(c,False)
        c['assets'][0]['placement']['scale'][0]=0
        with self.assertRaisesRegex(ValueError,'scale'):h.validate_config(c,False)

if __name__=='__main__':unittest.main()
