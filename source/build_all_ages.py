"""Build the Steam-based all-ages overlay from local disassembly inputs."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

from patch_bytecode import compressed, u32


def load_scene(research, edition, name):
    raw = (research / f'{edition}-raw' / f'{name}.rl').read_bytes()
    info = json.loads((research / f'{edition}-json' / f'{name}.rl.json').read_text(encoding='utf-8'))
    start = u32(raw, 32)
    code = raw[start:]
    commands = info['commands']
    spans = [(c, code[c['offset']:end]) for c, end in
             zip(commands, [c['offset'] for c in commands[1:]] + [len(code)])]
    return raw, info, spans


def choice(data):
    # Unconditional select: preserve original option separators and source lines.
    if data[:4] != b'\x23\x00\x02\x01' or data[7:9] != b'\x00{' or not data.endswith(b'}'):
        return None
    fields = []
    pos = 9
    for _ in range(int.from_bytes(data[5:7], 'little')):
        if data[pos:pos + 1] != b'\n' or data[pos + 3:pos + 4] != b'"':
            return None
        end = data.find(b'"', pos + 4)
        if end < 0 or b'\\' in data[pos + 4:end]:
            return None
        fields.append((pos + 3, end + 1))
        pos = end + 1
    if data[pos:pos + 1] != b'\n' or pos + 4 != len(data):
        return None
    return fields


def anchors(spans):
    result = []
    for idx, (command, data) in enumerate(spans):
        if command['hidden'] or command['type'] in ('kidoku', 'textout'):
            continue
        key = re.sub(r'@@PTR=\d+@@', '@', command['text'])
        if key.startswith('koePlay ('):
            key = 'koePlay'
        elif key.startswith('select(') and choice(data):
            key = ('select', len(choice(data)))
        result.append((idx, key))
    return result


def edits_for_scene(steam, translated):
    edits = []
    a, b = anchors(steam), anchors(translated)
    matcher = SequenceMatcher(None, [key for _, key in a], [key for _, key in b], autojunk=False)
    prev_a = prev_b = -1
    for block in matcher.get_matching_blocks():
        if block.size:
            pairs = [(a[block.a + i][0], b[block.b + i][0]) for i in range(block.size)]
        else:
            pairs = [(len(steam), len(translated))]
        for ai, bi in pairs:
            left = [x for x in steam[prev_a + 1:ai] if x[0]['type'] == 'textout']
            right = [x for x in translated[prev_b + 1:bi] if x[0]['type'] == 'textout']
            if len(left) == len(right):
                for (cmd, old), (_, new) in zip(left, right):
                    speaker = b'\x81\x79'
                    if old != new and (speaker in old) == (speaker in new):
                        try:
                            decoded = new.decode('gbk')
                        except UnicodeDecodeError:
                            continue
                        if any('\u4e00' <= ch <= '\u9fff' for ch in decoded):
                            edits.append((cmd['offset'], old, new, 'dialogue'))
            if ai < len(steam):
                cmd, old = steam[ai]
                new = translated[bi][1]
                af = choice(old)
                bf = choice(new)
                if af and bf and len(af) == len(bf):
                    replacement = bytearray(old)
                    for (start, end), (source_start, source_end) in reversed(list(zip(af, bf))):
                        replacement[start:end] = new[source_start:source_end]
                    if replacement != old:
                        edits.append((cmd['offset'], old, bytes(replacement), 'choice'))
            prev_a, prev_b = ai, bi
    return edits


def rewrite(raw, info, edits):
    start = u32(raw, 32)
    code = bytearray(raw[start:])
    header = bytearray(raw[:start])

    def shifted(offset):
        return offset + sum(len(new) - len(old) for at, old, new, _ in edits if at < offset)

    for site, target in (info['relocations'] or {}).items():
        pos = int(site) - start
        assert all(not (at <= pos < at + len(old)) for at, old, _, _ in edits)
        assert all(not (at < target < at + len(old)) for at, old, _, _ in edits)
        struct.pack_into('<I', code, pos, shifted(target))
    for i in range(100):
        pos = 0x34 + 4 * i
        target = u32(header, pos)
        if target:
            struct.pack_into('<I', header, pos, shifted(target))
    for at, old, new, _ in reversed(edits):
        assert code[at:at + len(old)] == old
        code[at:at + len(old)] = new
    result = header + code
    struct.pack_into('<I', result, 0x24, len(code))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--r18-package', type=Path, required=True)
    args = parser.parse_args()
    source, output, r18 = args.research, args.output, args.r18_package
    payload = output / 'payload'
    (payload / 'TXT').mkdir(parents=True)
    names = {file.name for file in (source / 'allages-extracted/TXT').glob('*.TXT')}
    names.add('SEEN9030.TXT')
    counts = {}
    audit = output / 'local-audit'
    audit.mkdir()
    for name in sorted(names):
        if not (source / 'steam-raw' / f'{name}.rl').exists():
            continue
        raw, info, steam = load_scene(source, 'steam', name)
        if name == 'SEEN9030.TXT':
            entry = next(cmd for cmd, _ in steam if cmd['text'] == '#entrypoint 000')
            bridge = next(cmd for cmd, _ in steam if '(9840, 0, special<0>(27))' in cmd['text'])
            following = next(cmd for cmd, _ in steam if cmd['offset'] > bridge['offset'])
            edits = [(entry['offset'] + 3, b'', bytes.fromhex('2302010c000100002824ff0e00000029'), 'init'),
                     (following['offset'], b'', bytes.fromhex('2302010c000200012824ff0e00000024ff0100000029'), 'diagnostic')]
        else:
            _, _, translated = load_scene(source, 'allages', name)
            edits = edits_for_scene(steam, translated)
        if edits:
            result = rewrite(raw, info, edits)
            (audit / f'{name}.rl').write_bytes(result)
            (payload / 'TXT' / name).write_bytes(compressed(result, source))
            counts[name] = dict(Counter(kind for _, _, _, kind in edits))
            counts[name]['steam_dialogue'] = sum(cmd['type'] == 'textout' for cmd, _ in steam)
    ini = (source / 'steam-original-backup/GAMEEXE.INI').read_bytes()
    for key, value in {
        b'CAPTION': b'"Tomoyo After - Steam Chinese All Ages"',
        b'FOLDNAME.TXT': b'"TXT" = 2 : "SEEN.TXT"',
    }.items():
        ini, replaced = re.subn(rb'(?m)^#' + re.escape(key) + rb'[ \t]*=[^\r\n]*', b'#' + key + b'=' + value, ini)
        assert replaced == 1, key
    ini += b'\r\n#ALL_FONT_USE=1\r\n#INIT_FONT_NAME="SimHei"\r\n#DLL.014="ta_cn"\r\n'
    (payload / 'Gameexe.ini').write_bytes(ini)
    shutil.copy2(r18 / 'payload/ta_cn.dll', payload)
    for name in ['Manage-Patch.ps1', '安装补丁.cmd', '卸载并恢复原版.cmd', '校验补丁.cmd', '原汉化版本说明.txt']:
        shutil.copy2(r18 / name, output)
    manifest = json.loads((r18 / 'manifest.json').read_text(encoding='utf-8'))
    manifest['version'] = '0.1.0-all-ages-experimental'
    manifest['originals'].append({
        'path': 'SEEN.TXT', 'sha256': hashlib.sha256((source / 'steam-original-backup/SEEN.TXT').read_bytes()).hexdigest(),
    })
    manifest['files'] = [{'path': str(file.relative_to(payload)), 'size': file.stat().st_size,
                          'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
                         for file in sorted(payload.rglob('*')) if file.is_file()]
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / '汉化覆盖记录.json').write_text(json.dumps(counts, indent=2), encoding='utf-8')
    print(len(counts), 'scenes;', sum(x.get('dialogue', 0) for x in counts.values()), 'dialogues;',
          sum(x.get('choice', 0) for x in counts.values()), 'choices')


if __name__ == '__main__':
    main()
