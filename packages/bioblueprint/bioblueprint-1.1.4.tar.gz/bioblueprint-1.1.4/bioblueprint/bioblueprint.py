#! /usr/bin/env python3

# NEED to make it so graph nodes are specific to a file + task/workflow, not a task/workflow name
# will require modifying wdl.py during graph construction to identify the path of the nodes
# then reexpose the attribute errors that account for duplicate names/remove altogether
# NEED to parse diffs to identify the task that was changed, not using the whole file

# BEYOND MVP
# NEED to incorporate conditional parsing to link I/O modifications to more refined testing paths

import re
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from bioblueprint.lib.wdl import compile_repo, extract_wdl_nodes
from bioblueprint.lib.graph import obtain_graph_paths
from git import Repo
from bioblueprint.lib.repos import (
    download_pr,
    define_phb_standards,
    phb_get_wf_display_name,
)
from bioblueprint.tools.update_io import main as phb_update_io

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def prep_output_dir(out_dir=None):
    """Prepare an output directory"""
    if out_dir:
        clean_dir = str(Path(out_dir).resolve())
    else:
        cur_time = datetime.now().strftime("%Y%m%d")
        clean_dir = f"{os.getcwd()}/bioblueprint_{cur_time}/"
    if not os.path.isdir(clean_dir):
        os.mkdir(clean_dir)
    return clean_dir


def prep_output_prefix(input_path, suffix):
    """Prepare the output base path"""
    out_base = input_path
    if input_path.endswith("/"):
        out_base = out_base[:-1]
    out_base = os.path.basename(re.sub(suffix + r"$", "", out_base))
    return out_base


def initialize_bioblueprint():
    parser = argparse.ArgumentParser(
        description="BioBlueprint workflow dependency compiler and automation"
    )

    in_par = parser.add_argument_group("Input parameters")
    in_par.add_argument(
        "-i", "--input", help="Local Git repository directory", required=True
    )
    in_par.add_argument(
        "-px", "--prefix", help='Workflow prefix; DEFAULT: "wf_"', default="wf_"
    )
    in_par.add_argument(
        "-sx", "--suffix", help='Language suffix; DEFAULT: ".wdl"', default=".wdl"
    )

    git_par = parser.add_argument_group("Git parameters")
    git_par.add_argument(
        "-d", "--derived_branch", help="Derived branch name; DEFAULT: active branch"
    )
    git_par.add_argument(
        "-s",
        "--source_branch",
        help='Source branch name; DEFAULT: "main"',
        default="main",
    )

    repo_par = parser.add_argument_group("Repository parameters")
    repo_par.add_argument(
        "-o",
        "--owner",
        help="GitHub repository owner; DEFAULT: theiagen",
        default="theiagen",
    )
    repo_par.add_argument(
        "-r",
        "--repository",
        help="GitHub repository name; DEFAULT: basename of -i/--input",
    )
    repo_par.add_argument(
        "-pr",
        "--pull_request",
        type=int,
        help="Modify existing pull request number; DEFAULT: create new PR",
    )

    run_par = parser.add_argument_group("Runtime parameters")
    run_par.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug output"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    args.input = str(Path(args.input).resolve())
    if not args.input.endswith("/"):
        args.input += "/"
    out_dir = prep_output_dir()
    out_base = prep_output_prefix(args.input, args.suffix)
    if not args.repository:
        args.repository = os.path.basename(args.input[:-1])

    logger.warning(
        "BioBlueprint may change your branch. Ensure you are pulled and committed appropriately"
    )

    return args, out_dir, out_base


def compile_branch(repo, branch_name=""):
    if branch_name:
        logger.info(f"Checking out branch: {branch_name}")
        repo.git.checkout(branch_name)
    else:
        branch_name = repo.active_branch.name
        logger.info(f"On branch: {branch_name}")
    commit = repo.head.commit.tree
    return commit, branch_name


def check_merge_status(repo, derived_name, source_name):
    """Check if source branch is merged into derived branch"""
    commits_ahead = repo.iter_commits(f"{derived_name}..{source_name}")
    ahead_count = sum(1 for _ in commits_ahead)
    if ahead_count > 0:
        return False
    return True


def identify_changed_files(src_commit, der_commit, suffix):
    """Identify changed files between two commits"""
    # get the diff
    diff = src_commit.diff(der_commit)
    added_files = [
        x.b_path for x in diff.iter_change_type("A") if x.b_path.endswith(suffix)
    ]
    modified_files = [
        x.b_path for x in diff.iter_change_type("M") if x.b_path.endswith(suffix)
    ]
    removed_files = [
        x.b_path for x in diff.iter_change_type("D") if x.b_path.endswith(suffix)
    ]

    logger.info(f"Added files: {added_files}")
    logger.info(f"Modified files: {modified_files}")
    logger.info(f"Removed files: {removed_files}")
    return added_files, modified_files, removed_files


def parse_branches(repo, derived_branch, source_branch, suffix):
    src_commit, source_branch = compile_branch(repo, branch_name=source_branch)
    der_commit, derived_branch = compile_branch(repo, branch_name=derived_branch)

    if source_branch == derived_branch:
        logger.warning(
            f"Source branch {source_branch} is the same as derived branch {derived_branch}"
        )

    added_files, modified_files, removed_files = identify_changed_files(
        src_commit, der_commit, suffix
    )
    if not (added_files or modified_files or removed_files):
        logger.warning(
            "No added, modified, or removed WDL files detected between source and derived branches"
        )

    return derived_branch, source_branch, added_files, modified_files, removed_files


def compile_affected_nodes(input_dir, files, prefix):
    """Compile nodes that are affected by modifications in specific workflow files"""
    nodes_dict = {"wf": [], "task": []}
    for file_ in files:
        node_names = extract_wdl_nodes(input_dir + file_)
        logger.debug(f"Parsed WDL file {file_}: {node_names}")
        if os.path.basename(file_).startswith(prefix):
            nodes_dict["wf"].extend(node_names)
        else:
            nodes_dict["task"].extend(node_names)
    return nodes_dict


def parse_io_modifications(
    der_io_dict, src_io_dict, input_exposure_depth=1, output_exposure_depth=0
):
    """Identify differences in I/O and report by its parent"""
    diff_dict = {}
    for wf in der_io_dict:
        if wf in src_io_dict:
            mod_inputs = sorted(
                set(der_io_dict[wf]["inputs"]) - set(src_io_dict[wf]["inputs"])
            )
            mod_outputs = sorted(
                set(der_io_dict[wf]["outputs"]) - set(src_io_dict[wf]["outputs"])
            )
            rm_inputs = sorted(
                set(src_io_dict[wf]["inputs"]) - set(der_io_dict[wf]["inputs"])
            )
            rm_outputs = sorted(
                set(src_io_dict[wf]["outputs"]) - set(der_io_dict[wf]["outputs"])
            )
            # only output exposed inputs / outputs
            terra_mod_inputs = [
                x for x in mod_inputs if x.count(".") <= input_exposure_depth
            ]
            terra_mod_outputs = [
                x for x in mod_outputs if x.count(".") <= output_exposure_depth
            ]
            terra_rm_inputs = [
                x for x in rm_inputs if x.count(".") <= input_exposure_depth
            ]
            terra_rm_outputs = [
                x for x in rm_outputs if x.count(".") <= output_exposure_depth
            ]
            if mod_inputs or mod_outputs or rm_inputs or rm_outputs:
                diff_dict[wf] = {
                    "added_inputs": terra_mod_inputs,
                    "added_outputs": terra_mod_outputs,
                    "removed_inputs": terra_rm_inputs,
                    "removed_outputs": terra_rm_outputs,
                }
        else:
            diff_dict[wf] = {
                "added_inputs": sorted(
                    [
                        x
                        for x in der_io_dict[wf]["inputs"]
                        if x.count(".") <= input_exposure_depth
                    ]
                ),
                "added_outputs": sorted(
                    [
                        x
                        for x in der_io_dict[wf]["outputs"]
                        if x.count(".") <= output_exposure_depth
                    ]
                ),
                "removed_inputs": [],
                "removed_outputs": [],
            }
    return diff_dict


def parse_wf_task_modifications(new_nodes, perturbed_nodes, removed_nodes):
    """Identify differences in workflows and tasks"""
    wf_diff_dict = {"\\+": [], "Δ": [], "\\-": []}
    task_diff_dict = {"\\+": [], "Δ": [], "\\-": []}
    for node in new_nodes["wf"]:
        wf_diff_dict["\\+"].append(node[1])
    for node in new_nodes["task"]:
        task_diff_dict["\\+"].append(node[1])
    for node in perturbed_nodes["wf"]:
        wf_diff_dict["Δ"].append(node[1])
    for node in perturbed_nodes["task"]:
        task_diff_dict["Δ"].append(node[1])
    for node in removed_nodes["wf"]:
        wf_diff_dict["\\-"].append(node[1])
    for node in removed_nodes["task"]:
        task_diff_dict["\\-"].append(node[1])
    return {k: sorted(v) for k, v in wf_diff_dict.items()}, {
        k: sorted(v) for k, v in task_diff_dict.items()
    }


def translate_tags_and_names(io_dict_der, io_dict_src, wf_path2name={}):
    """Translate tag hashes between derived and source references based on shared PATHs"""
    path2tag_der = {v["path"]: k for k, v in io_dict_der.items()}
    path2tag_src = {v["path"]: k for k, v in io_dict_src.items()}
    tag2name_der = {
        v: wf_path2name[k] for k, v in path2tag_der.items() if k in wf_path2name
    }
    tag2name_src = {
        v: wf_path2name[k] for k, v in path2tag_src.items() if k in wf_path2name
    }
    src2der = {v: path2tag_der[k] for k, v in path2tag_src.items() if k in path2tag_der}
    return src2der, tag2name_der, tag2name_src


def main():
    args, out_dir, out_base = initialize_bioblueprint()

    # initialize the repository and git metadata
    if not os.path.isdir(args.input + "/.git"):
        raise SystemExit(
            f"Input directory {args.input} is not the head of a git repository"
        )
    repo = Repo(args.input)

    starting_branch = repo.active_branch.name
    logger.info(f"Initial branch: {starting_branch}")
    logger.info(f"Checking out branch: {args.derived_branch}")
    repo.git.checkout(args.derived_branch)

    logger.info(f"Checking branch congruence (merge status)")
    merged = check_merge_status(repo, args.derived_branch, args.source_branch)
    if not merged:
        logger.error(
            f"Source branch {args.source_branch} is not merged into derived branch {args.derived_branch}."
        )
        raise SystemExit(
            f"Please merge {args.source_branch} into {args.derived_branch} before proceeding."
        )

    derived_branch, source_branch, added_files, modified_files, removed_files = (
        parse_branches(repo, args.derived_branch, args.source_branch, args.suffix)
    )

    # initialize repo-specific functions and metadata
    io_path = f"{out_dir}{out_base}.io.json"
    pr_out_path = f"{out_dir}{out_base}.pr.md"
    if args.repository == "public_health_bioinformatics":
        # define the standardized paths for PHB and required functions
        pr_template_path, pr_pop_func, i_tsv_path, o_tsv_path, dockstore_path = (
            define_phb_standards(args.input)
        )
        io_update_func = phb_update_io
        # identify served workflows that ought to be tested
        wf_path2name = phb_get_wf_display_name(dockstore_path)
        exempted_tasks = {"version_capture"}
    else:  # set generic standards
        # do not define functions to parse and output these data
        pr_pop_func, io_update_func = None, None
        pr_template_path = pr_out_path
        wf_path2name = {}
        with open(pr_template_path, "w") as out:
            out.write("")

    logger.info(f"Compiling derived branch graph: {args.derived_branch}")
    G_der, io_dict_der = compile_repo(repo, args.prefix, args.suffix)

    # compile additional and modififed repository nodes
    new_nodes = compile_affected_nodes(args.input, added_files, args.prefix)
    perturbed_nodes = compile_affected_nodes(args.input, modified_files, args.prefix)

    # compile and parse the source graph to obtain paths for removed nodes
    if source_branch == derived_branch:
        G_src, io_dict_src = G_der, io_dict_der
    else:
        logger.info(f"Checking out branch: {source_branch}")
        repo.git.checkout(source_branch)
        G_src, io_dict_src = compile_repo(repo, args.prefix, args.suffix)
    # create a translation mapping between tags
    src_tag2der_tag, tag2name_der, tag2name_src = translate_tags_and_names(
        io_dict_der, io_dict_src, wf_path2name
    )

    removed_nodes = compile_affected_nodes(args.input, removed_files, args.prefix)

    logger.info(f"Checking out branch: {args.derived_branch}")
    repo.git.checkout(args.derived_branch)
    # compile the paths affected by modified nodes
    perturbed_roots = obtain_graph_paths(
        G_der,
        new_nodes["wf"]
        + new_nodes["task"]
        + perturbed_nodes["wf"]
        + perturbed_nodes["task"],
        tag2name_der.keys(),
    )
    if removed_nodes["wf"] or removed_nodes["task"]:
        # need to translate between the source graph PATH to the derived graph PATH to obtain its tag
        perturbed_roots = {
            **perturbed_roots,
            **obtain_graph_paths(
                G_src, removed_nodes["wf"] + removed_nodes["task"], tag2name_src.keys()
            ),
        }

    removed_wf_set = set(removed_nodes["wf"])
    # create the testing dictionary by adding paths to workflows
    testing_dict = {}
    for k, v in sorted(perturbed_roots.items(), key=lambda x: x[0]):
        v = [x for x in v if x[1] not in exempted_tasks]
        if v:
            if k in io_dict_der:
                testing_dict[k[1]] = {"path": io_dict_der[k]["path"], "modified": v}
            # if it isn't here then there is an error potentially
            elif k in src_tag2der_tag:
                der_tag = src_tag2der_tag[k]
                testing_dict[der_tag[1]] = {
                    "path": io_dict_der[der_tag]["path"],
                    "modified": v,
                }
            elif k not in removed_wf_set:
                raise KeyError(f"Unknown error from modified node {k}")

    # only need the source branch if we are generating a PR or a test template
    clean_io_dict_der = {k[1]: v for k, v in io_dict_der.items()}
    clean_io_dict_src = {k[1]: v for k, v in io_dict_src.items()}
    io_diff_dict = parse_io_modifications(clean_io_dict_der, clean_io_dict_src)
    wf_diff_dict, task_diff_dict = parse_wf_task_modifications(
        new_nodes, perturbed_nodes, removed_nodes
    )

    if args.pull_request is not None:
        logger.info(
            f"Downloading PR #{args.pull_request} from {args.owner}/{args.repository}"
        )
        pr_str = download_pr(args.owner, args.repository, args.pull_request)
    else:
        logger.info(f"Populating new PR template from {pr_template_path}")
        with open(pr_template_path, "r") as pr_template:
            pr_str = pr_template.read()
    pr_str, testing_dict = pr_pop_func(
        wf_diff_dict, task_diff_dict, io_diff_dict, testing_dict, pr_str
    )

    # output files
    with open(io_path, "w") as out:
        out.write(json.dumps(clean_io_dict_der, indent=2))
    with open(f"{out_dir}{out_base}.testing.json", "w") as out:
        out.write(json.dumps(testing_dict, indent=2))
    with open(pr_out_path, "w") as out:
        out.write(pr_str)

    # update I/O if applicable
    if io_update_func:
        io_args = (
            clean_io_dict_der,
            i_tsv_path,
            o_tsv_path,
            wf_path2name,
            out_dir,
            out_base,
        )
        io_update_func(*io_args)

    repo.git.checkout(starting_branch)
    logger.info(f"Checking out branch: {starting_branch}")


if __name__ == "__main__":
    main()
    sys.exit(0)
