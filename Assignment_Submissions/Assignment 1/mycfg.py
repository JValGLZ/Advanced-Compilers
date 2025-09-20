import json
import sys


def get_path_lengths(cfg, entry):

    distances = {entry: 0}
    queue = [entry]
    
    while queue:
        current = queue.pop(0)
        current_dist = distances[current]
        
        for successor in cfg.get(current, []):
            if successor not in distances:
                distances[successor] = current_dist + 1
                queue.append(successor)
    
    return distances



def reverse_postorder(cfg, entry):

    visited = set()
    postorder = []
    
    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        
        for successor in cfg.get(node, []):
            dfs(successor)
        
        postorder.append(node)
    
    dfs(entry)
    return postorder[::-1]



def find_back_edges(cfg, entry):

    visited = set()
    in_stack = set()
    back_edges = []
    
    def dfs(node):
        visited.add(node)
        in_stack.add(node)
        
        for successor in cfg.get(node, []):
            if successor in in_stack:
                back_edges.append((node, successor))
            elif successor not in visited:
                dfs(successor)
        
        in_stack.remove(node)
    
    dfs(entry)
    return back_edges


def is_reducible(cfg, entry):
    back_edges = find_back_edges(cfg, entry)
    
    for tail, head in back_edges:
        distances = get_path_lengths(cfg, entry)
        if head not in distances or tail not in distances:
            return False
        if distances[head] >= distances[tail]:
            return False
    
    return True

# ================================================================
# ================================================================
# MYCFG CODE




TERMINATORS = 'jmp', 'br', 'ret'

def form_blocks(body):
    curr_block = []
    for instr in body: 
        if 'op' in instr: 
            curr_block.append(instr)

            if instr['op'] in TERMINATORS:
                yield curr_block
                curr_block = []

        else:  
            if curr_block:
                yield curr_block
            curr_block = [instr]  

    if curr_block:
        yield curr_block

def block_map(blocks):
    out = {}

    for block in blocks:
        if block and 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = 'b{}'.format(len(out))

        out[name] = block
    return out

def get_cfg(name2block):

    out = {}
    names = list(name2block.keys())
    for i, (name, block) in enumerate(name2block.items()):
        if not block:
            succ = []
        else:
            last = block[-1]
            op = last.get('op')
            if op in ('jmp', 'br'):
                succ = last.get('labels', [])
            elif op == 'ret':
                succ = []
            else:
                if i + 1 < len(names):
                    succ = [names[i + 1]]
                else:
                    succ = []
        out[name] = succ
    return out


def mycfg():
    cfgload = None
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        cfg = get_cfg(name2block)
        cfgload = cfg

        print('digraph {} {{'.format((func['name'])))
        for name in name2block:
            print('   {}'.format(name))
        for name, succs in cfg.items():
            for succ in succs:
                print('   {} -> {}'.format(name, succ))
        print('}')
    
    # print (cfgload)
    return cfgload





if __name__ == "__main__":
    cfg = mycfg()
    
    
    print(get_path_lengths(cfg, 'b0'))
    print(reverse_postorder(cfg, 'b0'))
    print(find_back_edges(cfg, 'b0'))
    print(is_reducible(cfg, 'b0'))
