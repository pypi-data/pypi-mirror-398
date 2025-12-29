import os

import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from qdiff.states import States


class SmellDiff:
    def __init__(self, key_cols:list, description_col:list):
        self.key_cols = key_cols
        self.all_cols = key_cols + description_col
        self.description_col = description_col[0] if len(description_col) == 1 else None
        # key_cols = ["Package", "Class", "Method", "Smell"]
        # all_cols = key_cols + ["Description"]

    def _read_csv(self, csv_old, csv_new):
        if not os.path.exists(csv_old):
            raise FileNotFoundError(csv_old)
        if not os.path.exists(csv_new):
            raise FileNotFoundError(csv_new)

        # Read CSVs
        df_old = pd.read_csv(csv_old)
        df_new = pd.read_csv(csv_new)

        # Normalize text to avoid false diffs
        df_old = df_old.fillna("").astype(str)
        df_new = df_new.fillna("").astype(str)
        return df_old, df_new

    def _group_rows(self, df):
        grouped = {}
        for _, row in df.iterrows():
            key = tuple(row[k] for k in self.key_cols)
            grouped.setdefault(key, []).append(row.to_dict())
        return grouped

    def diff_csv(self, csv_old, csv_new, output_path):
        df_old, df_new = self._read_csv(csv_old, csv_new)
        diff_df = self.diff(df_old, df_new)
        # Write output
        diff_df.to_csv(output_path, index=False)
        print(f"Diff written to {output_path}")

    def diff(self, df_old:DataFrame, df_new:DataFrame) -> DataFrame:
        extra_cols = [c for c in df_old.columns if c not in self.all_cols]
        old_groups = self._group_rows(df_old)
        new_groups = self._group_rows(df_new)

        all_keys = set(old_groups.keys()) | set(new_groups.keys())
        rows = []

        for key in all_keys:
            old_rows = old_groups.get(key, [])
            new_rows = new_groups.get(key, [])

            # Build sets of descriptions for comparison
            if self.description_col:
                old_descs = set(r[self.description_col] for r in old_rows)
                new_descs = set(r[self.description_col] for r in new_rows)

                # Unchanged
                for desc in old_descs & new_descs:
                    # pick one row from new_rows for extra columns
                    new_row = next(r for r in new_rows if r[self.description_col] == desc)
                    row = {**{k: v for k, v in zip(self.key_cols, key)}, self.description_col: desc,
                           "State": States.UNCHANGED.value}
                    for c in extra_cols:
                        row[c] = new_row[c]
                    rows.append(row)

                # Modified
                for desc in new_descs - old_descs:
                    new_row = next(r for r in new_rows if r[self.description_col] == desc)
                    row = {**{k: v for k, v in zip(self.key_cols, key)}, self.description_col: desc, "State": States.MODIFIED.value}
                    for c in extra_cols:
                        row[c] = new_row[c]
                    rows.append(row)
            else:
                if key in new_groups and key in old_groups:
                    src = new_rows[0]
                    row = {c: src[c] for c in self.key_cols}
                    row["State"] = States.UNCHANGED.value
                    for c in extra_cols:
                        row[c] = src[c]
                    rows.append(row)

            # New (keys only in new)
            if key not in old_groups:
                for new_row in new_rows:
                    if self.description_col:
                        row = {**{k: v for k, v in zip(self.key_cols, key)}, self.description_col: new_row[self.description_col],
                               "State": States.NEW.value}
                    else:
                        row = {**{k: v for k, v in zip(self.key_cols, key)},
                               "State": States.NEW.value}
                    for c in extra_cols:
                        row[c] = new_row[c]
                    rows.append(row)

            # Removed (keys only in old)
            if key not in new_groups:
                for old_row in old_rows:
                    if self.description_col:
                        row = {**{k: v for k, v in zip(self.key_cols, key)}, self.description_col: old_row[self.description_col],
                           "State": States.REMOVED.value}
                    else:
                        row = {**{k: v for k, v in zip(self.key_cols, key)},
                               "State": States.REMOVED.value}
                    for c in extra_cols:
                        row[c] = old_row[c]
                    rows.append(row)
        result_df = pd.DataFrame(rows)
        return result_df
