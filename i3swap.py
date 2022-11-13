#!/usr/bin/env python
from typing import Literal, Optional
from sys import stderr
from argparse import ArgumentParser
from i3ipc import Connection, Con


def print_or_nodes(o: Con, depth: int = 0) -> str:
    name = o.name or ""
    print(
        f"{'  '*depth}{o.type}: {o.id} {name:.42} ({o.layout} with {len(o.nodes)} children)"
    )
    if o.nodes:
        for n in o.nodes:
            print_or_nodes(n, depth + 1)


def find_swapee(
    focused_container: Con,
    layout: Literal["horizontal", "vertical"],
    level: Literal["highest", "lowest"],
    neighbor: Literal["first", "last"],
    swapee: Literal["first", "last"],
    verbose: int = 0,
) -> Optional[Con]:
    """Return swapee depending on criteria

    workspace: 94403059612560 2 (splith with 1 children)
      con: 94403059613056  (splith with 1 children)
        con: 94403059613520  (splith with 1 children)
          con: 94403059613984  (splith with 1 children)
            con: 94403058970656  (splith with 1 children)
              con: 94403059981248  (splith with 1 children)
                con: 94403060009888  (splith with 2 children)                                                       < common_parent with children(!) (splith, highest)
                  con: 94403060353904  (splitv with 2 children)
                    con: 94403059614448 Tilix: vim i3swap.py (splith with 0 children)                               < swapee (splith, highest, first)
                    con: 94403060624480 Tilix: ~ (splith with 0 children)                                           < swapee (splith, highest, last)
                  con: 94403060104288  (splitv with 3 children)
                    con: 94403060153328 Tilix: IPython: home/syphdias (splith with 0 children)
                    con: 94403059853696  (splith with 2 children)                                                   < common_parent with children(!) (splith, lowest)
                      con: 94403060640272  (splitv with 2 children)
                        con: 94403060477552 Tilix: ~ (splith with 0 children)                                       < swapee (splith, lowest, first)
                        con: 94403060027792 Tilix: ~ (splith with 0 children)                                       < swapee (splith, lowest, last)
                      con: 94403060474048  (splitv with 3 children)
                        con: 94403060338064 Tilix: ~/git/private/i3-swap (splith with 0 children)
                        con: 94403060644688 Tilix: ~/git/private/i3-swap/i3swap.py --l (splith with 0 children)     < focused_container
                        con: 94403060524208 Tilix: ~ (splith with 0 children)
                    con: 94403059044416 Tilix: ~ (splith with 0 children)
    """
    if verbose >= 2:
        print_or_nodes(focused_container.workspace())

    if layout == "vertical":
        layout = "splitv"
    else:
        layout = "splith"

    current_container = focused_container
    # find the parent container containing the focused container
    # and the one we want to swap with
    common_parent = None
    while current_container.type != "workspace":
        if current_container.layout == layout and len(current_container.nodes) > 1:
            # we found the FIRST container with the wanted layout
            # decend in the first node that we did not come from
            common_parent = current_container
            if level == "lowest":
                break
        if len(current_container.parent.nodes) > 1:
            focused_half = current_container
        current_container = current_container.parent

    # return None if no common parent was found
    if not common_parent:
        common_parent = focused_half.parent

    # we found the current parent, now we need to select a not focused neighbor

    # pick either the first (default) or the last neighbor
    neighbor_index = 0
    if neighbor == "last":
        neighbor_index = -1

    swapee_neighbor = [node for node in common_parent.nodes if node != focused_half][0]

    # pick either the first (default) or the last container in the swapee half
    swapee_index = 0
    if swapee == "last":
        swapee_index = -1

    # we found the focused neighbor, now we need to decent into it
    # to find the swapee (first container we find)
    while len(swapee_neighbor.nodes) > 0:
        swapee_neighbor = swapee_neighbor.nodes[swapee_index]
    swapee = swapee_neighbor

    if verbose >= 2:
        print("common parent:", common_parent.id)
        print("  focused half:", focused_half.id)
        print("  swapee half:", swapee_neighbor.id)
        print("    swapee:", swapee.id)

    return swapee


def main(args) -> None:
    i3 = Connection()
    tree = i3.get_tree()
    focused_container = tree.find_focused()

    swapee = find_swapee(
        focused_container,
        layout=args.layout,
        level=args.level,
        neighbor=args.neighbor,
        swapee=args.swapee,
        verbose=args.verbose,
    )

    if not swapee:
        if args.verbose:
            print("Found no swapee. Nothing to swap.")
        return

    move_result = focused_container.command(f"swap container with con_id {swapee.id}")
    if args.verbose:
        print(move_result[0].ipc_data)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "--layout",
        default="horizontal",
        choices=["horizontal", "vertical"],
        help="Swap horizontally or vertically",
    )
    parser.add_argument(
        "--level",
        default="highest",
        choices=["highest", "lowest"],
        help="Select which hierarchy level you want swap with",
    )
    parser.add_argument(
        "--neighbor",
        default="first",
        choices=["first", "last"],
        help="Take first or last to select the neighbor to swap with",
    )
    parser.add_argument(
        "--swapee",
        default="first",
        choices=["first", "last"],
        help="Take first or last container in the swapping container",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
    )

    args = parser.parse_args()

    if args.verbose:
        print(args)

    main(args)
