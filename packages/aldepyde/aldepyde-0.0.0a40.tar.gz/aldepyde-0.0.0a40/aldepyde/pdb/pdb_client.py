from io import BytesIO

from aldepyde.databases.RemoteFileHandler import RemoteFileHandler
from aldepyde import get_cache

EXTENSIONS = {'pdb', 'mmcif'}
PDB_URL = "https://files.rcsb.org/pub/pdb/data/structures/divided/"

class pdb_Client():
    def attempt_cache(self, file) -> BytesIO|None:
        cache_path = get_cache().retrieve(file)
        if cache_path is None:
            return None
        else:
            with open(cache_path, 'rb') as fp:
                return BytesIO(fp.read())

    def fetch(self, code, extension='mmcif'):
        code = code.lower().strip()
        extension = extension.lower().strip()
        if extension == 'pdb':
            filepath = f"pdb/{code[1:3]}/pdb{code}.ent.gz"
            name = f"pdb{code}.ent.gz"
        elif extension == 'mmcif':
            filepath = f"mmCIF/{code[1:3]}/{code}.cif.gz"
            name = f"{code}.cif.gz"
        else:
            raise ValueError(f"Invalid file extension {extension}.\nAllowed values are {EXTENSIONS}\n")
        c_attempt = self.attempt_cache(name)
        if c_attempt is not None:
            return c_attempt
        fetch_url = PDB_URL + filepath
        data = RemoteFileHandler.fetch_url(fetch_url)
        get_cache().save_to_cache(data, name)
        return data

