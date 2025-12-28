#! /usr/bin/env python3

# NEED to pass descriptions from the source task, not Terra Task Name

import json
import logging
from typing import Literal, Dict, List, Tuple, Union, Any
from copy import deepcopy
from collections import defaultdict, namedtuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def phb_row_to_string(
    row,
) -> str:
    """
    Convert a dictionary row to a tab-separated string.

    Args:
        row (Dict): The dictionary row to convert.
    Returns:
        The tab-separated string representation of the row.
    """
    # use json.dumps to get double-quote nested strings when within arrays/maps
    return "\t".join(str(v) for v in row.values())


def phb_resolve_classifications(
    var_name: str,
    description: str,
) -> Literal["docker", "database", "reference", "runtime", "general"]:
    """
    Resolve classifications based on variable name and descriptions.

    Args:
        var_name (str): The variable name.
        description (str): The variable description.
    Returns:
        The string classification category.
    """
    return (
        "docker"
        if any(_ in var_name for _ in ["docker", "docker_image"])
        and "internal component" not in description.lower()
        else (
            "database"
            if any(_ in var_name for _ in ["db", "database"])
            and "internal component" not in description.lower()
            else (
                "reference"
                if any(_ in var_name for _ in ["_ref", "ref_", "reference"])
                and "internal component" not in description.lower()
                else (
                    "runtime"
                    if any(
                        _ in var_name
                        for _ in ["cpu", "disk", "disk_size", "_mem", "mem_", "memory"]
                    )
                    and "internal component" not in description.lower()
                    else "general"
                )
            )
        )
    )


def phb_resolve_defaults(
    default: Union[str, Dict[str, Any]],
) -> str:
    """
    Resolve complex default values, including handling of functions like sub, addition, and nested functions like basename.

    Args:
        default (str | dict): The default value to resolve.
            - If str: returned as-is.
            - If dict: expected structure { "func": ..., "args": [...] }.
    Returns:
        The resolved default value as a string.
    """

    # recursively parse nested basename functions
    def parse_basename_func(default):
        if isinstance(default, dict) and default.get("func") == "basename":
            base, exts = parse_basename_func(default["args"][0][0])
            exts += [default["args"][1][0]]
            return base, exts
        else:
            return default, []

    # basename function
    if isinstance(default, dict) and default.get("func") == "basename":
        base, exts = parse_basename_func(default)
        default = f"basename of {base} (without {', '.join(exts)})"

    # substitution function
    elif isinstance(default, dict) and default.get("func") == "sub":
        default = f"{default['args'][0][0]} where '{default['args'][1][0]}' is substituted with '{default['args'][2][0]}'"

    # addition function
    elif isinstance(default, dict) and default.get("func") == "_add":
        default = "".join([_[0] for _ in default["args"]])

    # use json.dumps to double-quote strings
    elif isinstance(default, dict) or isinstance(default, list):
        default = json.dumps(default)

    # Note converting all default values into strings for consistency between dict and input tsv
    else:
        default = str(default) if default != None else ""

    return default


def phb_resolve_var_name(
    var_name: str,
) -> Union[Tuple[str, str], Tuple[None, None]]:
    """
    Resolve an input variable name and its associated workflow from the dict file

    Args:
        var_name (str): The input variable name from the dict file.
    Returns:
        Tuple[str, str]: A tuple containing the workflow name and the variable name (in that order).
    """
    parts = var_name.split(".")
    # variable is defined at the main workflow level
    if len(parts) == 1:
        return None, var_name
    # variable is defined at the task/subworkflow level
    elif len(parts) <= 2:
        return parts[0], parts[1]
    return None, None


def phb_resolve_descriptions(var_name: str) -> str:
    """
    Resolve descriptions based on variable.

    Args:
        var_name (str): The variable name.
    Returns:
        The resolved description.
    """
    common_descriptions = {
        ("cpu",): "Number of CPUs to allocate to the task",
        ("disk", "disk_size"): "Amount of storage (in GB) to allocate to the task",
        ("mem", "memory"): "Amount of memory/RAM (in GB) to allocate to the task",
        ("docker", "docker_image"): "The Docker container to use for the task",
        (
            "timezone",
        ): "Set the time zone to get an accurate date of analysis (uses UTC by default)",
    }
    description = ""
    for keys, desc in common_descriptions.items():
        for k in keys:
            if k in var_name:
                description = desc
                break
    return description


def phb_parse_tsv(tsv_file: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """
    Read input TSV file and return its contents.

    Args:
        tsv_file (str): The path to the TSV file.
    Returns:
        A dictionary mapping workflow display names to lists of dictionaries, where each inner dictionary represents an input variable and its associated metadata.
        A list of the file header
    """
    logger.debug(f"Parsing TSV file: {tsv_file}")
    with open(tsv_file, "r", newline="") as f:
        rows = f.readlines()
        tsv_file_header = rows[0].strip().split("\t")

        tsv_dict = {}
        for row in rows[1:]:
            row = row.strip().split("\t")
            tsv_row = dict(zip(tsv_file_header, row))

            # Only keep columns that exist in this row
            tsv_row = {k: v for k, v in tsv_row.items() if k in tsv_file_header}
            try:
                workflow_list = [x for x in tsv_row["Workflow"].split(", ") if x]
            except KeyError:
                raise KeyError(f"Incorrectly formatted row: {tsv_row}")

            # Populate tsv_dict with all workflows that use this input variable
            for wf in workflow_list:
                if wf not in tsv_dict:
                    tsv_dict[wf] = []
                tsv_dict[wf].append(tsv_row)

    return tsv_dict, tsv_file_header


def phb_generate_rows(combined_dict: dict) -> List[Dict[str, str]]:
    """
    Extract rows from a synthesized dictionary of TSV and BioBlueprint I/O metadata
    """
    all_rows_prep = []
    # prepare independent rows for any contrasting metadata
    for context_vars, wf_dict in combined_dict.items():
        t_rows = defaultdict(list)
        for wf, metadata in wf_dict.items():
            t_row = [
                (
                    k,
                    v,
                )
                for k, v in metadata.items()
            ] + list(context_vars)
            sorted_t_row = tuple(sorted(t_row, key=lambda x: x[0]))
            t_rows[sorted_t_row].append(wf)
        for t_row, wfs in t_rows.items():
            t_row_dict = {k: v for k, v in t_row}
            wfs_str = ", ".join(sorted(wfs))
            t_row_dict["Workflow"] = wfs_str
            all_rows_prep.append(t_row_dict)

    all_rows_sorted = [
        y
        for y in sorted(
            all_rows_prep,
            key=lambda x: (
                x.get("Terra Status", "").lower()
                != "required",  # False values are sorted before True values in python
                x.get("Terra Task Name", "").lower(),
                x.get("Variable", "").lower(),
            ),
        )
    ]

    return all_rows_sorted


def phb_write_tsv(
    metadata_dict: dict,
    tsv_file_header: list,
    output_file: str = "all_inputs_sorted.tsv",
) -> None:
    """
    Write a dictionary to a TSV file.
    Expected structure: { "Workflow Name": [ { "Terra Task Name": ..., "Variable": ..., ...}, ... ], ... }
    Args:
        output_file (str): The path to the output TSV file.
    """

    all_rows_sorted = phb_generate_rows(metadata_dict)

    with open(output_file, "w") as f:
        f.write("\t".join(tsv_file_header) + "\n")

        # unpack into a dictionary
        for row in all_rows_sorted:
            try:
                finalized_row = {k: row[k] for k in tsv_file_header}
            except KeyError:
                raise KeyError(f"{row} missing key")
            print(phb_row_to_string(finalized_row), file=f)


def phb_parse_io_dict(
    io_dict: Dict[str, Dict],
    wf_alias_map: Dict[str, str],
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """
    Parse the I/O dictionary of all inputs/outputs with their associated workflows.

    Args:
        io_dict (str): The I/O dictionary generated from Bioblueprint workflow parsing.
        wf_alias_map (dict): A dictionary mapping workflow file paths to workflow display names.

    Returns:
        A dictionary mapping workflow display names to lists of dictionaries, where each inner dictionary represents an input variable and its associated metadata.
        A dictionary mapping workflow display names to lists of dictionaries, where each inner dictionary represents an output variable and its associated metadata.
    """
    input_dict = {}
    output_dict = {}
    logger.debug(f"Parsing IO Dictionary")
    for wf_wdl_name, info in io_dict.items():
        path = info["path"]
        inputs = info["inputs"]
        outputs = info["outputs"]

        # If the workflow is not hosted on dockstore or no longer used, set the display name to nothing. Will be removed later.
        wf_display_name = wf_alias_map.get(path, "")
        if not wf_display_name:
            continue
        input_dict[wf_display_name] = []
        output_dict[wf_display_name] = []

        # Parse inputs first
        logger.debug(
            f"Parsing inputs: {wf_wdl_name} with path: {path} and display name: {wf_display_name}"
        )
        for var_name, attribute in inputs.items():
            # Terra only considers the first 3 levels of workflow inputs, skip if variable is too deeply nested
            if len(var_name.split(".")) > 2:
                continue

            # variable is defined at the task/subworkflow level
            terra_task_name, var_name = phb_resolve_var_name(var_name)

            # variable is defined at the main workflow level
            if terra_task_name is None:
                terra_task_name = wf_wdl_name

            var_type = attribute["type"].split("?")[0]
            description = phb_resolve_descriptions(var_name)
            default = phb_resolve_defaults(attribute["default"])
            status = (
                "Required"
                if ((attribute["default"] == None) and ("?" not in attribute["type"]))
                else "Optional"
            )
            classification = phb_resolve_classifications(var_name, description)

            input_dict[wf_display_name].append(
                {
                    "Terra Task Name": terra_task_name,
                    "Variable": var_name,
                    "Type": var_type,
                    "Description": description,
                    "Default Value": default,
                    "Terra Status": status,
                    "Classification": classification,
                    "Manual Override": "",
                }
            )

        # Parse outputs
        logger.debug(
            f"Parsing outputs: {wf_wdl_name} with path: {path} and display name: {wf_display_name}"
        )
        for var_name, var_type in outputs.items():
            output_dict[wf_display_name].append(
                {
                    "Variable": var_name,
                    "Type": var_type.split("?")[0],
                }
            )

    return input_dict, output_dict


def phb_prep_tsv_dict(in_dict: dict) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Prepare a dictionary to compare with another for row-row compatibility

    Args:
        input_dict (dict): An parsed I/O dict obtained from an input TSV or I/O dictionary made from BioBlueprint

    Returns:
        output_dict (dict): A dictionary with Terra Task Name and Variable Name extracted for comparisons.
    """
    contextual_variables = {"Terra Task Name", "Variable"}
    output_dict = defaultdict(dict)
    for wf, rows in in_dict.items():
        # unpack a row to obtain the variables we want, and those to maintain
        for row in rows:
            row_key = tuple(
                (
                    k,
                    v,
                )
                for k, v in row.items()
                if k in contextual_variables
            )
            if row.get("Manual Override"):
                output_dict[row_key][wf] = {
                    k: v for k, v in row.items() if k not in contextual_variables
                }
            else:
                output_dict[row_key][wf] = {"Description": row["Description"]}
    return dict(output_dict)


def phb_prep_io_dict(in_dict: dict) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Prepare a dictionary to compare with another for row-row compatibility

    Args:
        input_dict (dict): An parsed I/O dict obtained from an input TSV or I/O dictionary made from BioBlueprint

    Returns:
        output_dict (dict): A dictionary with Terra Task Name and Variable Name extracted for comparisons.
    """
    contextual_variables = {"Terra Task Name", "Variable"}
    output_dict = defaultdict(dict)
    for wf, rows in in_dict.items():
        # unpack a row to obtain the variables we want, and those to maintain
        for row in rows:
            row_key = tuple(
                (
                    k,
                    v,
                )
                for k, v in row.items()
                if k in contextual_variables
            )
            output_dict[row_key][wf] = {
                k: v for k, v in row.items() if k not in contextual_variables
            }
    return output_dict


def phb_update_io(
    i_or_o_dict: dict,
    tsv_dict: dict,
    internal_component_str="Internal component, do not modify",
) -> Tuple[Dict, List, List]:
    """
    Update the input variables in the I/O tsv file based on differences found in the dict input dictionary.

    Args:
        i_or_o_dict (dict): From the input dict. Dictionary mapping workflow display names to a list of dictionaries containing input variables and their metadata.
        tsv_dict (dict): From the IO input tsv file. Dictionary mapping workflow display names to a list of dictionaries containing input variables and their metadata.

    Returns:
        dict: The updated dictionary of valid inputs for all workflows.
    """
    # Flatten both input dictionaries into lists of tuples for easier comparison
    # Ignore wf entries that are most likely subworkflows. We only want to report/document the ones that show up in Terra.
    parsed_io_dict = phb_prep_io_dict(i_or_o_dict)
    tsv_descrip_dict = phb_prep_tsv_dict(tsv_dict)

    logger.debug(
        f"Checking for exact matches between {len(i_or_o_dict)} BioBlueprint rows and {len(tsv_descrip_dict)} TSV rows"
    )
    additions = []
    for dict_row_key, wf_dict in parsed_io_dict.items():
        for dict_wf_name, metadata in wf_dict.items():
            # does this I/O exist in the tsv currently
            if dict_row_key in tsv_descrip_dict:
                # if the workflow isn't there, grab a description for it, otherwise use the existing
                if dict_wf_name not in tsv_descrip_dict[dict_row_key]:
                    # a description may already exist from common variable names
                    if not metadata.get("Description"):
                        descriptions = set(
                            v["Description"]
                            for v in tsv_descrip_dict[dict_row_key].values()
                        )
                        # use the first description
                        if descriptions:
                            # check for multiple descriptions, omit internal components
                            if len(descriptions) > 1:
                                descriptions = sorted(
                                    x
                                    for x in descriptions
                                    if x != internal_component_str
                                )
                            metadata["Description"] = list(descriptions)[0]
                        else:
                            metadata["Description"] = "DESCRIPTION"
                    additions.append([dict_wf_name, dict_row_key, metadata])
                # this entry exists, propagate its current description
                else:
                    metadata["Description"] = tsv_descrip_dict[dict_row_key][
                        dict_wf_name
                    ]["Description"]
            # this entry does not exist
            else:
                # set an description for manual population
                if not metadata.get("Description"):
                    metadata["Description"] = "DESCRIPTION"
                additions.append([dict_wf_name, dict_row_key, metadata])
            if "Default Value" in metadata:
                if (
                    internal_component_str == metadata["Description"]
                    or metadata["Default Value"] == ""
                ):
                    metadata["Classification"] = "general"
            # only preexisting entries can be manually overridden
            if dict_row_key in tsv_descrip_dict:
                if dict_wf_name in tsv_descrip_dict[dict_row_key]:
                    # don't do anything if we want an override
                    if not tsv_descrip_dict[dict_row_key][dict_wf_name].get(
                        "Manual Override"
                    ):
                        tsv_descrip_dict[dict_row_key][dict_wf_name] = metadata
                else:
                    tsv_descrip_dict[dict_row_key][dict_wf_name] = metadata
            else:
                tsv_descrip_dict[dict_row_key] = {}
                tsv_descrip_dict[dict_row_key][dict_wf_name] = metadata

    # remove extraneous entries
    removals = []
    for dict_row_key, wf_dict in tsv_descrip_dict.items():
        if dict_row_key not in parsed_io_dict:
            for dict_wf_name, metadata in wf_dict.items():
                removals.append([dict_wf_name, dict_row_key, metadata])
        else:
            for dict_wf_name, metadata in wf_dict.items():
                if dict_wf_name not in parsed_io_dict[dict_row_key]:
                    removals.append([dict_wf_name, dict_row_key, metadata])
    for dict_wf_name, dict_row_key, metadata in removals:
        del tsv_descrip_dict[dict_row_key][dict_wf_name]

    return tsv_descrip_dict, additions, removals


def phb_generate_report(
    additions: list,
    removals: list,
    output_file: str = "io_changelog.tsv",
) -> None:
    """
    Generate a report of changes made to all I/O variables.
    """
    logger.debug(f"Generating report of changes to I/O variables: {output_file}")
    with open(output_file, "w", newline="") as f:

        print("ADDITIONS:", file=f)
        for wf_name, row, description in additions:
            row_dict = {k: v for k, v in row}
            row_dict["Description"] = description
            print(f"{wf_name}: {row_dict}", file=f)

        print(
            "\n---------------------------------------------------------------------------------\n",
            file=f,
        )
        print("REMOVALS:", file=f)
        for wf_name, row, description in removals:
            row_dict = {k: v for k, v in row}
            row_dict["Description"] = description
            print(f"{wf_name}: {row_dict}", file=f)


def main(
    io_dict: str,
    input_tsv_file: str,
    output_tsv_file: str,
    wf_alias_map: Dict,
    out_dir: str,
    out_prefix: str,
) -> None:
    input_dict, output_dict = phb_parse_io_dict(io_dict, wf_alias_map)

    # Parse and update input variables first
    logger.info(f"Updating {input_tsv_file}")
    tsv_input_dict, input_file_header = phb_parse_tsv(input_tsv_file)
    updated_input_dict, input_adds, input_rms = phb_update_io(
        input_dict, tsv_input_dict
    )
    logger.info(f"{len(input_adds)} additions; {len(input_rms)} removals")

    # Create the updated input tsv file and generate a report of changes made to input variables
    phb_generate_report(
        input_adds, input_rms, output_file=f"{out_dir}{out_prefix}_inputs_changelog.tsv"
    )
    phb_write_tsv(
        updated_input_dict,
        input_file_header,
        output_file=f"{out_dir}{out_prefix}_inputs.tsv",
    )

    # Parse and update output variables next
    logger.info(f"Updating {output_tsv_file}")
    tsv_output_dict, output_file_header = phb_parse_tsv(output_tsv_file)
    updated_output_dict, output_adds, output_rms = phb_update_io(
        output_dict, tsv_output_dict
    )
    logger.info(f"{len(output_adds)} additions; {len(output_rms)} removals")

    # Create the updated output tsv file and generate a report of changes made to output variables
    phb_generate_report(
        output_adds,
        output_rms,
        output_file=f"{out_dir}{out_prefix}_outputs_changelog.tsv",
    )
    phb_write_tsv(
        updated_output_dict,
        output_file_header,
        output_file=f"{out_dir}{out_prefix}_outputs.tsv",
    )
