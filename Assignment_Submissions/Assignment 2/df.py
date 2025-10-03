import sys
import json
from collections import namedtuple

from form_blocks import form_blocks
import cfg

# A single dataflow analysis consists of these part:
# - forward: True for forward, False for backward.
# - init: An initial value (bottom or top of the latice).
# - merge: Take a list of values and produce a single value.
# - transfer: The transfer function.
Analysis = namedtuple("Analysis", ["forward", "init", "merge", "transfer"])


def union(sets):
    out = set()
    for s in sets:
        out.update(s)
    return out


def df_worklist(blocks, analysis):
    """The worklist algorithm for iterating a data flow analysis to a
    fixed point.
    """
    preds, succs = cfg.edges(blocks)

    # Switch between directions.
    if analysis.forward:
        first_block = list(blocks.keys())[0]  # Entry.
        in_edges = preds
        out_edges = succs
    else:
        first_block = list(blocks.keys())[-1]  # Exit.
        in_edges = succs
        out_edges = preds

    # Initialize.
    in_ = {first_block: analysis.init}
    out = {node: analysis.init for node in blocks}

    # Iterate.
    worklist = list(blocks.keys())
    while worklist:
        node = worklist.pop(0)

        inval = analysis.merge(out[n] for n in in_edges[node])
        in_[node] = inval

        outval = analysis.transfer(blocks[node], inval)

        if outval != out[node]:
            out[node] = outval
            worklist += out_edges[node]

    if analysis.forward:
        return in_, out
    else:
        return out, in_


def fmt(val):
    """Guess a good way to format a data flow value. (Works for sets and
    dicts, at least.)
    """
    if isinstance(val, set):
        if val:
            # Check if the set contains tuples
            if val and isinstance(next(iter(val)), tuple):
                sample_tuple = next(iter(val))
                # Check if it's a reaching definition (var, id) pair
                if len(sample_tuple) == 2 and isinstance(sample_tuple[1], int):
                    return ", ".join("{}@{}".format(var, str(def_id)[-4:]) for var, def_id in sorted(val))
                # Check if it's an expression (op, arg1, arg2, ...)
                else:
                    return ", ".join("({})".format(" ".join(str(x) for x in expr)) for expr in sorted(val))
            else:
                return ", ".join(v for v in sorted(val))
        else:
            return "∅"
    elif isinstance(val, dict):
        if val:
            return ", ".join("{}: {}".format(k, v) for k, v in sorted(val.items()))
        else:
            return "∅"
    else:
        return str(val)


def run_df(bril, analysis):
    global _block_names
    for func in bril["functions"]:
        # Reset block names for each function
        _block_names = {}
        
        # Form the CFG.
        blocks = cfg.block_map(form_blocks(func["instrs"]))
        cfg.add_terminators(blocks)

        in_, out = df_worklist(blocks, analysis)
        for block in blocks:
            print("{}:".format(block))
            print("  in: ", fmt(in_[block]))
            print("  out:", fmt(out[block]))


def gen(block):
    """Variables that are written in the block."""
    return {i["dest"] for i in block if "dest" in i}


def use(block):
    """Variables that are read before they are written in the block."""
    defined = set()  # Locally defined.
    used = set()
    for i in block:
        used.update(v for v in i.get("args", []) if v not in defined)
        if "dest" in i:
            defined.add(i["dest"])
    return used


def cprop_transfer(block, in_vals):
    out_vals = dict(in_vals)
    for instr in block:
        if "dest" in instr:
            if instr["op"] == "const":
                out_vals[instr["dest"]] = instr["value"]
            else:
                out_vals[instr["dest"]] = "?"
    return out_vals


def cprop_merge(vals_list):
    out_vals = {}
    for vals in vals_list:
        for name, val in vals.items():
            if val == "?":
                out_vals[name] = "?"
            else:
                if name in out_vals:
                    if out_vals[name] != val:
                        out_vals[name] = "?"
                else:
                    out_vals[name] = val
    return out_vals


# Dictionary to store block names for deterministic IDs
_block_names = {}

def rd_gen(block):
    """Generate definitions in this block."""
    defs = set()
    # Get block name from the first instruction's label or use a counter
    block_id = id(block)  # Use block's memory address as unique identifier
    if block_id not in _block_names:
        _block_names[block_id] = len(_block_names)
    
    for i, instr in enumerate(block):
        if "dest" in instr:
            # Create unique ID using block number and instruction index
            unique_id = _block_names[block_id] * 1000 + i
            defs.add((instr["dest"], unique_id))
    return defs


def rd_transfer(block, in_defs):
    """Transfer function for reaching definitions."""
    # Kill all previous definitions of variables defined in this block
    killed_vars = {instr["dest"] for instr in block if "dest" in instr}
    surviving_defs = {(var, def_id) for var, def_id in in_defs if var not in killed_vars}
    
    # Add new definitions from this block
    new_defs = rd_gen(block)
    
    return surviving_defs | new_defs

def ae_gen(block):
    """Generate expressions in this block."""
    exprs = set()
    # Operations that don't compute reusable values
    non_expr_ops = {'br', 'jmp', 'ret', 'print', 'call', 'nop'}
    
    for instr in block:
        if "args" in instr and "op" in instr and instr["op"] not in non_expr_ops:
            expr = (instr["op"],) + tuple(instr["args"])
            exprs.add(expr)
    return exprs


def ae_kill(block):
    """Kill expressions that use variables defined in this block."""
    killed = set()
    defined_vars = {instr["dest"] for instr in block if "dest" in instr}
    
    # We need to return a function that can access all expressions
    def kill_func(all_exprs):
        killed_exprs = set()
        for expr in all_exprs:
            # expr is (op, arg1, arg2, ...)
            if len(expr) > 1:  # Has arguments
                expr_args = expr[1:]  # Skip the operation
                # If any argument is redefined, kill this expression
                if any(arg in defined_vars for arg in expr_args):
                    killed_exprs.add(expr)
        return killed_exprs
    return kill_func


def ae_transfer(block, in_exprs):
    """Transfer function for available expressions."""
    # Kill expressions that use variables defined in this block
    kill_func = ae_kill(block)
    killed_exprs = kill_func(in_exprs)
    surviving_exprs = in_exprs - killed_exprs
    
    # Add newly computed expressions from this block
    new_exprs = ae_gen(block)
    
    return surviving_exprs | new_exprs


def ae_intersect(expr_sets):
    """Intersection merge for available expressions (must be available on ALL paths)."""
    expr_sets = list(expr_sets)  # Convert generator to list
    if not expr_sets:
        return set()
    result = set(expr_sets[0])
    for expr_set in expr_sets[1:]:
        result = result.intersection(expr_set)
    return result


ANALYSES = {
    # A really really basic analysis that just accumulates all the
    # currently-defined variables.
    "defined": Analysis(
        True,
        init=set(),
        merge=union,
        transfer=lambda block, in_: in_.union(gen(block)),
    ),
    # Live variable analysis: the variables that are both defined at a
    # given point and might be read along some path in the future.
    "live": Analysis(
        False,
        init=set(),
        merge=union,
        transfer=lambda block, out: use(block).union(out - gen(block)),
    ),
    # A simple constant propagation pass.
    "cprop": Analysis(
        True,
        init={},
        merge=cprop_merge,
        transfer=cprop_transfer,
    ),
    # Reaching definitions analysis: which definitions can reach each point.
    "rd": Analysis(
        True,
        init=set(),
        merge=union,
        transfer=rd_transfer,
    ),
    # Available expressions analysis: which expressions are available at each point.
    "ae": Analysis(
        True,
        init=set(),
        merge=ae_intersect,
        transfer=ae_transfer,
    ),
}

if __name__ == "__main__":
    bril = json.load(sys.stdin)
    run_df(bril, ANALYSES[sys.argv[1]])
