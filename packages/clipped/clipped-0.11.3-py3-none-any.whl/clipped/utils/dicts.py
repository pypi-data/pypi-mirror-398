from typing import Dict, List, Optional, Tuple

from clipped.utils.humanize import humanize_attrs


def deep_update(config: Dict, override_config: Dict):
    for k, v in override_config.items():
        if isinstance(v, dict):
            k_config = config.get(k, {})
            if isinstance(k_config, dict):
                v_config = deep_update(k_config, v)
                config[k] = v_config
            else:
                config[k] = v
        else:
            config[k] = override_config[k]
    return config


def flatten_keys(
    objects: List[Dict], columns: List[str], columns_prefix: Optional[Dict] = None
) -> Tuple[List[Dict], Dict]:
    # Extend run with params_keys
    keys = set([])
    columns_prefix = columns_prefix or {}
    prefixed_columns = {}

    def process_objects():
        results = {}
        for k, v in col_values.items():
            results["{}.{}".format(column_prefix, k)] = v
            prefixed_columns[k] = "{}.{}".format(column_prefix, k)
        return results

    for col in columns:
        for obj in objects:
            col_values = obj.pop(col, {}) or {}
            if col in columns_prefix:
                column_prefix = columns_prefix[col]
                col_values = process_objects()
            col_keys = col_values.keys()
            keys |= set(col_keys)
            obj.update(col_values)

    # Check that all obj have all metrics
    # TODO: optimize this process
    for obj in objects:
        obj_keys = set(obj.keys())
        for key in keys:
            if key not in obj_keys:
                obj[key] = None

    return objects, prefixed_columns


def list_dicts_to_tabulate(
    list_dicts,
    exclude_attrs=None,
    include_attrs=None,
    humanize_values=True,
    upper_keys: bool = True,
):
    exclude_attrs = exclude_attrs or {}
    results = []
    if include_attrs:  # If include_attrs disable exclude_attrs
        exclude_attrs = {}
    for d_value in list_dicts:
        r_value = {}
        for k, v in d_value.items():
            if k in exclude_attrs:
                continue
            if include_attrs and k not in include_attrs:
                continue

            if humanize_values:
                v = humanize_attrs(k, v)

            if upper_keys:
                k = k.upper()
            r_value[k] = v
        results.append(r_value)
    return results


def list_dicts_to_csv(
    list_dicts,
    exclude_attrs=None,
    include_attrs=None,
):
    exclude_attrs = exclude_attrs or {}
    results = []
    if include_attrs:  # If include_attrs disable exclude_attrs
        exclude_attrs = {}
    for d_value in list_dicts:
        result = {}
        for k, v in d_value.items():
            if k in exclude_attrs:
                continue
            if include_attrs and k not in include_attrs:
                continue
            result[k] = v
        results.append(result)

    return results


def dict_to_tabulate(
    d_value,
    exclude_attrs=None,
    humanize_values=True,
    rounding: int = 2,
    timesince: bool = True,
):
    exclude_attrs = exclude_attrs or {}
    results = {}
    if hasattr(d_value, "to_dict"):
        d_value = d_value.to_dict()
    for k, v in d_value.items():
        if k in exclude_attrs:
            continue

        if humanize_values:
            v = humanize_attrs(k, v, rounding=rounding, timesince=timesince)

        results[k.upper()] = v

    return results
