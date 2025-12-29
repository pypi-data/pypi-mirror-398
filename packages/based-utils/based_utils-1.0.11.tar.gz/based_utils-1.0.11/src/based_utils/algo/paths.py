from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Hashable
from functools import cached_property, total_ordering
from queue import PriorityQueue
from typing import TYPE_CHECKING, ClassVar, Self

if TYPE_CHECKING:
    from collections.abc import Iterator
    from queue import Queue


class NoPathFoundError(Exception):
    pass


class ShortestPath[S: State](ABC):
    def __init__(self, begin_state: S) -> None:
        self.begin_state: S = begin_state
        self._end_state: S | None = None
        self.visited_states: set[S] = set()

    @property
    def end_state(self) -> S:
        """Get the complete path by traversing back to the start."""
        if self._end_state is None:
            raise NoPathFoundError
        return self._end_state

    @abstractmethod
    def _states_to_explore(self) -> Iterator[S]: ...

    @abstractmethod
    def _mark_as_state_to_explore(self, state: S) -> None: ...

    def find(self) -> Self:
        state = self.begin_state
        self._mark_as_state_to_explore(state)

        for state in self._states_to_explore():
            if state.is_end_state:
                # We found our path.
                self._end_state = state
                return self

            # Path not found, explore next states worth visiting.
            for next_state in state.next_states:
                if next_state in self.visited_states:
                    continue

                # Note: self._should_visit_state() will have side-effects.
                if self._should_visit_state(next_state):
                    self._mark_as_state_to_explore(next_state)

            self._after_state_explored(state)

        # No more states worth exploring before we could reach an end state.
        raise NoPathFoundError

    @abstractmethod
    def _after_state_explored(self, state: S) -> None: ...

    @abstractmethod
    def _should_visit_state(self, state: S) -> bool: ...

    @property
    def states(self) -> Iterator[S]:
        """Get the complete path by traversing back to the start."""
        return reversed(list(self.end_state.previous_states))

    @property
    def length(self) -> int:
        return self.end_state.cost


class ShortestPathBFS[S: BFSState](ShortestPath[S]):
    def __init__(self, begin_state: S) -> None:
        super().__init__(begin_state)
        self._queue: deque[S] = deque()

    def _states_to_explore(self) -> Iterator[S]:
        while self._queue:
            yield self._queue.popleft()

    def _mark_as_state_to_explore(self, state: S) -> None:
        self._queue.append(state)

    def _after_state_explored(self, state: S) -> None:
        pass

    def _should_visit_state(self, state: S) -> bool:
        self.visited_states.add(state)
        return True


class ShortestPathDijkstra[S: DijkstraState](ShortestPath[S]):
    def __init__(self, begin_state: S) -> None:
        super().__init__(begin_state)
        # DijkstraStates implement __lt__(), where state1 < state2 would mean:
        # state1 will pop from the queue sooner than state2 does.
        self._queue: Queue[S] = PriorityQueue()
        self._costs: dict[S, float] = {}

    def _states_to_explore(self) -> Iterator[S]:
        while not self._queue.empty():
            yield self._queue.get_nowait()

    def _mark_as_state_to_explore(self, state: S) -> None:
        self._queue.put_nowait(state)

    def _after_state_explored(self, state: S) -> None:
        self.visited_states.add(state)

    def _should_visit_state(self, state: S) -> bool:
        old_cost = self._costs.get(state)
        if old_cost and state.cost >= old_cost:
            # We've reached the state earlier in a more efficient way.
            return False

        # Most efficient route to this state so far: keep track of its cost.
        self._costs[state] = state.cost
        return True


class State[C, V: Hashable](Hashable, ABC):
    path_finder_cls: ClassVar[type[ShortestPath]]
    c: C
    v: V

    cost: int
    previous: Self | None

    def __init__(
        self, variables: V, *, previous_state: Self = None, cost: int = 0
    ) -> None:
        self.v = variables
        self.previous = previous_state
        self.cost = cost

    @property
    @abstractmethod
    def is_end_state(self) -> bool:
        """
        Returns true if this state is at the end of the path.

        To be implemented for each specific use case.
        """

    @property
    @abstractmethod
    def next_states(self) -> Iterator[Self]:
        """
        Iterates the states reachable from this state.

        To be implemented for each specific use case.
        """

    @property
    def previous_states(self) -> Iterator[Self]:
        state: Self | None = self
        while state:
            yield state
            state = state.previous

    @classmethod
    def find_path(cls: type[Self], variables: V, constants: C) -> ShortestPath[Self]:
        cls.c = constants
        return cls(variables).find_path_from_current_state()

    def find_path_from_current_state(self) -> ShortestPath[Self]:
        return self.path_finder_cls(self).find()

    def move(self, variables: V, *, distance: int = 1) -> Self:
        return self.__class__(variables, previous_state=self, cost=self.cost + distance)

    def __hash__(self) -> int:
        return hash(self.v)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.v == other.v
            # Not sure why comparing the hashes doesn't work
            # for some cases: return hash(self) == hash(other)
        return NotImplemented


class BFSState[C, V: Hashable](State[C, V], ABC):
    path_finder_cls = ShortestPathBFS


@total_ordering
class DijkstraState[C, V: Hashable](State[C, V], ABC):
    path_finder_cls = ShortestPathDijkstra

    def __lt__(self, other: object) -> bool:
        # States with a lower cost will have priority in the queue.
        if isinstance(other, DijkstraState):
            return self.cost < other.cost
        return NotImplemented


class AStarState[C, V: Hashable](DijkstraState[C, V], ABC):
    def __lt__(self, other: object) -> bool:
        # States with a lower score (cost + heuristic) will have priority in the queue.
        if isinstance(other, AStarState):
            return self.score < other.score
        return NotImplemented

    @cached_property
    def score(self) -> int:
        return self.cost + self.heuristic

    @property
    @abstractmethod
    def heuristic(self) -> int:
        """Basically turns the Dijkstra algo into A*."""
