"""Container-only U07 runner. Mounts: allowlisted /source, /work volume, /evidence."""
from pathlib import Path
import hashlib,json,os,platform,shutil,subprocess,sys,time
ROOT=Path('/work');EVIDENCE=Path('/evidence');EVIDENCE.mkdir(exist_ok=True)
report={'phase':sys.argv[1],'environment':{'os':platform.platform(),'python':sys.version},'commands':[]}
def run(args,cwd=ROOT,env=None):
    started=time.monotonic();p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,env=os.environ|(env or {}))
    record={'command':args,'cwd':str(cwd),'exit_code':p.returncode,'seconds':round(time.monotonic()-started,3),'stdout':p.stdout,'stderr':p.stderr};report['commands'].append(record)
    (EVIDENCE/(report['phase']+'-commands.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(' '.join(args),p.returncode,flush=True)
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    return p.stdout
def tree(folder):return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}
try:
    if report['phase']=='install':
        manifest=json.loads(Path('/source/publication/files.json').read_text())['files']
        manifest['publication/files.json']=hashlib.sha256(Path('/source/publication/files.json').read_bytes()).hexdigest()
        assert not list(ROOT.iterdir()), 'Fresh volume must be empty'
        actual={p.relative_to('/source').as_posix() for p in Path('/source').rglob('*') if p.is_file()}
        assert actual==set(manifest), 'Source contains missing or unexpected files'
        for name,h in manifest.items():
            p=Path('/source')/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==h
            dest=ROOT/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        report['source_sha256']=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest();report['copied_file_count']=len(manifest)
        run(['node','--version']);run(['npm','--version']);run(['python3','-m','venv','.venv'])
        run(['/work/.venv/bin/python','-m','pip','install','-r','requirements.txt'])
        run(['npm','ci','--no-fund','--no-audit'],ROOT/'apps/web')
    else:
        # /source is not mounted in this phase; no host/private research tree exists.
        assert not Path('/source').exists();report['private_workspace_mounted']=False
        env={'PATH':'/work/.venv/bin:'+os.environ['PATH']}
        run(['/work/.venv/bin/python','-m','pipeline.build_local'],env=env)
        run(['/work/.venv/bin/python','-m','unittest','discover','-s','tests','-p','test_public.py','-v'],env=env)
        builds=[]
        for i in range(1 if report['phase']=='capture' else 2):
            run(['npm','run','build'],ROOT/'apps/web',env=env);builds.append(tree(ROOT/'apps/web/out'))
        if len(builds)==2:assert builds[0]==builds[1],'Static builds differ'
        report['static_builds']=builds;report['static_byte_identity']=len(builds)==2
        server=subprocess.Popen(['/work/.venv/bin/python','-m','http.server','3000','--bind','127.0.0.1','--directory','apps/web/out'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            run(['npm','test'],ROOT/'apps/web',env=env)
            if report['phase']!='capture':run(['node','scripts/demo.mjs'],ROOT/'apps/web',env=env)
        finally:server.terminate();server.wait()
        shutil.copytree(ROOT/'verification',EVIDENCE/'verification',dirs_exist_ok=True)
        shutil.copytree(ROOT/'apps/web/out',EVIDENCE/'static',dirs_exist_ok=True)
        report['artifacts']=tree(ROOT/'data/artifacts')
    report['status']='CAPTURE_COMPLETE_NOT_U07' if report['phase']=='capture' else 'PASS'
except Exception as exc:
    report['status']='FAIL';report['error']=str(exc);raise
finally:(EVIDENCE/(report['phase']+'-report.json')).write_text(json.dumps(report,indent=2)+'\n')
