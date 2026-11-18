"""Verify a prepared patch, then create a ZIP and SHA-256 sidecar."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--archive-root', default='tomoyo-after-steam-cn-r18',
                        choices=('tomoyo-after-steam-cn-r18', 'tomoyo-after-steam-cn-all-ages'))
    args = parser.parse_args()
    package = args.package.resolve(strict=True)
    payload = (package / 'payload').resolve(strict=True)
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8-sig'))
    for item in manifest['files']:
        path = (payload / item['path']).resolve(strict=True)
        if not path.is_relative_to(payload):
            raise ValueError(f'Path outside payload: {item["path"]}')
        if path.stat().st_size != item['size'] or sha256(path) != item['sha256']:
            raise ValueError(f'Manifest mismatch: {item["path"]}')
    print(f'Validated {len(manifest["files"])} payload files.', flush=True)
    output = args.output.resolve()
    if output.is_relative_to(package):
        raise ValueError('Output must be outside the input package.')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    partial = output.with_suffix(output.suffix + '.partial')
    if partial.exists():
        raise FileExistsError(partial)
    with zipfile.ZipFile(partial, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                archive.write(path, Path(args.archive_root) / path.relative_to(package))
    with zipfile.ZipFile(partial) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'ZIP CRC mismatch: {bad}')
    partial.rename(output)
    digest = sha256(output)
    sidecar = output.with_suffix(output.suffix + '.sha256')
    sidecar.write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    print(json.dumps({'path': str(output), 'bytes': output.stat().st_size, 'sha256': digest}), flush=True)


if __name__ == '__main__':
    main()
