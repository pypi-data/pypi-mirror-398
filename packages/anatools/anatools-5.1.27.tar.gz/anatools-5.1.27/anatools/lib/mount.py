import json
import os
import sys
import time
import subprocess
import datetime
from anatools.lib.print import print_color

home = os.path.expanduser('~')
mountfile = os.path.join(home, '.renderedai', '.mounts.json')

timecheck = 10

def mount_folder(path, mountdata, mounttype='volume', mountexec='goofys', mountname=False, verbose=0):
    mounttypes = f'{mounttype}s'
    mounts = {}
    for mountId in mountdata[mounttypes].keys():
        try:
            command = ''
            wdir = ''
            profile = ''
            proc = None
            for i in range(len(mountdata[mounttypes][mountId]['keys'])):
                print(f'Mounting ', end='', flush=True)
                print_color(f"{'read-only' if mountdata[mounttypes][mountId]['rw'][i] == 'r' else 'read-write'}", "ffa500" if mountdata[mounttypes][mountId]['rw'][i] == 'r' else "00ff00", end='', flush=True)
                print(f" {mounttype} {mountdata[mounttypes][mountId]['name']}...", end='', flush=True)
                rw = '-o ro' if mountdata[mounttypes][mountId]['rw'][i] == 'r' else ''
                mountpoint = f'{home}/.renderedai/{mounttypes}/{mountId}'
                profile = f'renderedai-{mounttypes}-{mountId}'
                
                # SAFETY: Check if mountpoint exists and what it contains before deletion
                if os.path.exists(mountpoint):
                    # Check if it's currently mounted
                    mount_check = subprocess.run(['findmnt', '-n', mountpoint], capture_output=True)
                    if mount_check.returncode == 0:
                        # It's mounted, try to unmount first
                        subprocess.run(["fusermount", "-uz", mountpoint], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.run(["umount", "-lf", mountpoint], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Check if directory has content (potential data loss risk)
                    if os.path.isdir(mountpoint):
                        try:
                            contents = os.listdir(mountpoint)
                            if contents and not (len(contents) == 1 and contents[0] == 'lost+found'):
                                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                                with open('/tmp/mount.log', 'a') as f: 
                                    f.write(f'{timestamp} WARNING: Mount point {mountpoint} contains data: {contents[:10]}\n')
                                # Move the directory to a backup location instead of deleting
                                backup_dir = f'{mountpoint}.backup.{int(time.time())}'
                                os.rename(mountpoint, backup_dir)
                                print_color(f"\nWARNING: Moved existing data at {mountpoint} to {backup_dir}", 'warning', flush=True)
                            else:
                                subprocess.run(["rm", "-rf", mountpoint], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception as e:
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                            with open('/tmp/mount.log', 'a') as f: 
                                f.write(f'{timestamp} ERROR checking mountpoint: {str(e)}\n')
                
                os.makedirs(mountpoint, exist_ok=True)
                
                # SAFETY: Final check before mounting - ensure directory is empty
                if os.path.isdir(mountpoint):
                    contents = os.listdir(mountpoint)
                    if contents and not (len(contents) == 1 and contents[0] == 'lost+found'):
                        print_color(f"\nERROR: Mount point {mountpoint} is not empty, aborting mount to prevent data loss", 'error', flush=True)
                        continue
                
                env = os.environ.copy()
                if mountexec == 'goofys':
                    command = f'goofys {rw} --profile {profile} {mountdata[mounttypes][mountId]["keys"][i][:-1]} {mountpoint}'
                elif mountexec == 's3fs':
                    command = f's3fs {mountdata[mounttypes][mountId]["keys"][i][:-1]} {mountpoint} -o profile={profile} -o endpoint=us-west-2 -o url="https://s3-us-west-2.amazonaws.com" -o use_cache=/tmp/s3fs/{mounttypes}/{mountId} -o mp_umask=000 {rw} -o allow_other -f -d'
                elif mountexec == 'mount-s3':
                    readonly = '--read-only' if rw == '-o ro' else ''
                    command = f'mount-s3 {readonly} --profile {profile} --prefix {mountdata[mounttypes][mountId]["keys"][i][1:]+"/"} {mountdata[mounttypes][mountId]["keys"][i][:-1]} {mountpoint}'
                else: 
                    print_color(f"Invalid mountexec: {mountexec}", 'error', flush=True)
                    sys.exit(1)
                proc = subprocess.Popen(command, shell=True, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                
                # Wait a moment and verify mount succeeded
                time.sleep(2)
                mount_verify = subprocess.run(['findmnt', '-n', mountpoint], capture_output=True)
                if mount_verify.returncode != 0:
                    print_color(f"\nWARNING: Mount may have failed for {mountpoint}", 'warning', flush=True)
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    with open('/tmp/mount.log', 'a') as f: 
                        f.write(f'{timestamp} WARNING: Mount verification failed for {mountpoint}\n')
                
                wdir = f'{path}/{mounttypes}/{mountId}'
                os.makedirs(f'{path}/{mounttypes}/', exist_ok=True)
                if mountname:
                    wdir = os.path.join(path, mounttypes, mountdata[mounttypes][mountId]['name'])
                    if len([ws['name'] for ws in mountdata[mounttypes].values() if ws['name'] == mountdata[mounttypes][mountId]['name']]) > 1:
                        wdir = os.path.join(path, mounttypes, mountdata[mounttypes][mountId]['name'] + f'-{mountId[:5]}')
                if os.path.exists(wdir): 
                    try: os.unlink(wdir)
                    except: pass
                    if os.path.isdir(wdir): 
                        os.rmdir(wdir)
                    elif os.path.isfile(wdir): 
                        os.remove(wdir)
                os.symlink(f'{home}/.renderedai/{mounttypes}/{mountId}', wdir)
                mounts[mountId] = {
                    'status': 'mounted',
                    'exec': mountexec,
                    'command': command,
                    'name': mountdata[mounttypes][mountId]['name'],
                    'mountpath': f'{home}/.renderedai/{mounttypes}/{mountId}',
                    'symlink': wdir,
                    'profile': profile,
                    'pid': proc.pid,
                    'parentpid': os.getpid()
                }
                print('complete!', flush=True)
        except Exception as e:
            print(e)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            with open('/tmp/mount.log', 'a') as f: f.write(f' {timestamp} {str(e)}\n')
            print_color(f'failed, see /tmp/mount.log for details.', 'error', flush=True)
            mounts[mountId] = {
                'status': 'failed',
                'error': str(e)
            }
            continue
    return mounts

def update_credentials(client, workspaces, volumes):
    awsprofiles = {}
    mountdata = {'workspaces': {}, 'volumes': {}}
    expiration = time.time() + 3600  # default to 1 hour expiration
    if os.path.isdir(f'{home}/.aws') and os.path.isfile(f'{home}/.aws/credentials'):
        with open(f'{home}/.aws/credentials', 'r') as awscredfile:
            lines = awscredfile.readlines()
            profile = '[default]'
            awsprofiles[profile] = []
            for line in lines:
                line = line.rstrip()
                if line.startswith('[') and line.endswith(']'):
                    profile = line
                    awsprofiles[profile] = []
                else: awsprofiles[profile].append(line)
    for workspaceId in workspaces.keys():
        data = client.mount_workspaces(workspaces=[workspaceId])
        if data is False: print_color(f'There was an error retrieving mount credential for workspace {workspaceId}, please contact Rendered.ai for support.', 'error'); workspaces.remove(workspaceId)
        awsprofiles[f'[renderedai-workspaces-{workspaceId}]'] = [
            f"aws_access_key_id={data['credentials']['accesskeyid']}",
            f"aws_secret_access_key={data['credentials']['accesskey']}",
            f"aws_session_token={data['credentials']['sessiontoken']}" 
        ]
        mountdata['workspaces'][workspaceId]=data
        mountdata['workspaces'][workspaceId]['name'] = workspaces[workspaceId]['name']
        if 'expiresAt' in data['credentials']: expiration = datetime.datetime.fromisoformat(data['credentials']['expiresAt'].replace('Z', '+00:00')).timestamp()
    for volumeId in volumes.keys():
        data = client.mount_volumes(volumes=[volumeId])
        if data == False: print_color(f'There was an error retrieving mount credential for volume {volumeId}, please contact Rendered.ai for support.', 'error'); volumes.remove(volumeId)
        awsprofiles[f'[renderedai-volumes-{volumeId}]'] = [
            f"aws_access_key_id={data['credentials']['accesskeyid']}",
            f"aws_secret_access_key={data['credentials']['accesskey']}",
            f"aws_session_token={data['credentials']['sessiontoken']}" 
        ]
        mountdata['volumes'][volumeId]=data
        mountdata['volumes'][volumeId]['name'] = volumes[volumeId]['name']
        if 'expiresAt' in data['credentials']: expiration = datetime.datetime.fromisoformat(data['credentials']['expiresAt'].replace('Z', '+00:00')).timestamp()
    if not os.path.isdir(f'{home}/.aws'): os.mkdir(f'{home}/.aws')
    with open(f'{home}/.aws/credentials', 'w+') as awscredfile:
        for profile in awsprofiles.keys():
            if len(awsprofiles[profile]):
                awscredfile.write(profile+'\n')
                awscredfile.writelines([line + '\n' for line in awsprofiles[profile]])
    return mountdata, expiration


def mount_data(mountdata, path, mountexec, mountname=False, verbose=0):
    mounts = {}
    if not os.path.isdir(path): os.mkdir(path)
    mounts['workspaces'] = mount_folder(path, mountdata, 'workspace', mountexec, mountname, verbose)
    mounts['volumes'] = mount_folder(path, mountdata, 'volume', mountexec, mountname, verbose)
    if os.path.exists(mountfile):
        with open(mountfile, 'r') as f: filemounts = json.load(f)
        for mountId in mounts['volumes'].keys():
            filemounts['volumes'][mountId] = mounts['volumes'][mountId]
        for mountId in mounts['workspaces'].keys():
            filemounts['workspaces'][mountId] = mounts['workspaces'][mountId]
    else: filemounts = mounts
    with open(mountfile, 'w') as f: json.dump(filemounts, indent=4, sort_keys=True, fp=f)


def unmount_data(volumeIds, workspaceIds):
    if len(volumeIds):
        print_color(f'Unmounting volumes...', 'brand', end='')
        with open(mountfile, 'r') as f: mounts = json.load(f)
        for mountId in volumeIds:
            mount_info = mounts.get('volumes', {}).get(mountId)
            if not mount_info or mount_info.get('status') != 'mounted': continue
            try:
                # Attempt to kill all processes using the mount path.
                subprocess.run(["fuser", "-km", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(mount_info['symlink'])
            except (KeyError, FileNotFoundError, ProcessLookupError):
                # Ignore if process/symlink is already gone or keys are missing.
                pass
            finally:
                # Always attempt to unmount.
                subprocess.run(["fusermount", "-uz", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["umount", "-lf", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # CRITICAL: Verify that the mount is gone before deleting the directory.
                # Double-check with multiple methods to ensure mount is truly gone
                mount_check = subprocess.run(['findmnt', '-n', mount_info['mountpath']], capture_output=True)
                proc_mounts_check = subprocess.run(['grep', mount_info['mountpath'], '/proc/mounts'], capture_output=True)
                
                if mount_check.returncode == 0 or proc_mounts_check.returncode == 0:
                    print_color(f"\nERROR: Failed to unmount {mount_info['mountpath']}. Directory will not be removed to protect data.", 'error', flush=True)
                else:
                    # The directory is no longer a mount, verify it's a directory before removal
                    if os.path.isdir(mount_info['mountpath']) and not os.path.islink(mount_info['mountpath']):
                        # Additional safety: check if directory is empty or only contains lost+found
                        try:
                            contents = os.listdir(mount_info['mountpath'])
                            if not contents or (len(contents) == 1 and contents[0] == 'lost+found'):
                                subprocess.run(["rm", "-rf", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                print_color(f"\nWARNING: Directory {mount_info['mountpath']} is not empty after unmount. Not removing to protect data.", 'warning', flush=True)
                        except:
                            print_color(f"\nWARNING: Could not verify directory {mount_info['mountpath']} contents. Not removing to protect data.", 'warning', flush=True)
                
                del mounts['volumes'][mountId]
        with open(mountfile, 'w') as f: json.dump(mounts, indent=4, sort_keys=True, fp=f)
        print_color('complete!', 'brand')
    if len(workspaceIds):
        print_color(f'Unmounting workspaces...', 'brand', end='')
        with open(mountfile, 'r') as f: mounts = json.load(f)
        for mountId in workspaceIds:
            mount_info = mounts.get('workspaces', {}).get(mountId)
            if not mount_info or mount_info.get('status') != 'mounted': continue
            try:
                # Attempt to kill all processes using the mount path.
                subprocess.run(["fuser", "-km", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(mount_info['symlink'])
            except (KeyError, FileNotFoundError, ProcessLookupError):
                # Ignore if process/symlink is already gone or keys are missing.
                pass
            finally:
                # Always attempt to unmount.
                subprocess.run(["fusermount", "-uz", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["umount", "-lf", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # CRITICAL: Verify that the mount is gone before deleting the directory.
                # Double-check with multiple methods to ensure mount is truly gone
                mount_check = subprocess.run(['findmnt', '-n', mount_info['mountpath']], capture_output=True)
                proc_mounts_check = subprocess.run(['grep', mount_info['mountpath'], '/proc/mounts'], capture_output=True)
                
                if mount_check.returncode == 0 or proc_mounts_check.returncode == 0:
                    print_color(f"\nERROR: Failed to unmount {mount_info['mountpath']}. Directory will not be removed to protect data.", 'error', flush=True)
                else:
                    # The directory is no longer a mount, verify it's a directory before removal
                    if os.path.isdir(mount_info['mountpath']) and not os.path.islink(mount_info['mountpath']):
                        # Additional safety: check if directory is empty or only contains lost+found
                        try:
                            contents = os.listdir(mount_info['mountpath'])
                            if not contents or (len(contents) == 1 and contents[0] == 'lost+found'):
                                subprocess.run(["rm", "-rf", mount_info['mountpath']], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                print_color(f"\nWARNING: Directory {mount_info['mountpath']} is not empty after unmount. Not removing to protect data.", 'warning', flush=True)
                        except:
                            print_color(f"\nWARNING: Could not verify directory {mount_info['mountpath']} contents. Not removing to protect data.", 'warning', flush=True)
                
                del mounts['workspaces'][mountId]
        with open(mountfile, 'w') as f: json.dump(mounts, indent=4, sort_keys=True, fp=f)
        print_color('complete!', 'brand')

    # Clean up AWS credentials
    print_color(f'Cleaning up credentials...', 'brand', end='')
    aws_creds_path = os.path.join(home, '.aws', 'credentials')
    if os.path.exists(aws_creds_path):
        with open(aws_creds_path, 'r') as f: lines = f.readlines()
        with open(aws_creds_path, 'w') as f:
            in_renderedai_profile = False
            for line in lines:
                if line.strip().startswith('[renderedai-'): in_renderedai_profile = True
                elif line.strip().startswith('['): in_renderedai_profile = False
                if not in_renderedai_profile: f.write(line)
    print_color('complete!', 'brand')


def mount_loop(client, workspaces, volumes, path, preferredexec='goofys', mountname=False, verbose=0):
    goofys_version = None
    s3fs_version = None
    mountpoint_version = None
    try:
        goofys_version_result = subprocess.run(['goofys', '--version'], capture_output=True, text=True, check=True)
        goofys_version = goofys_version_result.stderr.strip()
    except: pass
    try:
        s3fs_version_result = subprocess.run(['s3fs', '--version'], capture_output=True, text=True, check=True)
        s3fs_version = s3fs_version_result.stdout.strip()
    except: pass
    try:
        mountpoint_version_result = subprocess.run(['mount-s3', '--version'], capture_output=True, text=True, check=True)
        mountpoint_version = mountpoint_version_result.stdout.strip()
    except: pass
    if goofys_version is None and s3fs_version is None and mountpoint_version is None:
        print_color("Failed to find goofys, s3fs, or mount-s3, please install one of these options to mount volumes and workspaces.", "error")
        print("Goofys: https://github.com/kahing/goofys")
        print("S3FS: https://github.com/s3fs-fuse/s3fs-fuse")
        print("Mount-S3: https://github.com/awslabs/mountpoint-s3")
        sys.exit(1)
    if preferredexec == 'goofys' and goofys_version: mountexec = 'goofys'
    elif preferredexec == 's3fs' and s3fs_version: mountexec = 's3fs'
    elif preferredexec == 'mount-s3' and mountpoint_version: mountexec = 'mount-s3'
    else: mountexec = 'goofys' if goofys_version else 's3fs' if s3fs_version else 'mount-s3'

    mountdata = None
    while True:
        try:
            mountdata, expiration = update_credentials(client, workspaces, volumes)
            mount_data(mountdata, path, mountexec, mountname, verbose)
            interval = expiration-time.time()
            for i in range(int(interval/timecheck-timecheck)): print(f'Remounting volumes in {int(interval-(i*timecheck))}s...', end='\r', flush=True); time.sleep(timecheck)
            unmount_data(mountdata['volumes'].keys(), mountdata['workspaces'].keys())
        except KeyboardInterrupt: unmount_data(mountdata['volumes'].keys(), mountdata['workspaces'].keys()); sys.exit(0)
        except Exception as e:
            print_color(f'Error: {e}', 'error')
            unmount_data(mountdata['volumes'].keys(), mountdata['workspaces'].keys())
            sys.exit(1)
