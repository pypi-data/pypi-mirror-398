import io
from typing import Tuple
from aldepyde.databases._database import local_database
import operator
from contextlib import nullcontext
import re

class scop_parser(local_database):
    #TODO Do we want to handle custom classes?
    regex = re.compile(b">[a-zA-Z0-9_.]* *[a-l](.[0-9]+)?(.[0-9]+)?(.[0-9]+)?")


    op = {
        "and": lambda a,b,c: a and b and c,
        "or": lambda a,b,c: a or b or c
    }

    def fetch(self, url):
        pass

    def fetch_code(self, codes):
        pass

    def parse(self, text):
        pass

    def extract_all_scop(self):
        pass

    def partition_scope(self):
        pass

    def extract_all_astral(self):
        self.refresh()
        lines = self.fp.readlines()
        entry = b""
        for line in lines:
            if line.startswith(b">") and len(entry) > 0:
                yield entry
                entry = b""
            entry += line
        yield entry

    # TODO allow a list of search parameters. Big challenge to make efficient, but could be cute

    def yield_astral(self, class_name:str=b'',contains_id:str=b'' , contains_desc:str=b'', mode:str="and", include_newline:bool=False):
        class_name, contains_desc, contains_id = self._bytify(class_name, contains_desc, contains_id)
        mode = self._validate_mode(mode)
        logic = scop_parser.op[mode]
        for line in self.extract_all_astral():
            identifiers = self.regex.search(line).group().split()
            id = identifiers[0]
            cls = identifiers[1]
            unmatched_spl = self.regex.sub(b'', line).split(b'\n')
            desc = unmatched_spl[0]
            if include_newline:
                sequence = b"\n".join(unmatched_spl[1:])
            else:
                sequence = b"".join(unmatched_spl[1:])
            if logic(class_name.lower() in cls.lower(), contains_id.lower() in id.lower(), contains_desc.lower() in desc.lower()):
                yield sequence


    # TODO Create a new function that yields everything in the dictionary. Don't be hacky to avoid creating a file
    def partition_astral(self, destination:None|str=None, append=False, class_name:str=b'',contains_id:str=b'' , contains_desc:str=b'', mode="and") -> dict:
        class_name, contains_desc, contains_id = self._bytify(class_name, contains_desc, contains_id)
        mode = self._validate_mode(mode)
        logic = scop_parser.op[mode]

        if append:
            file_context = open(destination, 'ab') if destination is not None else nullcontext(io.BytesIO())
        else:
            file_context = open(destination, 'wb') if destination is not None else nullcontext(io.BytesIO())
        with file_context as fp:
            ret_dict = dict()
            for line in self.extract_all_astral():
                identifiers = self.regex.search(line).group().split()
                id = identifiers[0]
                cls = identifiers[1]
                unmatched_spl = self.regex.sub(b'', line).split(b'\n')
                desc = unmatched_spl[0]
                sequence = b"\n".join(unmatched_spl[1:])
                if logic(class_name.lower() in cls.lower(), contains_id.lower() in id.lower(), contains_desc.lower() in desc.lower()):
                    ret_dict[id] = { # Yes, I know '>' isn't part of the FASTA identifier. This keeps things more consistant
                        "class" : cls,
                        "description" : desc,
                        "sequence" : sequence
                    }
                    fp.write(line)
        return ret_dict

    def add_entry_to_dict(self, data:dict, id:str|bytes, sequence:str|bytes, cls:bytes|str|None=None, description:bytes|str=b''):
        id, sequence, cls, description = self._bytify(id, sequence, cls, description)
        data[b'>'+id] = {
                        "class" : cls,
                        "description" : description,
                        "sequence" : sequence
                    }
        return data

    def add_entry_to_target_file(self, filepath:str, id:bytes|str, sequence:bytes|str, cls:bytes|str|None=None, description:bytes|str=''):
        sequence, cls, description = self._bytify(sequence, cls, description)
        sequence = sequence + b'\n' if sequence[-1] != b'\n' else sequence
        entry = {
                    "class" : cls,
                    "description" : description,
                    "sequence" : sequence
                    }
        id_code = f'>{id}'.encode('utf-8')
        d = {id_code:entry}
        self.write_from_dict(d, destination=filepath, append=True)


    # Just simple dictionary union for now. Maybe later detect clashes?
    def combine_data(self, d1:dict, d2:dict) -> dict:
        return d1 | d2

    def add_label(self, data:dict, label:str, class_name:str=b'',
                  contains_id:str=b'' , contains_desc:str=b'', mode="and",
                  add_to_end:bool=False) -> dict:
        mode = self._validate_mode(mode)
        class_name, contains_desc, contains_id, label = self._bytify(class_name, contains_desc, contains_id, label)
        logic = scop_parser.op[mode]
        for key in data.keys():
            cls = data[key]['class']
            desc = data[key]['description']
            id = key
            if logic(class_name.lower() in cls.lower(), contains_id.lower() in id.lower(),
                     contains_desc.lower() in desc.lower()):
                if add_to_end:
                    data[key]['description'] = data[key]['description'] + label
                else:
                    data[key]['description'] = label + data[key]['description']
        return data

    def write_from_dict(self, data:dict, destination:str, append:bool=False):
        if append:
            fp = open(destination, 'ab')
        else:
            fp = open(destination, 'wb')
        for key in data.keys():
            w_str = key + b' ' + data[key]['class'] + b' ' + data[key]['description'] + b'\n' + data[key]['sequence']
            fp.write(w_str)
        fp.close()

    def _bytify(self, *args:str|bytes|None) -> Tuple[bytes, ...]:
        r_lst = list()
        for arg in args:
            if isinstance(arg, str):
                r_lst.append(arg.encode('utf-8'))
            elif arg is None:
                r_lst.append(None)
            else:
                r_lst.append(arg)
        return tuple(r_lst)

    def _validate_mode(self, mode):
        mode = mode.strip()
        if mode == "":
            mode = 'and'
        if mode != "and" and mode != "or":
            raise ValueError(f"Invalid mode: {mode}\n\tmode must be \"and\" or \"or\".")
        return mode.lower()

    #TODO Make this iterable?