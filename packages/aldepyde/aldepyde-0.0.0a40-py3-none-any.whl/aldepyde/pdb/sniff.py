def is_mmcif(text:str) -> bool:
    for line in text.split('\n'):
        if line.startswith('#'):
            continue
        # First non-comment line must be data_{PDB} code
        if text.strip().startswith('data_'):
            return True
        else:
            return False

def _detect_gz(filepath):
    with open(filepath, 'rb') as fp:
        head = fp.read(2)
        if b"\x1f\x8b" in head:
            return True
    return False
