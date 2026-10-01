#!/usr/bin/env python3
"""Launch the bundled historical Pearl example without inventing a new plan approval."""
import argparse,pathlib,sys
import harness

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default=str(harness.ROOT/'projects'/'pearl-office'))
    parser.add_argument('--browser',choices=['safari','chrome'],default='safari')
    parser.add_argument('--no-open',action='store_true')
    parser.add_argument('--build-only',action='store_true')
    args=parser.parse_args();p=pathlib.Path(args.project).expanduser().resolve()
    if not (p/'project.json').exists():
        if harness.main(['init',str(p),'--example','pearl-office']):return 2
    if harness.read(p/'planning.json')!=harness.read(harness.ROOT/'templates'/'pearl-office.json') or harness.read(p/'sources.json')['files']:
        sys.exit('Quickstart only accepts the unchanged historical example without uploads. Use the normal plan → approve → build workflow for your edits.')
    # This automatic approval applies exclusively to the bundled historical plan.
    for command in (['plan',str(p)],['approve',str(p),'--accept']):
        if harness.main(command):return 2
    expected=harness.digest({'plan':harness.plan_hash(p),'runtime':harness.runtime_hash(),'version':harness.VERSION})[:16]
    dest=p/'builds'/expected
    if dest.exists():
        harness.verify_build(dest);harness.write(p/'current-build.json',{'buildId':expected,'path':dest.relative_to(p).as_posix()})
    elif harness.main(['build',str(p)]):return 2
    if harness.main(['validate',str(p),'--build']):return 2
    if args.build_only:return 0
    cmd=['play',str(p),'--browser',args.browser]
    if args.no_open:cmd.append('--no-open')
    return harness.main(cmd)
if __name__=='__main__':sys.exit(main())
