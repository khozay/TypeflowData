import os
import sys
import json
import zipfile
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

APK_PATH = "/home/khozy/Projects/Typeflow/references/yandex_keyboard/ru.yandex.androidkeyboard.apk"
OUTPUT_DIR = "/home/khozy/Projects/TypeflowData/dictionaries"
MANIFEST_PATH = "/home/khozy/Projects/TypeflowData/dictionaries.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with zipfile.ZipFile(APK_PATH, 'r') as z:
    config = json.loads(z.read('assets/downloading_dicts_configuration.json').decode('utf-8'))

tasks = []
manifest = {}

for lang, items in config.items():
    if lang == 'shared':
        for item in items:
            name = item.get('name')
            if name in ('whitelist', 'multi_autocc'):
                url = item['url']
                md5 = item['md5']
                filename = f"{name}_{item.get('executable_file', name)}"
                tasks.append({
                    'lang': 'shared',
                    'name': name,
                    'filename': filename,
                    'url': url,
                    'expected_md5': md5,
                    'expected_size': item.get('download_size', 0),
                    'version': item.get('version', '1.0'),
                    'executable_file': item.get('executable_file', name),
                    'is_zip': False
                })
        continue

    for item in items:
        if item.get('name') == 'main':
            url = item['url']
            md5 = item['md5']
            filename = f"{lang}.zip"
            tasks.append({
                'lang': lang,
                'name': 'main',
                'filename': filename,
                'url': url,
                'expected_md5': md5,
                'expected_size': item.get('download_size', 0),
                'unpacked_size': item.get('unpacked_size', 0),
                'version': item.get('version', '1.0'),
                'executable_file': item.get('executable_file', f"main_{lang}"),
                'is_zip': True
            })

print(f"Total files to process: {len(tasks)}")

def verify_file(filepath, expected_md5):
    if not os.path.isfile(filepath):
        return False, None, None
    hasher_md5 = hashlib.md5()
    hasher_sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher_md5.update(chunk)
            hasher_sha256.update(chunk)
    actual_md5 = hasher_md5.hexdigest()
    actual_sha256 = hasher_sha256.hexdigest()
    return actual_md5.lower() == expected_md5.lower(), actual_md5, actual_sha256

def download_task(task):
    filepath = os.path.join(OUTPUT_DIR, task['filename'])
    valid, cur_md5, cur_sha256 = verify_file(filepath, task['expected_md5'])
    if valid:
        return task, filepath, cur_md5, cur_sha256, False

    temp_path = filepath + ".tmp"
    req = urllib.request.Request(task['url'], headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as resp, open(temp_path, 'wb') as out_f:
        while chunk := resp.read(65536):
            out_f.write(chunk)

    if os.path.exists(filepath):
        os.remove(filepath)
    os.rename(temp_path, filepath)

    valid, cur_md5, cur_sha256 = verify_file(filepath, task['expected_md5'])
    if not valid:
        raise ValueError(f"MD5 mismatch for {task['filename']}: expected {task['expected_md5']}, got {cur_md5}")

    return task, filepath, cur_md5, cur_sha256, True

print("Starting concurrent downloads...")
results = []
downloaded_count = 0
reused_count = 0

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(download_task, t): t for t in tasks}
    for fut in as_completed(futures):
        task_info = futures[fut]
        try:
            task, filepath, file_md5, file_sha256, was_downloaded = fut.result()
            results.append({
                'lang': task['lang'],
                'name': task['name'],
                'filename': task['filename'],
                'url': task['url'],
                'version': task['version'],
                'size': os.path.getsize(filepath),
                'md5': file_md5,
                'sha256': file_sha256,
                'executable_file': task['executable_file']
            })
            if was_downloaded:
                downloaded_count += 1
                print(f"[{downloaded_count + reused_count}/{len(tasks)}] Downloaded {task['filename']} ({os.path.getsize(filepath)/(1024*1024):.2f} MB)")
            else:
                reused_count += 1
                print(f"[{downloaded_count + reused_count}/{len(tasks)}] Verified existing {task['filename']}")
        except Exception as e:
            print(f"FAILED {task_info['filename']}: {e}", file=sys.stderr)

results.sort(key=lambda x: x['lang'])
manifest = {
    'total_languages': len([r for r in results if r['lang'] != 'shared']),
    'total_files': len(results),
    'total_bytes': sum(r['size'] for r in results),
    'items': results
}

with open(MANIFEST_PATH, 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"\nDone! Downloaded: {downloaded_count}, Existing: {reused_count}")
print(f"Total size on disk: {manifest['total_bytes'] / (1024*1024):.2f} MB")
print(f"Manifest saved to: {MANIFEST_PATH}")
