import pandas as pd
import numpy as np
import re
from numbers import Number
from collections import deque
import ast

def read_hits_files(file_path, file_type="emu", return_df=True):
    delimiter = "|" if file_type == "fpga" else " "
    converters = {i: lambda s: int(s.split(':')[1].strip()) for i in range(5)} if file_type == "fpga" else None
    columns = ['id', 'bx', 'tdc', 'l', 'w'] if file_type == "fpga" else ['bxsend', 'sl', 'bx', 'tdc', 'l', 'w', 'id', 'event']

    data = np.loadtxt(
        file_path,
        delimiter=delimiter,
        dtype=int,
        converters=converters
    )

    if data.size == 0:  # Handle empty data array
        return pd.DataFrame() if return_df else {}

    if data.ndim == 1:  # Reshape single-row data to ensure correct dimensions
        data = data.reshape(1, -1)

    df = pd.DataFrame(data, columns=columns)
    wh, sc, st = map(int, re.search(r"wh(-?\d+)_sc(\d+)_st(\d+)", file_path).groups())
    df["wh"] = wh
    df["sc"] = sc
    df["st"] = st

    if file_type == "fpga":
        df["sl"] = 1 if "SL0" in file_path else (3 if "SL1" in file_path else None)

    return df if return_df else df.to_dict(orient="records")

def read_showers_files(file_path, file_type="emu", return_df=True):
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        if not content.strip():
            return pd.DataFrame()  # Return empty DataFrame if file is empty

        # Extract wh, sc, st from filename
        match = re.search(r"wh(-?\d+)_sc(\d+)_st(\d+)", file_path)
        if not match:
            raise ValueError("Filename must include 'wh-<n>_sc<nn>_st<n>' pattern.")
        wh, sc, st = map(int, match.groups())

        # Decide on split and SL logic
        if file_type == "emu":
            blocks = re.split(r'# Event ', content.strip())[1:]  # drop first if empty
            get_id = lambda lines: int(lines[0])
            sl = None
        elif file_type == "fpga":
            blocks = re.split(r'Index: ', content.strip())[1:]
            sl = 1 if "SL0" in content else (3 if "SL1" in content else None)
            get_id = lambda lines: int(lines[0])
        else:
            raise ValueError("file_type must be 'emu' or 'fpga'")

        # Optional key remapping
        key_map = {
            "WireCounter": "wires",
            "wiresprofile": "wires",
            "Max Wire": "maxw",
            "Min Wire": "minw",
            "ShowerBX": "bx",
        }

        data = []
        for block in blocks:
            lines = block.strip().splitlines()
            if not lines:
                continue

            entry = {
                "wh": wh,
                "sc": sc,
                "st": st,
                "event": None if file_type == "fpga" else get_id(lines),
                "index": None if file_type == "emu" else get_id(lines),
            }
            if sl is not None:
                entry["sl"] = sl

            for line in lines[1:]:
                if ':' not in line:
                    continue
                key, value = map(str.strip, line.split(':', 1))
                key = key.replace("_", "")
                key = key.replace("SL0", "").replace("SL1", "")
                key = key_map.get(key, key).lower()

                # Parse value (int, float, list, string)
                try:
                    if key == "wires" or key == "ids":
                        if file_type == "emu":
                            entry[key] = ast.literal_eval(value)
                        elif file_type == "fpga":
                            entry[key] = list(map(int, value.strip().split()))
                    elif '.' in value:
                        entry[key] = float(value)
                    else:
                        entry[key] = int(value)
                except Exception:
                    entry[key] = value  # fallback to raw string if parsing fails

            data.append(entry)

        return pd.DataFrame(data) if return_df else data
    except FileNotFoundError:
        return pd.DataFrame()  # Return empty DataFrame if file does not exist

def get_missing_hits(cmssw_df, fpga_df, columns):
    df1 = cmssw_df[columns].sort_values(by=list(columns)).reset_index(drop=True)
    df2 = fpga_df[columns].sort_values(by=list(columns)).reset_index(drop=True)
    
    missing_in_df2 = pd.merge(df1, df2, how='left', indicator=True)
    missing_in_df2 = missing_in_df2[missing_in_df2['_merge'] == 'left_only'].drop(columns=['_merge'])
    return missing_in_df2

def set_shower_event(showers_row, cmssw_hits_df):
    mask = cmssw_hits_df["id"].isin(showers_row["ids"])
    evn = cmssw_hits_df.loc[mask, "event"].drop_duplicates()
    event = evn.to_list()[0] if evn.size == 1 else evn.to_list()

    return event

def set_shower_bxsend(showers_row, cmssw_hits_df):
    if not "event" in showers_row:
        event = set_shower_event(showers_row, cmssw_hits_df)
    else:
        event = showers_row["event"]

    mask = cmssw_hits_df["event"] == (event if isinstance(event, Number) else event[0])

    last_bxsend, last_bx = cmssw_hits_df.sort_values("bx").loc[mask, ["bxsend", "bx"]].iloc[-1].values
    dbx = showers_row["bx"] - last_bx
    bxsend = last_bxsend + dbx
        
    return bxsend

def dump_hits_to_nhits(hits_df, buff_persistance=16):
    if not "bxsend" in hits_df.columns:
        raise KeyError("hits_df should contain bxsend column")
    _hits_df = hits_df.sort_values("bxsend").copy()
    hits_buffer = deque() # fifo of tuples (bx, [hit1, hit2, ...])
    nhits_trend = []

    min_bxsend = _hits_df["bxsend"].min()
    max_bxsend = _hits_df["bxsend"].max()
    
    for bxsend in range(min_bxsend, max_bxsend + 17):
        hits = _hits_df.loc[_hits_df["bxsend"] == bxsend]

        if not hits.empty:
            hits_buffer.extend([(bxsend, hits["id"].to_list())])

        nhits = len(hits_buffer) if hits_buffer else 0

        nhits_trend.append([bxsend, nhits])
        while (hits_buffer and bxsend - hits_buffer[0][0] > buff_persistance):
            hits_buffer.popleft()

    return np.array(nhits_trend)

def match_shower(shower_row, ref_showers_df, by={"bxsend": 30}):
    matches = []
    for key, tolerance in by.items():
        if any( abs(ref_showers_df[key] - shower_row[key]) <= tolerance):
            matches.append(True)
        else:
            matches.append(False)
    return all(matches)

def compute_agreement(showers_df, ref_showers_df):
    if showers_df.empty and ref_showers_df.empty:
        return 1  # Agreement is perfect if both are empty
    elif showers_df.empty or ref_showers_df.empty:
        return 0  # Agreement is zero if only one is empty

    matches = showers_df.apply(match_shower, args=(ref_showers_df,), axis=1)
    agreement_ratio = matches.value_counts()[True] / matches.size
    return agreement_ratio