#! /usr/bin/env python3

import os
import re
import WDL
import logging
import networkx as nx

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


def parse_expr_apply(expr, parsed_expr):
    """Parse a WDL function applied to an expression"""
    # extract the function and prepare a dictionary for argument population
    apply_dict = {"func": expr.function_name, "args": []}
    for arg in expr.arguments:
        apply_dict["args"].append(parse_expr(arg, []))
    parsed_expr.append(apply_dict)
    return parsed_expr


def parse_expr_array(expr, parsed_expr):
    parsed_expr.append(expr.literal.json)
    return parsed_expr


def parse_expr_get(expr, parsed_expr):
    parsed_expr = parse_expr(expr.expr, parsed_expr)
    return parsed_expr


def parse_expr_ident(expr, parsed_expr):
    parsed_expr.append(str(expr.name))
    return parsed_expr


def parse_expr_string(expr, parsed_expr):
    """Extract a Python str from a WDL String while removing extraneous quotes"""
    deconstruction = "".join(
        [x for x in expr.parts if x.replace("'", "").replace('"', "")]
    )
    parsed_expr.append(deconstruction)
    return parsed_expr


def parse_expr_value(expr, parsed_expr):
    parsed_expr.append(expr.value)
    return parsed_expr


def parse_expr_map(expr, parsed_expr):
    for k, v in expr.items:
        parsed_expr.append([parse_expr(k, []), parse_expr(v, [])])
    return parsed_expr


def parse_expr(expr, parsed_expr):
    """Recrusively parse expression types"""
    if isinstance(expr, WDL.Expr.Apply):
        parsed_expr = parse_expr_apply(expr, parsed_expr)
    elif isinstance(expr, WDL.Expr.Get):
        parsed_expr = parse_expr_get(expr, parsed_expr)
    elif isinstance(expr, WDL.Expr.Ident):
        parsed_expr = parse_expr_ident(expr, parsed_expr)
    elif isinstance(expr, WDL.Expr.String):
        parsed_expr = parse_expr_string(expr, parsed_expr)
    elif isinstance(expr, WDL.Expr.Array):
        parsed_expr = parse_expr_array(expr, parsed_expr)
    elif isinstance(expr, (WDL.Expr.Int, WDL.Expr.Boolean, WDL.Expr.Float)):
        parsed_expr = parse_expr_value(expr, parsed_expr)
    elif isinstance(expr, (WDL.Expr.Map)):
        parsed_expr = parse_expr_map(expr, parsed_expr)
    else:
        # expression parsing function needs to be added
        raise AttributeError(f"unaccounted expression type: {type(expr)}; {str(expr)}")
    return parsed_expr


def parse_call(G, node, io_dict={}, source_callee=None, source_node=None):
    name2tag = {}

    # acquire the inputs delivered to the call
    callee = node.callee
    callee_tag = (
        callee.digest,
        callee.name,
    )
    # acquire the source information from the call
    if isinstance(callee, (WDL.Tree.Task, WDL.Tree.Workflow)):
        G.add_edge(source_callee, callee_tag)
        if source_node:
            derived_source = source_node + "." + node.name
        else:
            derived_source = node.name
        name2tag[derived_source] = callee_tag
        io_dict[derived_source] = {
            "callee": callee_tag,
            "inputs": populate_inputs(callee.inputs),
            "outputs": {x.name: str(x.type) for x in callee.outputs},
        }
    else:
        raise AttributeError(f"unexpected call type {type(callee)}")
    return G, io_dict, name2tag


def parse_scatter_condn(
    G, node, wf_tag, io_dict={}, source_callee=None, source_node=None
):
    """Parse a scatter or conditional expression and append to graph and io_dict as tasks/wfs appear"""
    in2expr = {}
    name2tag = {}
    for node in node.body:
        if isinstance(node, WDL.Tree.Call):
            if source_node:
                derived_source = source_node + "." + node.name
            else:
                derived_source = node.name
            call_inputs = link_inputs(node.inputs)
            for k, v in call_inputs.items():
                if v not in in2expr:
                    in2expr[v] = []
                in2expr[v].append(
                    (
                        derived_source,
                        k,
                    )
                )
            G, io_dict, t_name2tag = parse_call(
                G, node, io_dict, source_callee=source_callee, source_node=source_node
            )
            name2tag = {**name2tag, **t_name2tag}
        elif isinstance(node, (WDL.Tree.Conditional, WDL.Tree.Scatter)):
            G, io_dict, t_in2expr, t_name2tag = parse_scatter_condn(
                G,
                node,
                wf_tag,
                io_dict,
                source_callee=source_callee,
                source_node=source_node,
            )
            in2expr = combine_in2expr(t_in2expr, in2expr)
            name2tag = {**name2tag, **t_name2tag}
        # ignore variable definitions, raise an error otherwise
        elif not isinstance(node, WDL.Tree.Decl):
            raise AttributeError(
                f"unexpected node type {type(node)} in scatter/conditional body"
            )
    return G, io_dict, in2expr, name2tag


def link_inputs(inputs):
    """Link the inputs dictionary with the name and default values"""
    inputs_dict = {}
    for i, v in inputs.items():
        if isinstance(v, WDL.Expr.Get):
            data = [x for x in parse_expr(v.expr, [])]
            # ignore Arrays/Maps
            if len(data) == 1:
                inputs_dict[i] = data[0]

    return inputs_dict


def combine_in2expr(t_in2expr, in2expr):
    """Populate a dictionary relating workflows to inputs and expressions"""
    for k, v in t_in2expr.items():
        if k not in in2expr:
            in2expr[k] = []
        in2expr[k] += v
    return in2expr


def parse_wf(G, wf, wf_tag):
    """Obtain the 1st order data structures (I/O, call namespaces, and call input expressions) from a workflow"""
    io_dict = {}
    name2tag = {}
    in2expr = {}
    # parse the body of a workflow and compile its calls
    for node in wf.body:
        if isinstance(node, WDL.Tree.Call):
            derived_source = node.name
            call_inputs = link_inputs(node.inputs)
            for k, v in call_inputs.items():
                if v not in in2expr:
                    in2expr[v] = []
                in2expr[v].append(
                    (
                        derived_source,
                        k,
                    )
                )
            G, io_dict, t_name2tag = parse_call(G, node, io_dict, source_callee=wf_tag)
            name2tag = {**name2tag, **t_name2tag}
        elif isinstance(node, (WDL.Tree.Conditional, WDL.Tree.Scatter)):
            G, io_dict, t_in2expr, t_name2tag = parse_scatter_condn(
                G, node, wf_tag, io_dict, source_callee=wf_tag
            )
            in2expr = combine_in2expr(t_in2expr, in2expr)
            name2tag = {**name2tag, **t_name2tag}
        elif isinstance(node, WDL.Tree.Decl):
            continue  # these are just variable definitions, no action needed
        else:
            raise AttributeError(f"unexpected node type {type(node)} in workflow body")

    return G, io_dict, in2expr, name2tag


def populate_inputs(inputs):
    """Populate the inputs dictionary with the name, type, and default values"""
    inputs_dict = {}
    for i in inputs:
        inputs_dict[i.name] = {"type": str(i.type), "default": None}
        # if there is an expression indicating a default is set
        if i.expr:
            data = [x for x in parse_expr(i.expr, [])]
            # only maintain the list type for Arrays/Maps
            if len(data) == 1:
                inputs_dict[i.name]["default"] = data[0]
            else:
                inputs_dict[i.name]["default"] = data

    return inputs_dict


def compile_workflow_data_structures(workflow_file, G):
    """Import a WDL workflow, return its dependency graph, and I/O"""
    dep_io_dict = {}
    try:
        wdl = WDL.load(workflow_file)
    except Exception as e:
        raise RuntimeError(f"WDL parsing errors raised from {workflow_file}: {e}")

    # if this is a workflow, parse the workflow
    if wdl.tasks:
        raise AttributeError(
            f"Anticipated workflow WDL file {workflow_file} contains tasks"
        )
    elif wdl.workflow:
        wf_tag = (
            wdl.workflow.digest,
            wdl.workflow.name,
        )
        logger.debug(f"Parsing {wdl.workflow.name}")
        G, dep_io_dict, wf_in2expr, name2tag = parse_wf(G, wdl.workflow, wf_tag)
        wf_io_dict = {"inputs": {}, "outputs": {}}
        if wdl.workflow.inputs:
            wf_io_dict["inputs"] = populate_inputs(wdl.workflow.inputs)
        if wdl.workflow.outputs:
            wf_io_dict["outputs"] = WDL.values_to_json(wdl.workflow.effective_outputs)
        available_inputs = set(WDL.values_to_json(wdl.workflow.available_inputs))
        for dep, io_dict in dep_io_dict.items():
            for k, v in io_dict["inputs"].items():
                dep_input = f"{dep}.{k}"
                if dep_input in available_inputs:
                    wf_io_dict["inputs"][dep_input] = v
        if wf_tag not in G.nodes:
            G.add_node(wf_tag)
    else:
        raise AttributeError(
            f"Anticipated workflow WDL file {workflow_file} does not contain a workflow"
        )

    return G, wf_tag, wf_in2expr, dep_io_dict, name2tag, wf_io_dict


def extract_wdl_nodes(wdl_file):
    """Parse a WDL file and obtain the tasks/workflows contained"""
    node_names = []
    logger.debug(f"Parsing WDL file {wdl_file}")
    wdl = WDL.load(wdl_file)
    if wdl.workflow:
        wdl_tag = (
            wdl.workflow.digest,
            wdl.workflow.name,
        )
        node_names.append(wdl_tag)
    elif wdl.tasks:
        for task in wdl.tasks:
            node_names.append(
                (
                    task.digest,
                    task.name,
                )
            )
    else:
        raise AttributeError(
            f"Anticipated WDL file {wdl_file} does not contain a workflow or task"
        )
    return node_names


def float_default_from_dep_io_dict(i, linked_expressions, dep_io_dict):
    """Float defaults up to the top for optional inputs w/o a default and a single determined linked value"""
    defaults = set()
    for node_call, node_input in linked_expressions:
        if node_call not in dep_io_dict:
            raise KeyError(f"Node {node_call} not found in dependency I/O dictionary")
        elif node_input not in dep_io_dict[node_call]["inputs"]:
            raise KeyError(f"Input {node_input} not found in node {node_call} inputs")
        t_default = dep_io_dict[node_call]["inputs"][node_input]["default"]
        defaults.add(t_default)
    # if there is a single default value to link, float it
    if len(defaults) == 1:
        default = list(defaults)[0]
    else:
        default = None
        logger.debug(f"input: {i} is not used in imported modules")

    return default


def float_first_order_defaults(inputs_dict, dep_io_dict, in2expr):
    """Extract default input data from dependencies and apply to source input dictionary"""
    for i, input_metadata in inputs_dict.items():
        # this is the source WDL
        if i.count(".") == 0:
            if "?" in input_metadata["type"]:
                # if there isn't a default
                if input_metadata["default"] is None:
                    # if there is a downstream link
                    if i in in2expr:
                        input_metadata["default"] = float_default_from_dep_io_dict(
                            i, in2expr[i], dep_io_dict
                        )

    return inputs_dict


def float_nested_wf_defaults(wf2io, wf2in2expr, wf2name2tag):
    """Extract default input data from dependencies and apply to source input dictionary"""

    # initialize an iterative default float loop
    default_floated = True
    # continue as long as a default has been floated in the previous iteration
    while default_floated:
        default_floated = False
        for src_wf, io_dict in wf2io.items():
            for i, input_metadata in io_dict["inputs"].items():
                # if this is an optional input
                if "?" in input_metadata["type"]:
                    # if it doesn't have a default
                    if input_metadata["default"] is None:
                        # if this is a nested input
                        if i.count(".") == 0:
                            # if there is an expression to float from
                            if i in wf2in2expr[src_wf]:
                                input_expressions = wf2in2expr[src_wf][i]
                                defaults = set()
                                for node_call, node_input in input_expressions:
                                    node_tag = wf2name2tag[src_wf][node_call]
                                    if node_tag in wf2io:
                                        defaults.add(
                                            wf2io[node_tag]["inputs"][node_input][
                                                "default"
                                            ]
                                        )
                                if len(defaults) == 1:
                                    default = list(defaults)[0]
                                    if default is not None:
                                        input_metadata["default"] = list(defaults)[0]
                                        default_floated = True

    # set nested defaults from their wf source now that they are comprehensively populated
    for src_wf, io_dict in wf2io.items():
        for i, input_metadata in io_dict["inputs"].items():
            if "?" in input_metadata["type"]:
                if input_metadata["default"] is None:
                    if i.count(".") == 1:
                        node_data = re.search(r"(.*)\.([^\.]+$)", i)
                        node_call = node_data.group(1)
                        node_input = node_data.group(2)
                        node_tag = wf2name2tag[src_wf][node_call]
                        # if it is a workflow, grab its default
                        if node_tag in wf2io:
                            input_metadata["default"] = wf2io[node_tag]["inputs"][
                                node_input
                            ]["default"]
    return wf2io


def compile_io(wf2io, wf2dependency_io, wf2namespace2tag, wf2inputs2expressions):

    # default floating could probably be done more efficiently with graph traversal
    for wf_tag, io in wf2io.items():
        io["inputs"] = float_first_order_defaults(
            io["inputs"], wf2dependency_io[wf_tag], wf2inputs2expressions[wf_tag]
        )

    wf2io = float_nested_wf_defaults(wf2io, wf2inputs2expressions, wf2namespace2tag)

    for io_dict in wf2io.values():
        io_dict["inputs"] = {
            k: v
            for k, v in sorted(io_dict["inputs"].items(), key=lambda x: x[0].count("."))
        }

    return wf2io


def compile_repo(repo, wf_prefix="wf_", wf_suffix=".wdl"):
    """Acquire all workflows and compile the repository's dependency graph"""
    # get the base repository path
    repo_dir_path = os.path.abspath(repo.working_tree_dir)

    # acquire all workflows in the repository
    workflows = {}
    for file in repo.git.ls_files().splitlines():
        wf_full_path = os.path.join(repo_dir_path, file)
        if os.path.basename(file).startswith(wf_prefix) and os.path.basename(
            file
        ).endswith(wf_suffix):
            workflows[wf_full_path] = file

    # initialize the graph
    G = nx.DiGraph()
    # init the io dict
    wf2io, wf2dependency_io, wf2namespace2tag, wf2inputs2expressions = {}, {}, {}, {}
    for raw_wf_path, repo_path in workflows.items():
        G, wf_tag, wf_in2expr, dep_io_dict, name2tag, wf_io_dict = (
            compile_workflow_data_structures(raw_wf_path, G)
        )
        wf2io[wf_tag] = wf_io_dict
        wf2io[wf_tag]["path"] = repo_path
        wf2dependency_io[wf_tag] = dep_io_dict
        wf2namespace2tag[wf_tag] = name2tag
        wf2inputs2expressions[wf_tag] = wf_in2expr

    io = compile_io(wf2io, wf2dependency_io, wf2namespace2tag, wf2inputs2expressions)

    return G, {k: v for k, v in sorted(io.items(), key=lambda x: x[0])}
