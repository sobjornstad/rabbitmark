"""
binary_search.py - helper code for binary search algorithm
"""
from math import ceil, log2
from typing import List, Tuple


class BisectionState:
    """
    Abstraction for carrying out a binary search, automatically or (especially)
    manually.

    The BisectionState does not care about your actual data; instead, it
    manages the state of the search space, with a zero-based index and lower
    and upper bounds. The primary method of interacting with it is by
    retrieving the current index/pivot point (/index/ property) and indexing
    into your data to determine whether you have found the item and which way
    to narrow the search space, then calling mark_after(), mark_before(), or
    backtrack() to choose where to look next.

    Backtracking is supported for the convenience of manual searching, where
    the user may notice they've made a mistake and want to try again. A call
    to backtrack() simply restores the state at the previous step. You can
    backtrack all the way up to the initial state if needed.

    A variety of properties are also provided to aid in the presentation of
    user interfaces for manual binary searching, such as at_end, which
    indicates whether the index is currently on the last item.

    Constructor parameters:
        num_items    - The total number of items to search in
        start_at_end - If True, start the search with the last item
                       and then jump back to the middle if it's not selected.
                       Convenient for some types of searches like
                       finding a working version of something, where the most recent
                       is unusually likely to be the goal.
    """
    def __init__(self, num_items: int, start_at_end: bool = False) -> None:
        assert num_items > 0, "Must have at least one item to bisect."

        self.num_items = num_items  #: total number of items in the bisection set
        self.lower = 0              #: lowest index in current search space
        self.upper = num_items-1    #: highest index in current search space
        if start_at_end:
            self.index = self.upper #: current pivot point
        else:
            self.index = num_items // 2
        #: history of past values of 3 variables above
        self.stack: List[Tuple[int, int, int]] = []

    ### State checks ###
    @property
    def at_end(self) -> bool:
        "Whether we are looking at the last item in the full list (NOT search window)."
        return self.index == self.num_items - 1

    @property
    def at_start(self) -> bool:
        "Whether we are looking at the first item in the full list."
        return self.index == 0

    @property
    def at_only(self) -> bool:
        "Whether we are looking at the only item in the full list."
        return self.num_items == 1

    @property
    def can_go_after(self) -> bool:
        """
        We can choose an item after the current one unless we're on the last one
        in the search window.
        """
        return self.index < self.upper

    @property
    def can_go_before(self) -> bool:
        """
        We can choose an item before the current one unless we're on the first one
        in the search window.
        """
        return self.index > self.lower

    @property
    def can_backtrack(self) -> bool:
        "We can backtrack as long as we have at least one previous choice on record."
        return len(self.stack) > 0

    @property
    def remaining_steps(self) -> int:
        "The maximum number of steps it will take to converge on a single value."
        if self.upper - self.lower == 0:
            return 0
        elif self.upper - self.lower == 1:
            return 1
        else:
            return ceil(log2(self.upper - self.lower))


    ### Save/restore functionality ###
    def _memento(self) -> Tuple[int, int, int]:
        "Save off the state variables for possible later restoration."
        return (self.lower, self.upper, self.index)

    def _restore(self, memento: Tuple[int, int, int]):
        "Return the state of the bisector to that encapsulated in the /memento/."
        self.lower, self.upper, self.index = memento


    ### Bisection steps ###
    def mark_after(self) -> None:
        "Indicate the desired item is after this one."
        assert self.can_go_after, "Invalid bisection step! Already at end."
        self.stack.append(self._memento())
        self.lower = self.index + 1
        increase_by = (self.upper - self.index + 1) // 2
        self.index = self.index + increase_by

    def mark_before(self) -> None:
        "Indicate the desired item is before this one."
        assert self.can_go_before, "Invalid bisection step! Already at beginning."
        self.stack.append(self._memento())
        self.upper = self.index - 1
        decrease_by = (self.index - self.lower + 1) // 2
        self.index = self.index - decrease_by

    def backtrack(self) -> None:
        "Back up to the previous choice point."
        assert self.can_backtrack, "Invalid bisection step! No steps to back out."
        self._restore(self.stack.pop())
