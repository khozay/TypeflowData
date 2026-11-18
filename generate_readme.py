import json

with open('/home/khozy/Projects/TypeflowData/dictionaries.json', 'r') as f:
    data = json.load(f)

lines = [
    '# TypeflowData - Language Dictionaries & Models',
    '',
    'Official compound dictionary models and NLP assets for [Typeflow Keyboard](https://github.com/khozay/Typeflow).',
    '',
    f'**Total Languages Supported:** {data["total_languages"]}  ',
    f'**Total Archive Size:** {data["total_bytes"] / (1024*1024):.2f} MB  ',
    '**Release Tag:** `v1.0.0`  ',
    '',
    'These models are unpacked at runtime into `main_<lang>` and directly loaded by Typeflow\'s native C++ suggestion engine (`libjni_ykeyboard3.so`) for continuous autocomplete, neural ranking, and autocorrection.',
    '',
    '## Available Dictionaries',
    '',
    '| Language | Code | Archive | Size | Version | Direct Download |',
    '| :--- | :--- | :--- | :--- | :--- | :--- |'
]

for item in data['items']:
    lang = item['lang']
    fn = item['filename']
    sz_mb = f"{item['size'] / (1024*1024):.2f} MB"
    ver = item['version']
    dl_url = f"https://github.com/khozay/TypeflowData/releases/download/v1.0.0/{fn}"
    lines.append(f"| **{lang.upper()}** | `{lang}` | `{fn}` | {sz_mb} | {ver} | [Download]({dl_url}) |")

with open('/home/khozy/Projects/TypeflowData/README.md', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print("Successfully generated README.md")
