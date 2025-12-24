"""
Volume Data Transfer Library

This module provides functions for efficient data transfer between volumes,
local paths, and S3 using direct boto3 operations with parallel execution.
"""

import os
import sys
import hashlib
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Check for boto3 dependency
try:
    import boto3
    from botocore.exceptions import ClientError
    from boto3.s3.transfer import TransferConfig
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    TransferConfig = None  # Placeholder

from anatools.lib.print import print_color


class TransferProgress:
    """Track and display transfer progress."""

    def __init__(self, total_files=0, total_size=0, verbose=False):
        self.total_files = total_files
        self.total_size = total_size
        self.completed_files = 0
        self.completed_size = 0
        self.failed_files = []
        self.start_time = time.time()
        self.lock = Lock()
        self.verbose = verbose

    def update(self, file_path, size, success=True):
        """Update progress for a completed file."""
        with self.lock:
            if success:
                self.completed_files += 1
                self.completed_size += size
            else:
                self.failed_files.append(file_path)
            self._display_progress()

    def _display_progress(self):
        """Display current progress."""
        if self.total_files == 0:
            return

        elapsed = time.time() - self.start_time
        percent = (self.completed_files / self.total_files) * 100

        # Calculate speed
        if elapsed > 0:
            speed_mb = (self.completed_size / (1024 * 1024)) / elapsed
            speed_str = f"{speed_mb:.2f} MB/s"
        else:
            speed_str = "calculating..."

        # Calculate ETA
        if self.completed_files > 0 and elapsed > 0:
            files_per_sec = self.completed_files / elapsed
            remaining_files = self.total_files - self.completed_files
            eta_seconds = remaining_files / files_per_sec
            eta_str = f"{int(eta_seconds)}s"
        else:
            eta_str = "calculating..."

        if not self.verbose:
            print(f"\rProgress: {self.completed_files}/{self.total_files} files ({percent:.1f}%) | "
                  f"Speed: {speed_str} | ETA: {eta_str}  ", end='', flush=True)
        else:
            print(f"Progress: {self.completed_files}/{self.total_files} files ({percent:.1f}%) | "
                  f"Speed: {speed_str} | ETA: {eta_str}")

    def finish(self):
        """Display final summary."""
        if not self.verbose:
            print()  # New line after progress bar
        elapsed = time.time() - self.start_time
        size_mb = self.completed_size / (1024 * 1024)

        print_color(f"\nTransfer completed!", 'brand')
        print(f"  Files transferred: {self.completed_files}/{self.total_files}")
        print(f"  Data transferred: {size_mb:.2f} MB")
        print(f"  Time elapsed: {elapsed:.2f}s")

        if self.failed_files:
            print_color(f"\n  Failed files ({len(self.failed_files)}):", 'error')
            for failed in self.failed_files[:10]:
                print(f"    - {failed}")
            if len(self.failed_files) > 10:
                print(f"    ... and {len(self.failed_files) - 10} more")


def get_volume_id_from_mountpoint(path):
    """
    Extract volume ID from a mount point by reading /proc/mounts.

    Args:
        path: Local path that might be a volume mount point

    Returns:
        str: Volume ID if found, None otherwise
    """
    import re

    abs_path = os.path.abspath(path)

    # Find the longest matching mount point
    try:
        with open('/proc/mounts', 'r') as f:
            mounts = f.readlines()

        best_match = None
        best_match_len = 0

        for line in mounts:
            parts = line.split()
            if len(parts) < 2:
                continue

            device = parts[0]
            mount_point = parts[1]

            # Check if our path is under this mount point
            if abs_path.startswith(mount_point):
                # Find the longest match (most specific mount point)
                if len(mount_point) > best_match_len:
                    best_match = (device, mount_point)
                    best_match_len = len(mount_point)

        if best_match:
            device, mount_point = best_match

            # Parse device path to extract volume ID
            # Format: bucket-name:/org-id/volume-id or bucket-name:/org-id/volume-id/
            # Example: renderedai-dev-volumes:/3da3f384-d6e8-45af-ab8f-bfee07948132/f084ad3b-2d32-4bf0-8bd5-52c0769b4811
            match = re.match(r'^[^:]+:/[a-f0-9\-]+/([a-f0-9\-]+)/?$', device)
            if match:
                volume_id = match.group(1)
                # Calculate prefix relative to mount point
                if abs_path == mount_point:
                    prefix = ''
                else:
                    prefix = os.path.relpath(abs_path, mount_point)
                return {
                    'volume_id': volume_id,
                    'prefix': prefix
                }

    except (IOError, OSError):
        pass

    return None


def parse_transfer_location(location):
    """
    Parse a transfer location string into its components.

    Args:
        location: String in format:
            - "volumeId" or "volumeId:prefix" for volumes
            - "/path/to/local" or "path/to/local" for local paths
            - Volume mount points are detected automatically

    Returns:
        dict: {
            'type': 'volume' or 'local',
            'volumeId': str (if volume) or None,
            'prefix': str (volume prefix or local path),
        }
    """
    if not location:
        raise ValueError("Location cannot be empty")

    # Check if it's a local path
    if location.startswith('/') or location.startswith('./') or location.startswith('..'):
        abs_path = os.path.abspath(location)

        # Check if this path is a volume mount point by reading /proc/mounts
        mount_info = get_volume_id_from_mountpoint(abs_path)
        if mount_info:
            return {
                'type': 'volume',
                'volumeId': mount_info['volume_id'],
                'prefix': mount_info['prefix']
            }

        # Regular local path
        return {
            'type': 'local',
            'volumeId': None,
            'prefix': abs_path
        }

    # Check for volume with prefix (contains colon)
    if ':' in location:
        parts = location.split(':', 1)
        volume_id = parts[0]
        prefix = parts[1].strip('/')  # Remove leading/trailing slashes

        # Validate volumeId format (basic check)
        if not volume_id or len(volume_id) < 5:
            # Might be a Windows path like C:\path, treat as local
            return {
                'type': 'local',
                'volumeId': None,
                'prefix': os.path.abspath(location)
            }

        return {
            'type': 'volume',
            'volumeId': volume_id,
            'prefix': prefix
        }

    # Check if it looks like a volume ID or a local path
    # Volume IDs are typically alphanumeric with dashes
    if '-' in location and not os.path.exists(location):
        return {
            'type': 'volume',
            'volumeId': location,
            'prefix': ''
        }

    # Default to local path
    return {
        'type': 'local',
        'volumeId': None,
        'prefix': os.path.abspath(location)
    }


def parse_s3_uri(s3_uri):
    """
    Parse an S3 URI into bucket and prefix.

    Args:
        s3_uri: S3 URI in format "s3://bucket/prefix/" or "bucket:/prefix/"

    Returns:
        dict: {
            'bucket': str,
            'prefix': str,
            'region': str
        }
    """
    # Parse S3 URI - handle both formats:
    # 1. s3://bucket-name/prefix/
    # 2. bucket-name:/prefix/
    if s3_uri.startswith('s3://'):
        s3_uri = s3_uri[5:]  # Remove 's3://'
        parts = s3_uri.split('/', 1)
        bucket = parts[0]
        prefix = parts[1].rstrip('/') if len(parts) > 1 else ''
    elif ':/' in s3_uri:
        # Handle bucket-name:/prefix/ format
        parts = s3_uri.split(':/', 1)
        bucket = parts[0]
        prefix = parts[1].rstrip('/') if len(parts) > 1 else ''
    else:
        raise Exception(f"Invalid S3 URI format: {s3_uri}")

    # Determine region (default to us-west-2 for Rendered.ai)
    region = 'us-west-2'

    return {
        'bucket': bucket,
        'prefix': prefix,
        'region': region
    }


def resolve_volume_s3_location(client, volume_id):
    """
    Get S3 bucket and prefix information for a volume using mount credentials.

    Args:
        client: anatools client instance
        volume_id: Volume ID to resolve

    Returns:
        dict: {
            'bucket': str,
            'prefix': str,
            'credentials': dict with 'accesskeyid', 'accesskey', 'sessiontoken',
            'region': str
        }
    """
    # Get mount credentials for the volume
    mount_data = client.mount_volumes(volumes=[volume_id])

    if not mount_data or 'credentials' not in mount_data:
        raise Exception(f"Failed to retrieve credentials for volume {volume_id}")

    # Parse S3 location from keys
    # keys format: ["s3://bucket-name/prefix/"]
    if 'keys' not in mount_data or not mount_data['keys']:
        raise Exception(f"No S3 keys found for volume {volume_id}")

    s3_uri = mount_data['keys'][0]
    s3_info = parse_s3_uri(s3_uri)

    return {
        'bucket': s3_info['bucket'],
        'prefix': s3_info['prefix'],
        'credentials': mount_data['credentials'],
        'region': s3_info['region']
    }


def create_s3_client(credentials, region='us-west-2'):
    """
    Create a boto3 S3 client with temporary credentials.

    Args:
        credentials: Dict with 'accesskeyid', 'accesskey', 'sessiontoken'
        region: AWS region

    Returns:
        boto3 S3 client
    """
    return boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=credentials['accesskeyid'],
        aws_secret_access_key=credentials['accesskey'],
        aws_session_token=credentials['sessiontoken']
    )


def calculate_etag(file_path, chunk_size=8 * 1024 * 1024):
    """
    Calculate ETag for a file (MD5 hash).

    Args:
        file_path: Path to file
        chunk_size: Chunk size for reading

    Returns:
        str: MD5 hash (ETag)
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()


def list_s3_objects(s3_client, bucket, prefix, recursive=True):
    """
    List all objects in an S3 bucket with given prefix.

    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket name
        prefix: Key prefix
        recursive: If False, only list objects at current level

    Returns:
        list: List of dicts with 'key', 'size', 'etag', 'last_modified'
    """
    objects = []
    continuation_token = None

    # Add trailing slash to prefix if not empty
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    while True:
        params = {
            'Bucket': bucket,
            'Prefix': prefix,
            'MaxKeys': 1000
        }

        if not recursive:
            params['Delimiter'] = '/'

        if continuation_token:
            params['ContinuationToken'] = continuation_token

        try:
            response = s3_client.list_objects_v2(**params)
        except ClientError as e:
            print_color(f"Error listing S3 objects: {e}", 'error')
            raise

        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip directory markers
                if obj['Key'].endswith('/'):
                    continue

                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'etag': obj['ETag'].strip('"'),
                    'last_modified': obj['LastModified']
                })

        if not response.get('IsTruncated'):
            break

        continuation_token = response.get('NextContinuationToken')

    return objects


def list_local_files(local_path, recursive=True):
    """
    List all files in a local directory.

    Args:
        local_path: Local directory path
        recursive: If False, only list files at current level

    Returns:
        list: List of dicts with 'path', 'size', 'relative_path'
    """
    files = []

    if not os.path.exists(local_path):
        raise Exception(f"Local path does not exist: {local_path}")

    if os.path.isfile(local_path):
        return [{
            'path': local_path,
            'size': os.path.getsize(local_path),
            'relative_path': os.path.basename(local_path)
        }]

    if recursive:
        for root, dirs, filenames in os.walk(local_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, local_path)
                files.append({
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'relative_path': relative_path
                })
    else:
        for item in os.listdir(local_path):
            file_path = os.path.join(local_path, item)
            if os.path.isfile(file_path):
                files.append({
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'relative_path': item
                })

    return files


def upload_file_to_s3(s3_client, local_file, bucket, key, max_retries=3):
    """
    Upload a single file to S3 with retries.

    Args:
        s3_client: boto3 S3 client
        local_file: Path to local file
        bucket: S3 bucket
        key: S3 key
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    config = TransferConfig(
        multipart_threshold=100 * 1024 * 1024,
        max_concurrency=10,
        multipart_chunksize=100 * 1024 * 1024,
        use_threads=True
    )

    for attempt in range(max_retries):
        try:
            s3_client.upload_file(local_file, bucket, key, Config=config)
            return True
        except ClientError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print_color(f"Failed to upload {local_file} to s3://{bucket}/{key}: {e}", 'error')
                return False
    return False


def download_file_from_s3(s3_client, bucket, key, local_file, max_retries=3):
    """
    Download a single file from S3 with retries.

    Args:
        s3_client: boto3 S3 client
        bucket: S3 bucket
        key: S3 key
        local_file: Path to save file locally
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(local_file), exist_ok=True)

    config = TransferConfig(
        multipart_threshold=100 * 1024 * 1024,
        max_concurrency=10,
        multipart_chunksize=100 * 1024 * 1024,
        use_threads=True
    )

    for attempt in range(max_retries):
        try:
            s3_client.download_file(bucket, key, local_file, Config=config)
            return True
        except ClientError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print_color(f"Failed to download s3://{bucket}/{key} to {local_file}: {e}", 'error')
                return False
    return False


def copy_s3_object(s3_client, source_bucket, source_key, dest_bucket, dest_key, max_retries=3):
    """
    Copy an object within S3 (server-side copy).
    Uses multipart copy for files >5GB to handle large files efficiently.

    Args:
        s3_client: boto3 S3 client
        source_bucket: Source S3 bucket
        source_key: Source S3 key
        dest_bucket: Destination S3 bucket
        dest_key: Destination S3 key
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    copy_source = {'Bucket': source_bucket, 'Key': source_key}

    try:
        head_response = s3_client.head_object(Bucket=source_bucket, Key=source_key)
        file_size = head_response['ContentLength']
    except ClientError as e:
        print_color(f"Failed to get object metadata for s3://{source_bucket}/{source_key}: {e}", 'error')
        return False

    MULTIPART_THRESHOLD = 5 * 1024 * 1024 * 1024

    if file_size >= MULTIPART_THRESHOLD:
        return _multipart_copy_s3_object(s3_client, source_bucket, source_key, dest_bucket, dest_key, file_size, max_retries)

    for attempt in range(max_retries):
        try:
            s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            return True
        except ClientError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print_color(f"Failed to copy s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}: {e}", 'error')
                return False
    return False


def _multipart_copy_s3_object(s3_client, source_bucket, source_key, dest_bucket, dest_key, file_size, max_retries=3):
    """
    Perform multipart copy for large S3 objects (>5GB).

    Args:
        s3_client: boto3 S3 client
        source_bucket: Source S3 bucket
        source_key: Source S3 key
        dest_bucket: Destination S3 bucket
        dest_key: Destination S3 key
        file_size: Size of the source object in bytes
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    PART_SIZE = 500 * 1024 * 1024

    try:
        mpu = s3_client.create_multipart_upload(
            Bucket=dest_bucket,
            Key=dest_key
        )
        upload_id = mpu['UploadId']

        parts = []
        part_number = 1
        bytes_copied = 0

        while bytes_copied < file_size:
            start_byte = bytes_copied
            end_byte = min(bytes_copied + PART_SIZE - 1, file_size - 1)

            for attempt in range(max_retries):
                try:
                    part_response = s3_client.upload_part_copy(
                        Bucket=dest_bucket,
                        Key=dest_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        CopySource={
                            'Bucket': source_bucket,
                            'Key': source_key
                        },
                        CopySourceRange=f'bytes={start_byte}-{end_byte}'
                    )

                    parts.append({
                        'ETag': part_response['CopyPartResult']['ETag'],
                        'PartNumber': part_number
                    })
                    break
                except ClientError as e:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        s3_client.abort_multipart_upload(
                            Bucket=dest_bucket,
                            Key=dest_key,
                            UploadId=upload_id
                        )
                        print_color(f"Failed to copy part {part_number} of s3://{source_bucket}/{source_key}: {e}", 'error')
                        return False

            bytes_copied = end_byte + 1
            part_number += 1

        s3_client.complete_multipart_upload(
            Bucket=dest_bucket,
            Key=dest_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        return True

    except ClientError as e:
        print_color(f"Failed multipart copy of s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}: {e}", 'error')
        try:
            s3_client.abort_multipart_upload(
                Bucket=dest_bucket,
                Key=dest_key,
                UploadId=upload_id
            )
        except:
            pass
        return False


def local_to_s3_transfer(client, source_path, dest_volume_id, dest_prefix='',
                         recursive=True, parallel=10, dry_run=False, verbose=False):
    """
    Transfer files from local path to S3 volume.

    Args:
        client: anatools client
        source_path: Local source path
        dest_volume_id: Destination volume ID
        dest_prefix: Destination prefix within volume
        recursive: Transfer recursively
        parallel: Number of parallel workers
        dry_run: Don't actually transfer, just show what would happen
        verbose: Verbose output

    Returns:
        bool: True if successful
    """
    print_color(f"Preparing upload from local to volume...", 'brand')

    # List local files
    local_files = list_local_files(source_path, recursive)

    if not local_files:
        print_color("No files found to transfer", 'warning')
        return True

    # Get S3 location for destination
    dest_s3 = resolve_volume_s3_location(client, dest_volume_id)
    dest_s3_client = create_s3_client(dest_s3['credentials'], dest_s3['region'])

    # Combine volume prefix and destination prefix
    if dest_prefix:
        full_dest_prefix = f"{dest_s3['prefix']}/{dest_prefix}".strip('/')
    else:
        full_dest_prefix = dest_s3['prefix']

    # Build transfer list
    transfer_list = []
    total_size = 0

    for file_info in local_files:
        dest_key = f"{full_dest_prefix}/{file_info['relative_path']}".strip('/')
        transfer_list.append({
            'local_file': file_info['path'],
            'dest_key': dest_key,
            'size': file_info['size']
        })
        total_size += file_info['size']

    if not transfer_list:
        print_color("No files need to be transferred", 'brand')
        return True

    print(f"Transferring {len(transfer_list)} files ({total_size / (1024*1024):.2f} MB)...")

    if dry_run:
        print_color("\n[DRY RUN] Would transfer:", 'warning')
        for item in transfer_list[:20]:
            print(f"  {item['local_file']} -> s3://{dest_s3['bucket']}/{item['dest_key']}")
        if len(transfer_list) > 20:
            print(f"  ... and {len(transfer_list) - 20} more files")
        return True

    # Execute parallel uploads
    progress = TransferProgress(len(transfer_list), total_size, verbose)

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {}
        for item in transfer_list:
            future = executor.submit(
                upload_file_to_s3,
                dest_s3_client,
                item['local_file'],
                dest_s3['bucket'],
                item['dest_key']
            )
            futures[future] = item

        for future in as_completed(futures):
            item = futures[future]
            success = future.result()
            progress.update(item['local_file'], item['size'], success)

    progress.finish()
    return len(progress.failed_files) == 0


def s3_to_local_transfer(client, source_volume_id, source_prefix, dest_path,
                        recursive=True, parallel=10, dry_run=False, verbose=False):
    """
    Transfer files from S3 volume to local path.

    Args:
        client: anatools client
        source_volume_id: Source volume ID
        source_prefix: Source prefix within volume
        dest_path: Local destination path
        recursive: Transfer recursively
        parallel: Number of parallel workers
        dry_run: Don't actually transfer, just show what would happen
        verbose: Verbose output

    Returns:
        bool: True if successful
    """
    print_color(f"Preparing download from volume to local...", 'brand')

    # Get S3 location for source
    source_s3 = resolve_volume_s3_location(client, source_volume_id)
    source_s3_client = create_s3_client(source_s3['credentials'], source_s3['region'])

    # Combine volume prefix and source prefix
    if source_prefix:
        full_source_prefix = f"{source_s3['prefix']}/{source_prefix}".strip('/')
    else:
        full_source_prefix = source_s3['prefix']

    # List S3 objects
    s3_objects = list_s3_objects(source_s3_client, source_s3['bucket'], full_source_prefix, recursive)

    if not s3_objects:
        print_color("No files found to transfer", 'warning')
        return True

    # Build transfer list
    transfer_list = []
    total_size = 0

    for obj in s3_objects:
        # Calculate relative path by removing prefix
        rel_path = obj['key'][len(full_source_prefix):].lstrip('/')
        local_file = os.path.join(dest_path, rel_path)

        transfer_list.append({
            'source_key': obj['key'],
            'local_file': local_file,
            'size': obj['size']
        })
        total_size += obj['size']

    if not transfer_list:
        print_color("No files need to be transferred", 'brand')
        return True

    print(f"Transferring {len(transfer_list)} files ({total_size / (1024*1024):.2f} MB)...")

    if dry_run:
        print_color("\n[DRY RUN] Would transfer:", 'warning')
        for item in transfer_list[:20]:
            print(f"  s3://{source_s3['bucket']}/{item['source_key']} -> {item['local_file']}")
        if len(transfer_list) > 20:
            print(f"  ... and {len(transfer_list) - 20} more files")
        return True

    # Execute parallel downloads
    progress = TransferProgress(len(transfer_list), total_size, verbose)

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {}
        for item in transfer_list:
            future = executor.submit(
                download_file_from_s3,
                source_s3_client,
                source_s3['bucket'],
                item['source_key'],
                item['local_file']
            )
            futures[future] = item

        for future in as_completed(futures):
            item = futures[future]
            success = future.result()
            progress.update(item['local_file'], item['size'], success)

    progress.finish()
    return len(progress.failed_files) == 0


def s3_to_s3_transfer(client, source_volume_id, source_prefix, dest_volume_id, dest_prefix,
                     recursive=True, parallel=10, dry_run=False, verbose=False):
    """
    Transfer files between S3 volumes (server-side copy).

    Args:
        client: anatools client
        source_volume_id: Source volume ID
        source_prefix: Source prefix within volume
        dest_volume_id: Destination volume ID
        dest_prefix: Destination prefix within volume
        recursive: Transfer recursively
        parallel: Number of parallel workers
        dry_run: Don't actually transfer, just show what would happen
        verbose: Verbose output

    Returns:
        bool: True if successful
    """
    print_color(f"Preparing volume-to-volume transfer (server-side copy)...", 'brand')

    # Get mount credentials for both volumes (single credential with access to both)
    mount_data = client.mount_volumes(volumes=[source_volume_id, dest_volume_id])

    if not mount_data or 'credentials' not in mount_data:
        raise Exception(f"Failed to retrieve credentials for volumes")

    # Parse S3 locations for both volumes from keys
    if 'keys' not in mount_data or len(mount_data['keys']) < 2:
        raise Exception(f"Expected 2 S3 keys, got {len(mount_data.get('keys', []))}")

    # Parse source S3 location
    source_s3_uri = mount_data['keys'][0]
    source_s3 = parse_s3_uri(source_s3_uri)

    # Parse destination S3 location
    dest_s3_uri = mount_data['keys'][1]
    dest_s3 = parse_s3_uri(dest_s3_uri)

    # Create S3 client with shared credentials
    s3_client = create_s3_client(mount_data['credentials'], source_s3['region'])

    # Combine volume prefixes with user-specified prefixes
    if source_prefix:
        full_source_prefix = f"{source_s3['prefix']}/{source_prefix}".strip('/')
    else:
        full_source_prefix = source_s3['prefix']

    if dest_prefix:
        full_dest_prefix = f"{dest_s3['prefix']}/{dest_prefix}".strip('/')
    else:
        full_dest_prefix = dest_s3['prefix']

    # List source objects
    source_objects = list_s3_objects(s3_client, source_s3['bucket'], full_source_prefix, recursive)

    if not source_objects:
        print_color("No files found to transfer", 'warning')
        return True

    # Build transfer list
    transfer_list = []
    total_size = 0

    for obj in source_objects:
        # Calculate relative path
        rel_path = obj['key'][len(full_source_prefix):].lstrip('/')
        dest_key = f"{full_dest_prefix}/{rel_path}".strip('/')

        transfer_list.append({
            'source_key': obj['key'],
            'dest_key': dest_key,
            'size': obj['size']
        })
        total_size += obj['size']

    if not transfer_list:
        print_color("No files need to be transferred", 'brand')
        return True

    print(f"Transferring {len(transfer_list)} files ({total_size / (1024*1024):.2f} MB)...")

    if dry_run:
        print_color("\n[DRY RUN] Would transfer:", 'warning')
        for item in transfer_list[:20]:
            print(f"  s3://{source_s3['bucket']}/{item['source_key']} -> s3://{dest_s3['bucket']}/{item['dest_key']}")
        if len(transfer_list) > 20:
            print(f"  ... and {len(transfer_list) - 20} more files")
        return True

    # Execute parallel S3 copies
    progress = TransferProgress(len(transfer_list), total_size, verbose)

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {}
        for item in transfer_list:
            future = executor.submit(
                copy_s3_object,
                s3_client,
                source_s3['bucket'],
                item['source_key'],
                dest_s3['bucket'],
                item['dest_key']
            )
            futures[future] = item

        for future in as_completed(futures):
            item = futures[future]
            success = future.result()
            progress.update(item['dest_key'], item['size'], success)

    progress.finish()
    return len(progress.failed_files) == 0


def transfer_data(client, source, dest, recursive=True, parallel=10,
                 dry_run=False, verbose=False, **kwargs):
    """
    Main transfer orchestrator - routes to appropriate transfer method.

    Args:
        client: anatools client
        source: Source location (volumeId[:prefix] or path)
        dest: Destination location (volumeId[:prefix] or path)
        recursive: Transfer recursively
        parallel: Number of parallel workers
        dry_run: Don't actually transfer
        verbose: Verbose output
        **kwargs: Ignored (for backward compatibility)

    Returns:
        bool: True if successful
    """
    # Parse locations
    src = parse_transfer_location(source)
    dst = parse_transfer_location(dest)

    if verbose:
        print(f"Source: {src}")
        print(f"Destination: {dst}")

    # Route to appropriate transfer method
    if src['type'] == 'volume' and dst['type'] == 'volume':
        # Volume to volume (S3 to S3)
        return s3_to_s3_transfer(
            client, src['volumeId'], src['prefix'],
            dst['volumeId'], dst['prefix'],
            recursive, parallel, dry_run, verbose
        )
    elif src['type'] == 'local' and dst['type'] == 'volume':
        # Local to volume (upload)
        return local_to_s3_transfer(
            client, src['prefix'], dst['volumeId'], dst['prefix'],
            recursive, parallel, dry_run, verbose
        )
    elif src['type'] == 'volume' and dst['type'] == 'local':
        # Volume to local (download)
        return s3_to_local_transfer(
            client, src['volumeId'], src['prefix'], dst['prefix'],
            recursive, parallel, dry_run, verbose
        )
    else:
        # Local to local (not implemented - use cp/rsync)
        print_color("Local-to-local transfer not supported. Use 'cp' or 'rsync' instead.", 'error')
        return False
