"""
Tree - Genetic Programming Tree Structure.

This module implements the core tree data structure used for genetic programming
in the nature evolution framework. Trees represent executable programs where:
- Each node is a function or terminal value (wrapped in a Codon)
- The tree structure defines the computation flow
- Trees can be mutated, crossed over, and evaluated

Key concepts:
- Node: A single tree node wrapping a Codon (function/value)
- Tree: The container managing a collection of nodes with tree topology
- Evaluation: Trees are callable and execute depth-first
- Mutation: Random tree modifications for evolution
"""

from collections import defaultdict, deque
from copy import deepcopy
from typing import Annotated, Any, Callable, Optional, Self, Sequence, cast
from uuid import uuid4

import black
import graphviz
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from nature.chromosome import Chromosome
from nature.codons import Codon, Inp
from nature.color import Color
from nature.logging import logger
from nature.random import Random
from nature.utils import clamp, is_debug

# Placeholder index value indicating "does not exist"
DNE = -1

NodeArray = Annotated[NDArray, "Node"]


class Node:
    """
    A single node in a genetic programming tree.

    Each node wraps a Codon (function or terminal value) and maintains
    connectivity information within the tree structure. Nodes are callable
    and execute their codon's function when invoked.

    Attributes:
        codon: The wrapped function/value that this node represents
        index: Position in the tree's node array
        parent_index: Index of this node's parent (-1 if root)
        child_indices: Indices of child nodes in tree array
        depth: Distance from root (0 for root)
        height: Maximum distance to any leaf descendant
        size: Number of descendants (including self)
        value: Cached result for terminal nodes or memoized functions
        ctx: Optional context dict passed during evaluation
    """

    def __init__(self, codon: Codon) -> None:
        """
        Initialize a node with a codon.

        For terminal codons (nullary, non-input), the value is immediately
        computed and cached for efficiency.
        """
        self.codon = codon
        self.index: int = DNE
        self.index_in_parent: int = DNE
        self.parent_index: int = DNE
        self.child_indices: list[int] = []
        self.depth: int = 0
        self.height: int = 0
        self.size: int = 0
        self.ctx: dict | None = None
        self.arity_override: int | None = None

        # Reify codon value if terminal (constant terminal, not input node)
        self.value: Any = None

        if self.codon.nullary and not self.codon.is_input:
            try:
                self.eval_codon()  # Pre-compute terminal value
            except:
                logger.exception(f"error executing codon: {self.codon.func_name}")
                if is_debug():
                    breakpoint()
                raise

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.codon.func_name})"

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute this node's codon function.

        Returns cached value if available, otherwise evaluates the codon.
        For input nodes, forwards the tree-level args/kwargs.

        Args:
            *args: Arguments passed from parent node or tree root
            **kwargs: Keyword arguments passed from tree root

        Returns:
            The result of evaluating this node's codon
        """
        # Fast path: return cached terminal/memoized value
        if self.value is not None:
            return self.value

        # Provide execution context to codon (e.g., for dataframe access)
        self.codon.ctx = self.ctx
        try:
            if self.codon.nullary:
                if self.codon.is_input:
                    # Input nodes extract specific args/kwargs by key
                    # E.g., Inp('x') returns kwargs['x'] or args[0] if 'x' is positional
                    return self.codon(*args, **kwargs)
                else:
                    # Terminal nodes (constants) - already evaluated in __init__
                    return self.eval_codon()
            else:
                # Non-terminal nodes: execute function with child results
                value = self.codon(*args, **kwargs)
                # Cache result if codon has memoization enabled
                if self.codon.memo:
                    self.value = value
                return value
        except:
            logger.exception(f"error executing codon: {self.codon.func_name}")
            if is_debug():
                breakpoint()
            raise
        finally:
            # Clean up context reference
            self.codon.ctx = None

    def __eq__(self, other: object) -> bool:
        other = cast(Node, other)
        if self.codon.nullary:
            if self.codon.is_input and other.codon.is_input:
                return cast(Inp, self.codon).key == cast(Inp, other.codon).key
            return self.value == other.value
        else:
            return self.codon is other.codon or self.codon.hash == other.codon.hash

    @property
    def computed_arity(self) -> int:
        return self.arity_override or self.codon.arity

    @classmethod
    def copy(cls, source: "Node") -> "Node":
        dest = type(source)(source.codon)
        dest.depth = source.depth
        dest.index = source.index
        dest.parent_index = source.parent_index
        dest.index_in_parent = source.index_in_parent
        dest.child_indices = source.child_indices.copy()
        dest.value = deepcopy(source.value)
        return dest

    def eval_codon(self, *args, **kwargs) -> Any:
        self.value = self.codon(*args, **kwargs)
        return self.value


class Tree:
    """
    Genetic programming tree representing an executable program.

    A Tree is a collection of Nodes arranged in a tree topology where each node
    contains a Codon (function or terminal). Trees can be:
    - Built from scratch via interpolation
    - Mutated by replacing subtrees
    - Grafted by transplanting subtrees from other trees
    - Compiled into fast native Python functions
    - Rendered as Python code or visual graphs

    Attributes:
        chromosome: Grammar defining allowed codons and tree structure
        nodes: Array of Node objects forming the tree
        size: Number of nodes in the tree
        capacity: Maximum number of nodes allowed
        target_size: Desired tree size for fitness evaluation
        func: Compiled callable (lazy-compiled on first execute)
    """

    def __init__(
        self,
        chromosome: Chromosome,
        nodes: NodeArray | None = None,
        context: dict | None = None,
    ) -> None:
        """
        Initialize a tree with a chromosome grammar.

        Args:
            chromosome: Grammar defining codons and tree constraints
            nodes: Optional pre-existing nodes array for cloning
            context: Optional context dict passed to nodes during evaluation
        """
        self.chromosome = chromosome
        self.random = chromosome.random
        self.nodes: NodeArray = np.array(nodes if nodes is not None else [None])
        self.func: Callable | None = None  # lazily compiled function
        self.n_input_codons: int = 0
        self.ctx = context or {}

        mu = chromosome.mu
        sigma = chromosome.sigma
        k = chromosome.k_sigma

        self.size = 0
        self.capacity = int(mu + k * sigma)
        self.target_size = int(max(2, self.random.gauss(mu, k * sigma)))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.execute(*args, **kwargs)

    def __getstate__(self) -> object:
        state = self.__dict__.copy()
        state.pop("func", None)  # dynamic function is not pickle-able
        state["local"] = {}  # clear process-local state
        return state

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the tree program with given arguments.

        Lazily compiles the tree into a native Python function on first call,
        then executes it with the provided arguments.

        Args:
            *args: Positional arguments passed to the tree function
            **kwargs: Keyword arguments passed to the tree function

        Returns:
            The result of executing the compiled tree function
        """
        if not getattr(self, "func", None):
            self.compile(context=self.ctx)
        assert self.func is not None
        return self.func(*args, **kwargs)

    def validate_size(self) -> bool:
        """
        Check if tree size is within valid bounds.

        Returns:
            True if tree size is between min and max chromosome constraints
        """
        return (
            self.size >= self.chromosome.min_tree_size
            and self.size <= self.chromosome.max_tree_size
        )

    @property
    def fullness(self) -> float:
        """
        Calculate how full the tree is relative to target size.

        Returns:
            Ratio of actual size to target size (e.g., 0.8 = 80% full)
        """
        return self.size / self.target_size

    @classmethod
    def copy(cls, source: "Tree") -> "Tree":
        """
        Create a deep copy of a tree.

        Args:
            source: Tree to copy

        Returns:
            New Tree instance with copied nodes
        """
        clone = cls(chromosome=source.chromosome, nodes=source.nodes)
        clone.build(copy=True)
        return clone

    def build(
        self,
        interpolate=True,
        copy=False,
        graft: Optional["Graft"] = None,
    ) -> Self:
        """
        Construct the tree structure by traversing and connecting nodes.

        Builds the tree in breadth-first order, creating nodes through interpolation
        or copying existing ones. Updates node metadata (depth, height, size) and
        establishes parent-child relationships.

        Args:
            interpolate: If True, create missing nodes by selecting compatible codons.
                        If False, stop at incomplete nodes.
            copy: If True, deep-copy existing nodes instead of reusing them
            graft: Optional Graft object specifying a subtree to transplant

        Returns:
            Self for method chaining

        Raises:
            IndexError: If interpolation cannot find compatible codon for a position
        """
        root = self.nodes[0] or Node(self.chromosome.output_codon)
        root.parent_index = DNE
        root.index_in_parent = DNE
        root.index = 0
        root.height = 0
        root.depth = 0
        root.size = 0

        queue: deque[tuple[Node | None, Node]] = deque([(None, root)])
        nodes: NodeArray = np.empty(self.capacity, dtype=object)

        self.size = 0
        self.n_input_codons = 0
        self.func = None

        while queue:
            index = self.size
            prev_parent, parent = queue.popleft()
            # print(parent, parent.depth, len(nodes) / self.capacity)

            # Ensure sufficient self.nodes array capacity
            if self.size >= nodes.size:
                nodes = np.concat([nodes, np.empty(self.capacity, dtype=object)])

            # Begin grafting in a subtree at the current nodes index?
            if graft and index == graft.dst_node_index:
                if prev_parent is not None:
                    prev_parent.child_indices[parent.index_in_parent] = index

                # Replace the normal "parent" node with a copy of the root graft node
                graft_root = Node.copy(graft.src_tree.nodes[graft.src_node_index])
                graft_root.index_in_parent = parent.index_in_parent
                graft_root.parent_index = parent.parent_index
                graft_root.depth = parent.depth
                graft.visited.add(id(graft_root))

                parent = graft_root
            elif prev_parent is not None:
                # we're not grafting, proceed normally
                prev_parent.child_indices[parent.index_in_parent] = index

            parent.index = index
            nodes[index] = parent if not copy else Node.copy(parent)

            if parent.codon.is_input:
                self.n_input_codons += 1

            # Increment node counter, since nodes itself is fixed len array
            self.size += 1

            # Ensure parent.child_indices has elements if non-terminal
            if not parent.codon.nullary and not parent.child_indices:
                parent.child_indices = [DNE] * parent.computed_arity

            # Upsert child nodes of parent
            for i_child, child_index in enumerate(parent.child_indices):
                child: Node | None = None
                # If node is from the graft source tree, the child should also
                # come from graft source:
                if graft and id(parent) in graft.visited:
                    child = Node.copy(graft.src_tree.nodes[child_index])
                    graft.visited.add(id(child))

                # Only procede with normal node copying/interpolation process IF
                # we haven't already bound child via the grafting step above:
                if child is None:
                    if child_index == DNE:
                        # Get or create the child node
                        if interpolate:
                            # Interpolate subtree
                            child = self.interpolate(parent, i_child, parent.depth + 1)
                        else:
                            continue  # Ignore the NIL
                    else:
                        # Use existing child node
                        child = cast(Node, self.nodes[child_index])

                assert child is not None

                # Set common child node meta
                child.parent_index = parent.index
                child.index_in_parent = i_child
                child.depth = parent.depth + 1
                child.height = 0

                queue.append((parent, child))

        # Update sub-tree heights and cumulative sizes. O(N)
        for parent in reversed(nodes[: self.size]):
            parent = cast(Node, parent)
            parent.size = sum(nodes[i].size for i in parent.child_indices if i != DNE) + 1
            if parent.child_indices:
                parent.height = max(
                    (nodes[i].height + 1 for i in parent.child_indices if i != DNE), default=0
                )

        # Replace old self.nodes
        self.nodes = nodes
        return self

    def interpolate(self, parent: Node, child_index: int, child_depth: int) -> Node:
        """
        Create a new child node compatible with parent's type requirements. It's
        called "interpolate" because it interpolates nodes into a tree's node
        array.

        Selects a random codon from those compatible with the parent's expected
        input types at the given child position and depth.

        Args:
            parent: Parent node requiring a child
            child_index: Index in parent's argument list (0-indexed)
            child_depth: Depth of the new child node in tree

        Returns:
            New Node with compatible codon

        Raises:
            IndexError: If no compatible codons exist for this position
        """
        candidate_codons = self.chromosome.find_compatible_child_codons(
            parent=parent.codon,
            child_index=child_index,
            child_depth=child_depth,
            fullness=self.fullness,
        )

        if candidate_codons.any():
            codon = self.random.np_choice(candidate_codons)
            return Node(codon)

        raise IndexError(
            f"no codons compatible with {parent} at child index {child_index} "
            f"{parent.codon.arg_names[child_index]} "
            f"in tree {self.chromosome.name}. Required child with return types: "
            f"{parent.codon.arg_types[child_index]} in tree {self.chromosome.name} "
            f"at depth {child_depth}"
        )

    def similarity(self, other: "Tree") -> float:
        """Return a real value number between 0.0 and 1.0. The number indicates
        the ratio of similar nodes to the total number of comparable between the
        two trees. For example, if both trees have 5 nodes, we compare them
        piecewise, checking for identical terminal values and, for internal
        nodes, identical codons. If 3 of 5 are identical, the similarity is 3/5.

        Moreover,  if the trees have a differing number of nodes, then this is
        reflected in the fact that the max node array length is used in the
        denominator. So if one tree has len 5 and the other 7, the max possible
        similarity score would be 5/7.

        Args:
            other (ExpressionTree): Tree to compare.

        Returns:
            float: Real value from 0-1. 0 Means no similarity. 1 Means exact match.
        """
        return 0
        # TODO: redo this more efficiently. like maybe precompute in build
        # smaller_len, larger_len = sorted([self.size, other.size])
        # n_similar: float = (
        #     cast(NDArray, self.nodes[:smaller_len] == other.nodes[:smaller_len]).astype(float).sum()
        # )
        # return float((n_similar / larger_len) if larger_len else 0)

    def mutate(self, n_attempts: int = 3) -> bool:
        """Mutates the tree in-place a given number of times. It tries to select
        `n_nodes` distinct nodes to mutate. We delete each selected node and
        replace it with a new interpolated random subtree.

        Args:
            n_nodes (int, optional): Number of nodes to mutate.

        Returns:
            bool: True if mutation successful
        """
        # Iterate through randomly chosen node indices, setting their
        # corresponding entries in their parent's child_indices arrays to NIL.
        # Then, we simply call rebuild with interpolate, which handles the
        # generation and insertion of new subtrees.
        for index in self.random.np_choice(
            np.arange(1, min(self.capacity, self.size)),
            size=int(clamp(n_attempts, 1, self.size - 1)),
            replace=False,
        ):
            node = cast(Node, self.nodes[index])
            if node.codon.mutable:
                parent = cast(Node, self.nodes[node.parent_index])
                parent.child_indices[node.index_in_parent] = DNE
                self.build(interpolate=True)
                return True

        return False

    def graft(
        self,
        donor: "Tree",
        i_src: int | None = None,
        i_dst: int | None = None,
        strict=False,
        max_capacity_multiplier: float = 1.0,
    ) -> bool:
        """Copy a random subtree from other into self, provided there exists
        compatible nodes between the two.

        Args:
            donor Tree: Tree from which we're grafting a Node.
            i_src: Index of the root donor node being grafted in. If none, a
            node is chosen at random, with smaller trees exponentially weighted
            in proportion to this tree's current fullness percent.
            i_dst: Index of the node in self.nodes to replace with the graft
            root node.
            strict: raise on error insteada of returning False
            max_capacity_multiplier: A multiplier of 1.0 means that the
            resultant tree size shouldn't grow beyond the base capacity defined
            in the tree's chromosome.  1.4 would mean that the resultant tree
            could be up to 40% larger than its chromosomes base capacity.

        Returns:
            bool: True if graft successful
        """
        # If no index in the donor/source tree is given:
        #   choose a subtree at random. If this tree is already near or over the
        #   base chromosome capacity, we select a node from the donor lower in
        #   its own tree, using an exponential distribution
        if i_src is None:
            i_src = self.random.randrange(1, donor.size)

        # Source_node is the root node of the subtree we're grafting in.
        src_node = cast(Node, donor.nodes[i_src])

        # Find a matching node in self with respect to the parent's expectation
        # of the source node's return type.
        if i_dst is not None and i_dst > 0:
            dst_node = cast(Node, self.nodes[i_dst])
            parent = cast(Node, self.nodes[dst_node.parent_index])
            allowed_ret_types = set(parent.codon.arg_types[dst_node.index_in_parent])
            if not allowed_ret_types.intersection(src_node.codon.ret_types):
                if strict:
                    raise IndexError(
                        f"source node {src_node} cannot be grafted into index {i_dst}"
                        "because the node.ret_types is incompatible with the parent"
                    )
                return False
        else:
            # Filter nodes in self.nodes based on parent node arg type
            # expectations to create an array of candidate nodes to choose the
            # target replacement node from, where we graft in the source node
            src_ret_types = set(src_node.codon.ret_types)
            dst_node_candidates = np.fromiter(
                (
                    dst_node
                    for dst_node in cast(
                        Sequence[Node], self.nodes[1 : min(self.capacity, self.size)]
                    )
                    if self.chromosome.allows_codon_at_depth(src_node.codon, dst_node.depth)
                    and src_ret_types.intersection(
                        cast(Node, self.nodes[dst_node.parent_index]).codon.arg_types[
                            dst_node.index_in_parent
                        ]
                    )
                ),
                dtype=object,
            )
            if not dst_node_candidates.any():
                if strict:
                    raise IndexError(f"no candidate in dst tree for graft root {src_node}")
                return False
            else:
                dst_node = cast(Node, self.random.np_choice(dst_node_candidates))

        assert src_node is not None
        assert dst_node is not None

        # print(self.size, donor.size, src_node.size, dst_node.size)
        # print(i_src, i_dst)

        # Enforce tree size constraints such that the tree size stats (mean
        # size, std, etc) remain pretty fairly constant and bounded over time.
        new_proposed_size = self.size - dst_node.size + src_node.size
        if new_proposed_size >= max_capacity_multiplier * self.capacity:
            if strict:
                raise IndexError(
                    f"graft generated new tree size of {new_proposed_size} which is "
                    f"greater than the max: {max_capacity_multiplier*self.capacity}"
                )
            return False

        self.build(interpolate=False, graft=Graft(donor, src_node.index, dst_node.index))

        return True

    def compile(self, context: dict | None = None, deepcopy_values=False) -> Self:
        """
        Compile tree into a fast native Python function.

        Translates the tree structure into Python code and compiles it using exec().
        The compiled function runs ~10x faster than interpreted node-by-node execution.
        Compilation is lazy - occurs automatically on first execute() call.

        Args:
            context: Optional context dict made available to nodes during execution
            deepcopy_values: If True, deep-copy terminal values into function scope

        Returns:
            Self for method chaining (now with self.func compiled)
        """
        # Build the dynamically compiled function's lexical scope, consisting of
        # each node's codon's func name mapped to the instance itself, along
        # with the tree's node array.
        nodes = cast(Sequence[Node], self.nodes[: self.size])
        scope: dict = dict(
            **self.chromosome.compiled_scope,
            _X=np.empty(self.size, dtype=object),
            _F=np.empty(self.size, dtype=object),
        )
        for i, node in enumerate(nodes):
            node.ctx = context
            scope["_X"][i] = deepcopy(node.value) if deepcopy_values else node.value
            scope["_F"][i] = node

        # Compile that thang!
        exec(self.render_func_def(pretty=False, expand=False), scope)

        # Extract the compiled callable, which should have been created in the
        # scope dict, under the name of its chromosome.
        self.func = scope[self.chromosome.name]

        return self

    def render_func_def(self, pretty=True, expand=True) -> str:
        """
        Generate Python source code representing this tree.

        Translates the tree structure into executable Python function definition.
        Used by compile() and useful for debugging/visualization.

        Args:
            pretty: If True, format code with black for readability
            expand: If True, inline terminal values for readability.
                   If False, use array references (_X[i]) for compact output

        Returns:
            Python function definition as a string

        Example:
            >>> tree.render_func_def(pretty=True, expand=True)
            def regress(x):
                _x1 = 2.5
                _x2 = x ** _x1
                return _x2
        """
        stack: deque[Any] = deque()
        assignments = []
        arg_index = 1

        nodes = cast(Sequence[Node], self.nodes[: self.size])
        for node in reversed(nodes):
            codon = node.codon

            if codon.is_input:
                arg_name = cast(Inp, codon).arg_names[0][0]
                stack.appendleft(arg_name)
            elif node.codon.nullary:
                arg_name = f"_x{arg_index}"
                if expand:
                    assignments.append(f"{arg_name}={node.value}")
                else:
                    assignments.append(f"{arg_name}=_X[{node.index}]")
                stack.appendleft(arg_name)
                arg_index += 1
            else:
                arg_name = f"_x{arg_index}"
                arg_index += 1
                arity = node.computed_arity
                if codon.operator:
                    args = f" {codon.operator} ".join(stack.pop() for _ in range(arity))
                    assignments.append(f"{arg_name}={args}")
                else:
                    # Render a function/codon call
                    args_str = ",".join(reversed([stack.pop() for _ in range(arity)]))
                    if expand:
                        if codon.is_output:
                            stack.appendleft(f"({args_str})")
                            continue
                        else:
                            assignments.append(f"{arg_name}={codon.func_name}({args_str})")
                    else:
                        assignments.append(f"{arg_name}=_F[{node.index}]({args_str})")
                stack.appendleft(arg_name)

        retval_str = stack[0]
        assignments_str = "\n ".join(assignments)
        body = f"\n {assignments_str}\n return {retval_str}"
        func_def = self.chromosome.func_def_template.format(body)
        return (black.format_str(func_def, mode=black.Mode()) if pretty else func_def).strip()

    @staticmethod
    def render_call_graph(
        trees: dict[str, "Tree"],
        title: str | None = None,
        horizontal=True,
        distinct_colors_min_depth=2,
    ) -> None:
        """
        Render tree structure as a visual graph using Graphviz.

        Creates a directed graph visualization showing the tree's node structure
        with color-coding by depth and labeled edges. Useful for debugging and
        understanding evolved programs.

        Args:
            trees: Dictionary mapping tree names to Tree instances to visualize
            title: Optional title for the graph. If None, uses chromosome name
            horizontal: If True, lay out graph left-to-right. If False, top-to-bottom
            distinct_colors_min_depth: Minimum depth before applying color variation

        Side Effects:
            Opens rendered graph in default viewer
        """
        graph = graphviz.Digraph(format="png", name=title, engine="dot")
        parent_color_dict = defaultdict(lambda: Color.random(luminosity=0.7))
        arrow_shape = "cds" if horizontal else "invhouse"

        with graph.subgraph(name="cluster_legend") as legend:  # type: ignore
            legend.attr(label="Legend")
            legend.attr(style="dashed")
            legend.attr(fontname="Sans")

            # Nodes for legend
            legend.node("L2", "Terminal", fontname="Sans", shape="box")
            legend.node(
                "L3",
                "Input",
                fontname="Sans",
                shape=arrow_shape,
                style="filled",
                fillcolor="#acf",
            )
            legend.node(
                "L1",
                "Function",
                fontname="Sans",
                style="filled",
                fillcolor="#efe",
                shape="ellipse",
                penwidth="2",
            )

        for name, tree in trees.items():
            with graph.subgraph(name=f"cluster_{name}") as s:  # type: ignore
                s.attr(fontname="Sans")
                s.attr(style="filled", fillcolor="#eee", label=name.replace("_", " ").title())
                for node in cast(Sequence[Node], tree.nodes[1 : tree.size]):
                    if node.depth <= distinct_colors_min_depth:
                        color = Color.random(luminosity=0.7)
                        parent_color_dict[node.index] = color
                    else:
                        color = parent_color_dict[node.parent_index]
                        parent_color_dict[node.index] = color

                    color = color.copy()
                    color.luminosity += (
                        0.2 * (node.depth / tree.nodes[0].height) if tree.nodes[0].height else 0
                    )

                    arity = node.computed_arity

                    s.node(
                        str(id(node)),
                        label=(
                            (
                                # f"{str(cast(Inp,node.codon).key).replace('_', ' ')}: {' | '.join(t.__name__ for t in node.codon.arg_types[0])}  "
                                f"{str(cast(Inp,node.codon).key).replace('_', ' ')}  "
                                if node.codon.is_input
                                else str(node.value)
                            )
                            if (node.value is not None or node.codon.is_input)
                            and node.codon.nullary
                            else (
                                node.codon.func_name.replace("_", " ").title()
                                + ("  " if node.codon.is_output else "")
                            )
                        ),
                        style="filled",
                        fillcolor=(
                            ("white" if not node.codon.is_input else "#acf")
                            if node.codon.nullary
                            else color.to_hex()
                        ),
                        fontname="Sans",
                        shape=(
                            (
                                ("box" if node.codon.nullary else "ellipse")
                                if node.index > 0
                                else arrow_shape
                            )
                            if not (node.codon.is_input)
                            else arrow_shape
                        ),
                        penwidth=str(2 if (not node.codon.is_input and arity > 0) else 1),
                    )

                    for i, child_index in enumerate(node.child_indices):
                        child = cast(Node, tree.nodes[child_index])
                        s.edge(
                            str(id(node)),
                            str(id(child)),
                            arrowhead="normal",
                            label=node.codon.arg_names[i].replace("_", " "),
                            fontsize="10",
                            fontcolor="#333",
                            fontname="Sans",
                            dir="back",
                        )

        graph.attr(label=title, labelloc="t", fontsize="20", fontname="Sans")
        graph.attr(dpi="96")
        graph.attr(rankdir="RL" if horizontal else None)
        graph.render(title, view=True, cleanup=True)


class Graft:
    def __init__(
        self,
        src_tree: Tree,
        src_node_index: int,
        dst_node_index: int,
    ):
        self.graft_id = uuid4().hex
        self.src_tree = src_tree
        self.src_node_index = src_node_index
        self.dst_node_index = dst_node_index

        # For use by Tree.build only when applying the graft:
        self.visited: set[int] = set()
