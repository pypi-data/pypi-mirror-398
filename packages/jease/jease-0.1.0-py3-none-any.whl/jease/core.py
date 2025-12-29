import json
from copy import deepcopy
from collections.abc import Mapping

class JEase:
    def __init__(self, data):
        self.data = deepcopy(data)  # avoid modifying original

    # ---------------- Core Access ----------------
    def get(self, key_path, default=None):
        keys = key_path.split(".")
        result = self.data
        try:
            for key in keys:
                if isinstance(result, list):
                    result = [r.get(key, default) if isinstance(r, dict) else default for r in result]
                else:
                    result = result.get(key, default)
        except Exception:
            return default
        return JEase(result) if isinstance(result, (dict, list)) else result

    # ---------------- Filtering ----------------
    def filter(self, **conditions):
        if not isinstance(self.data, list):
            raise TypeError("Filter works only on lists of dicts")
        filtered = []
        for item in self.data:
            match = True
            for k, v in conditions.items():
                if "__" in k:
                    key, op = k.split("__")
                    value = item.get(key)
                    if op == "gte" and not (value >= v):
                        match = False
                    elif op == "lte" and not (value <= v):
                        match = False
                    elif op == "eq" and not (value == v):
                        match = False
                else:
                    if item.get(k) != v:
                        match = False
            if match:
                filtered.append(item)
        self.data = filtered
        return self

    # ---------------- Mapping ----------------
    def map(self, key_or_func, default=None):
        if isinstance(self.data, list):
            result = []
            for item in self.data:
                if callable(key_or_func):
                    result.append(key_or_func(item))
                else:
                    keys = key_or_func.split(".")
                    val = item
                    for k in keys:
                        val = val.get(k, default) if isinstance(val, dict) else default
                    result.append(val)
            self.data = result
        return self

    # Shortcut to pluck
    def pluck(self, key, default=None):
        return self.map(key, default)

    # ---------------- Sorting ----------------
    def sort(self, key, desc=False):
        if isinstance(self.data, list):
            def get_val(item):
                keys = key.split(".")
                val = item
                for k in keys:
                    val = val.get(k, None) if isinstance(val, dict) else None
                return val
            self.data.sort(key=get_val, reverse=desc)
        return self

    # ---------------- Aggregation ----------------
    def aggregate(self, key, func="sum"):
        if not isinstance(self.data, list):
            raise TypeError("Aggregate works only on lists of dicts")
        values = []
        for item in self.data:
            val = item
            for k in key.split("."):
                val = val.get(k, None) if isinstance(val, dict) else None
            if val is not None:
                values.append(val)
        if func == "sum":
            return sum(values)
        elif func == "mean":
            return sum(values) / len(values) if values else 0
        elif func == "min":
            return min(values) if values else None
        elif func == "max":
            return max(values) if values else None
        elif func == "count":
            return len(values)
        elif func == "median":
            if not values:
                return None
            values.sort()
            n = len(values)
            mid = n // 2
            if n % 2 == 0:
                return (values[mid-1] + values[mid]) / 2
            return values[mid]
        else:
            raise ValueError("Unknown aggregate function")

    # ---------------- Mutation ----------------
    def update(self, key_path, value):
        def _update(obj, keys, val):
            if len(keys) == 1:
                if isinstance(obj, dict):
                    obj[keys[0]] = val
            else:
                if isinstance(obj, dict):
                    if keys[0] not in obj or not isinstance(obj[keys[0]], dict):
                        obj[keys[0]] = {}
                    _update(obj[keys[0]], keys[1:], val)
                elif isinstance(obj, list):
                    for item in obj:
                        _update(item, keys, val)
        _update(self.data, key_path.split("."), value)
        return self

    def remove(self, key_path):
        def _remove(obj, keys):
            if len(keys) == 1:
                if isinstance(obj, dict) and keys[0] in obj:
                    del obj[keys[0]]
            else:
                if isinstance(obj, dict) and keys[0] in obj:
                    _remove(obj[keys[0]], keys[1:])
                elif isinstance(obj, list):
                    for item in obj:
                        _remove(item, keys)
        _remove(self.data, key_path.split("."))
        return self

    def merge(self, other):
        def _merge(a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                for k, v in b.items():
                    if k in a and isinstance(a[k], dict) and isinstance(v, dict):
                        _merge(a[k], v)
                    else:
                        a[k] = deepcopy(v)
            elif isinstance(a, list) and isinstance(b, list):
                a.extend(deepcopy(b))
        _merge(self.data, other)
        return self

    # ---------------- Info / Helpers ----------------
    def keys(self):
        if isinstance(self.data, dict):
            return list(self.data.keys())
        elif isinstance(self.data, list) and all(isinstance(d, dict) for d in self.data):
            return [list(d.keys()) for d in self.data]
        return []

    def values(self):
        if isinstance(self.data, dict):
            return list(self.data.values())
        elif isinstance(self.data, list) and all(isinstance(d, dict) for d in self.data):
            return [list(d.values()) for d in self.data]
        return []

    def unique(self):
        if isinstance(self.data, list):
            self.data = list({json.dumps(v, sort_keys=True) if isinstance(v, dict) else v for v in self.data})
            # decode back dicts
            self.data = [json.loads(v) if isinstance(v, str) and v.startswith("{") else v for v in self.data]
        return self

    def length(self):
        if isinstance(self.data, list):
            return len(self.data)
        elif isinstance(self.data, dict):
            return len(self.data.keys())
        return 0

    def exists(self, key_path):
        keys = key_path.split(".")
        if isinstance(self.data, dict):
            d = self.data
            for k in keys:
                if not isinstance(d, dict) or k not in d:
                    return False
                d = d[k]
            return True
        elif isinstance(self.data, list):
            return all(JEase(d).exists(key_path) if isinstance(d, dict) else False for d in self.data)
        return False

    def to_list(self):
        return self.data

    # ---------------- Pretty / Display ----------------
    def show(self, pretty=True):
        if pretty:
            print(json.dumps(self.data, indent=2))
        else:
            print(self.data)
        return self

    def report(self):
        """Quick summary report for list of dicts"""
        if not isinstance(self.data, list):
            print("Not a list, cannot report.")
            return self
        count = len(self.data)
        numeric_keys = set()
        for item in self.data:
            if isinstance(item, dict):
                for k, v in item.items():
                    if isinstance(v, (int, float)):
                        numeric_keys.add(k)
        print(f"Items count: {count}")
        for k in numeric_keys:
            values = [item[k] for item in self.data if isinstance(item, dict) and k in item]
            print(f"{k}: min={min(values)}, max={max(values)}, mean={sum(values)/len(values):.2f}")
        return self
