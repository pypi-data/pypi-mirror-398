from dataclasses import dataclass
from typing import Union, List

import pandas as pd

__version__ = "0.1.0"

class RowLengthNotSameError(Exception):
    def __str__(self):
        return "lengths of rows aren't the same."


def _check_length(fwf_l: List[str], enc: str):
    lenb = lambda x: len(x.encode(enc))
    if len({lenb(x) for x in fwf_l}) != 1:
        raise RowLengthNotSameError


def to_fwf(self, metadata: List[tuple[str, int]], enc):
    """method to make a list of fixed width format strings from
    a dataframe.
    :param metadata: list of data type designation and length
    :type metadata: list[tuple[str, int]]
    :param enc: encoding
    """
    for i, (kind, length) in enumerate(metadata):
        col = self.columns[i]
        match kind:
            case "9":
                self[col] = self[col].astype(str).str.zfill(length)
            case "X":
                self[col] = self[col].astype(str).str.ljust(length)
    _check_length(lines := [f"{"".join(x)}\n" for x in self.values.tolist()], enc)
    return lines


setattr(pd.DataFrame, "to_fwf", to_fwf)


def parse_fwf(file, params: dict[str, int], enc):
    """method to make a dataframe from fixed width format file.
    :param file: file path
    :param params: params dictionary
    :type params: dict[str, int]
    :param enc: encoding
    """
    with open(file, "r", encoding=enc) as f:
        rows, lines, errors = [[] for _ in range(3)]
        for i, line in enumerate(f):
            lines.append(line)
            row, base, _has_error = [], 0, False
            for length in params.values():
                edge = base + length
                buf = line.encode(enc)[base:edge]
                try:
                    row.append(buf.decode(enc))
                except UnicodeDecodeError as e:
                    errors.append((i, e))
                    _has_error = True
                    break
                base += length
            if not _has_error:
                rows.append(row)
        df = pd.DataFrame(rows, columns=list(params.keys()))
        return {"df": df, "errors": errors, "lines": lines}


setattr(pd, "parse_fwf", parse_fwf)


@dataclass
class Fwf:
    encoding: str = None
    header: Union[str, list, None] = None
    contents: Union[str, list, None] = None
    footer: Union[str, list, None] = None

    @property
    def data(self):
        retval = []
        for p in (self.header, self.contents, self.footer):
            if p:
                if not isinstance(p, list):
                    p = [p]
                retval.extend(self._flatten(p))
        _check_length(retval, self.encoding)
        return retval

    def _flatten(self, l):
        retval = []
        for elm in l:
            if isinstance(elm, list):
                retval.extend(self._flatten(elm))
            else:
                retval.append(elm)
        return retval


def fwf_row(info, enc):
    metadata = [tuple(x[1:]) for x in info.values()]
    for k, v in info.items():
        info[k] = [v[0]]
    return pd.DataFrame(info).to_fwf(metadata, enc)
