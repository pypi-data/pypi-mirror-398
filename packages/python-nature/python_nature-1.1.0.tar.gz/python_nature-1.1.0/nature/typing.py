from typing import Annotated, TypeAlias
from numpy.typing import NDArray
from queue import Queue


QueueType = Queue
NodeArray = Annotated[NDArray, "ExpressionNode"]
SpeciesArray = Annotated[NDArray, "Species"]
