import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

DICT_DIR = "/home/khozy/Projects/TypeflowData/dictionaries"
TAG = "v1.0.0"

files = [f for f in sorted(os.listdir(DICT_DIR)) if not f.endswith('.tmp')]
total = len(files)
print(f"Total assets to upload: {total}")

def upload_file(filename):
    filepath = os.path.join(DICT_DIR, filename)
    cmd = ["gh", "release", "upload", TAG, filepath, "--clobber"]
    for attempt in range(3):
        res = subprocess.run(cmd, cwd="/home/khozy/Projects/TypeflowData", capture_output=True, text=True)
        if res.returncode == 0:
            return filename, True, None
        time_to_wait = (attempt + 1) * 2
        import time; time.sleep(time_to_wait)
    return filename, False, res.stderr

completed = 0
failed = []

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(upload_file, fn): fn for fn in files}
    for fut in as_completed(futures):
        fn, success, err = fut.result()
        completed += 1
        if success:
            sz = os.path.getsize(os.path.join(DICT_DIR, fn)) / (1024 * 1024)
            print(f"[{completed}/{total}] Uploaded {fn} ({sz:.2f} MB)")
        else:
            print(f"[{completed}/{total}] FAILED {fn}: {err}", file=sys.stderr)
            failed.append(fn)

print(f"\nUpload complete! Successfully uploaded: {completed - len(failed)}/{total}")
if failed:
    print(f"Failed files: {failed}", file=sys.stderr)
    sys.exit(1)
