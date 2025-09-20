This folder contains all files necessary for assignment 1

In this folder you will see the: 
    mycfg.py file
    test folder

The mycfg.py file has the code that I use to create the cfg. I made it following the first Bril video assigned

The four required functions are found in the mycfg.py file. They are all placed at the top. The functions are the following: 
    
    get_path_lengths(cfg, entry): To find the shortest path, I made a BFS. This would find the shortest path lengths from the entry point given in the CFG. I set up distances and the queue to start with the entry. I use queue so that it goes in order from the entry. 

    reverse_postorder(cfg, entry): Here, I use DFS to visit every node and mark them as visited which helps to avoid cycles and then records nodes in postorder. Then I return the postorder list reversed. 

    find_back_edges(cfg, entry): Again, I use DFS tracking visited nodes and nodes that are in the recursion stack to check for cycles. If the successor is already in the stack then the edge is a back edge. 

    is_reducible(cfg, entry): I am checking if it is reducible by finding all back edges and checking that for each back edge, the target is closer to the entry node than the source with using shortest path distances. I use my previous functions to get back edges and shortest paths from the entry. If it doesn't match the reducibility condition, it will return false. 

The test directory has the files I used to test the functions. I grabbed these test cases from the examples found inside 
bril\test\interp\core
bril\benchmark\core
bril\examples\test\df

I have the turnt file in the test folder which can run all tests by running
    turnt {filename.bril}
There is one thing and it is that the way I have it setup, if this is tested, you must change the string argument every run since it may be different per run. So you would have to go into the mycfg.py file and change the argument. 

