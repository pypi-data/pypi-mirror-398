import pandas as pd
import anndata

def _get_value_info(value, key_name=None, is_top_level_anndata_component=False, 
                    level_of_value=None, max_depth = 3, n_to_show = 4, limited_keys=None):
    """Helper to format the value's type/shape/info for printing."""
    info_str = f"({type(value).__name__})"

    if key_name and key_name in limited_keys:
        return "(dict) --"

    if isinstance(value, pd.DataFrame):
        # For top-level AnnData components like obs/var, show full columns
        if True: # is_top_level_anndata_component:
            if len(value.columns.tolist()) > n_to_show:
                lst = value.columns.tolist()[:n_to_show]
                lst.append('...')
                info_str = f"DataFrame {value.shape}, cols=[{', '.join(lst)} ])"
            else:
                info_str = f"DataFrame {value.shape}, cols={value.columns.tolist()})"
        else:
            info_str = f"DataFrame (shape={value.shape}, {len(value.columns)} cols)"
    elif hasattr(value, 'shape') and hasattr(value, 'dtype'):
        if len(value.shape) == 0:
            info_str = f"{value}"
        elif (len(value.shape) == 1) and (value.shape[0] < 5):
            info_str = f"{value}"
        else:
            info_str = f"array (shape={value.shape}, dtype={value.dtype})"
    elif isinstance(value, dict):
        info_str = "(dict)"
        # Check if recursion for this dict will be stopped at the next level
        if level_of_value is not None and level_of_value >= max_depth:
            keys_to_show = list(value.keys())
            if keys_to_show:
                if len(keys_to_show) > n_to_show: # Limit display for very long key lists
                    info_str += f" Keys=[{', '.join(map(str, keys_to_show[:n_to_show]))}, ... ]" # (Max depth reached)"
                    # info_str += f" Keys: [{', '.join(map(str, keys_to_show))}]" # (Max depth reached)"
                else:
                    info_str += f" Keys=[{', '.join(map(str, keys_to_show))}]" # (Max depth reached)"
            else:
                info_str += " (empty dictionary at max depth)"
    elif isinstance(value, str):
        if len(value) < 80: # Display short strings directly
            info_str = f"'{value}'"
        else:
            info_str = "(str)"
    elif isinstance(value, (int, float, bool)):
        info_str = str(value)
    elif value is None:
        info_str = "None"
    
    return info_str

def _display_dict_or_dataframe_recursive(current_obj, current_depth, parent_prefix, 
                                         max_depth = 3, n_to_show = 4, limited_keys = None ):
    # The max_depth check here is now primarily for stopping further recursion
    # The 'Max depth reached' message is handled by _get_value_info for dicts.
    if current_depth >= max_depth:
        return # Stop further recursion
    
    if isinstance(current_obj, dict) or hasattr(current_obj, 'keys'):
        if not current_obj:
            print(f"{parent_prefix}└── (empty)")
            return
        
        keys = list(current_obj.keys())
        max_key_len = max(len(str(k)) for k in keys) if keys else 0

        for i, key in enumerate(keys):
            is_last_item = (i == len(keys) - 1)
            line_connector = "└── " if is_last_item else "├── "
            child_sub_prefix = "     " if is_last_item else "│    "

            value = current_obj[key]
            # Pass the level for this value (which is current_depth + 1) to _get_value_info
            value_info = _get_value_info(value, key_name=key, level_of_value=current_depth + 1, 
                                         max_depth = max_depth, n_to_show = n_to_show, limited_keys = limited_keys)
            
            key_display = str(key).ljust(max_key_len) if max_key_len > 0 else str(key)
            print(f"{parent_prefix}{line_connector}{key_display}: {value_info}")

            # Only recurse if the current_depth + 1 is less than max_depth AND not in limited_keys
            if current_depth + 1 < max_depth and key not in limited_keys:
                if isinstance(value, dict) or isinstance(value, pd.DataFrame):
                    show_anndata_tree(value, max_depth=max_depth, limited_keys=limited_keys,
                                     _current_depth=current_depth + 1, _parent_prefix=parent_prefix + child_sub_prefix,
                                     n_to_show = n_to_show )
            # If it's a DataFrame, even if limited, display its columns if not already in info
            elif isinstance(value, pd.DataFrame):
                if "columns=" not in value_info and hasattr(value, 'columns'):
                    # print(f"{parent_prefix}{child_sub_prefix}└─ Columns: {', '.join(value.columns.tolist())}")
                    pass

    # No need for explicit DataFrame handling here, _get_value_info covers it.
        
def show_anndata_tree(obj, max_depth = 3, n_to_show = 4, limited_keys = None, _current_depth = 0, _parent_prefix = ""):
    """
    Prints a tree-like structure of an AnnData object or its components (dict, DataFrame),
    detailing their main components, with recursive exploration of nested
    dictionaries up to a specified depth. Recursion is limited for keys
    specified in `limited_keys`.

    Args:
        obj: The AnnData object, dictionary, or pandas DataFrame to print.
        max_depth (int): The maximum depth to recurse into nested dictionaries.
        limited_keys (list): A list of keys whose dictionary values should not be recursed into.
        _current_depth (int): Internal parameter for tracking current recursion depth.
        _parent_prefix (str): Internal parameter for tracking indentation in tree structure.
    """

    if limited_keys is None:
        # Default keys to limit recursion for very large nested dicts/dataframes
        limited_keys = [
            'gene_to_band_map', 'Celltype_marker_DB', 'Pathways_DB', 'cnv',
            'DEG_grouping_vars', 'DEG_stat', 'DEG_vs_ref_stat', 'run summary',
            # 'CCI', 'CCI_sample', 'DEG', 'DEG_vs_ref', 'GSA_down', 'GSA_up',
            # 'GSA_vs_ref_down', 'GSA_vs_ref_up', 'GSEA', 'GSEA_vs_ref',
            'log', 'inferploidy_summary', 'cnv_neighbors_info', 'HiCAT_summary', 
            'lut_sample_to_cond', 'analysis_parameters'
        ]

    # --- Main function logic ---

    # If the initial object is an AnnData object
    if _current_depth == 0 and isinstance(obj, anndata.AnnData):
        print(f"AnnData object with n_obs × n_vars = {obj.n_obs} × {obj.n_vars}")

        # List of main AnnData attributes to display
        anndata_components = {
            "X": obj.X,
            "obs": obj.obs,
            "var": obj.var,
            "obsm": obj.obsm,
            "obsp": obj.obsp,
            "varm": obj.varm,
            "varp": obj.varp,
            "uns": obj.uns
        }

        component_keys = list(anndata_components.keys())
        for i, comp_key in enumerate(component_keys):
            is_last_comp = (i == len(component_keys) - 1)
            comp_connector = "└── " if is_last_comp else "├── "
            comp_sub_prefix = "     " if is_last_comp else "│    "

            comp_value = anndata_components[comp_key]
            # Pass level_of_value=1 to _get_value_info for top-level AnnData components
            comp_info = _get_value_info(comp_value, key_name=comp_key, is_top_level_anndata_component=True, 
                                        level_of_value=1, max_depth = max_depth, n_to_show = n_to_show, limited_keys = limited_keys)
            
            print(f"{_parent_prefix}{comp_connector}{comp_key}: {comp_info}")

            # Recurse into complex components (dicts, DataFrames from obsm/obsp) if not at max_depth
            if comp_key in ["uns", "obsm", "obsp", "varm", "varp"]:
                # Only recurse if current_depth + 1 is less than max_depth
                if _current_depth + 1 < max_depth:
                    _display_dict_or_dataframe_recursive(comp_value, _current_depth + 1, _parent_prefix + comp_sub_prefix, 
                                                         max_depth = max_depth, n_to_show = n_to_show, limited_keys = limited_keys)
            # For obs/var (DataFrames), columns are already in comp_info, so no further action needed.

    # Handle dictionary (top-level or recursive)
    elif isinstance(obj, dict):
        if _current_depth == 0: # If called directly with a dict
            print("Dictionary Structure (top-level):")
        _display_dict_or_dataframe_recursive(obj, _current_depth, _parent_prefix, 
                                             max_depth = max_depth, n_to_show = n_to_show, limited_keys = limited_keys)

    # Handle DataFrame (top-level or recursive)
    elif isinstance(obj, pd.DataFrame):
        if _current_depth == 0: # If called directly with a DataFrame
            if len(obj.columns.tolist()) > 3:
                lst = obj.columns.tolist()[:3]
                lst.append('...')
                print(f"DataFrame Structure (top-level): shape={obj.shape}, columns={lst}")
            else:
                print(f"DataFrame Structure (top-level): shape={obj.shape}, columns={obj.columns.tolist()}")
            pass
        # Otherwise, its info is handled by the parent's _get_value_info.

    # Handle other types if called directly (e.g., array, string, int)
    elif _current_depth == 0:
        print(f"Object Type: {type(obj).__name__}")
        print(f"Value Info: {_get_value_info(obj, max_depth = max_depth, n_to_show = n_to_show, limited_keys = limited_keys)}")

    return
    
show_tree = show_anndata_tree