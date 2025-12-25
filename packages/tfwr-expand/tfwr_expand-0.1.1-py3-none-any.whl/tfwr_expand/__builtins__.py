from __future__ import annotations
import builtins
from enum import Enum
from typing import AbstractSet, Any, Iterable, Iterator, overload, Self, SupportsIndex, Tuple

# TODO: Complete comments.

# Keywords:
#   +, -, *, /, //, %, **,
#   ==, !=, <=, >=, <, >,
#   not, and, or,
#   True, False, None,
#   import, from,
#   def, ..., return,
#   global,
#   if, elif, else, while, for, continue, break,
#   __name__
#
# single-line string only:
#   'str' is ok.
#   """str""" is unsupported.

"""
@category: `builtin_funcions`.
@description: Computes the absolute value of a `number`.
@parameter number: The number.
@returns: `number` if number is positive, `-number` otherwise.
@ticks: 1.
@unlock: `Unlocks.?`
"""
abs = builtins.abs
len = builtins.len
min = builtins.min
max = builtins.max

range = builtins.range
str = builtins.str


class list:
	def __init__(self, iterable: (Iterable[Any] | list | None)=None, /) -> None: ...

	def append(self, object: Any, /) -> None: ...
	def pop(self, index: SupportsIndex = -1, /) -> Any: ...
	def insert(self, index: SupportsIndex, object: Any, /) -> None: ...
	def remove(self, value: Any, /) -> None: ...

	def __len__(self) -> builtins.int: ...
	def __iter__(self) -> Iterable[Any]: ...
	@overload
	def __getitem__(self, i: SupportsIndex, /) -> Any: ...
	@overload
	def __getitem__(self, s: builtins.slice, /) -> builtins.list: ...
	@overload
	def __setitem__(self, key: SupportsIndex, value: Any, /) -> None: ...
	@overload
	def __setitem__(self, key: builtins.slice, value: Iterable[Any], /) -> None: ...
	def __add__(self, value: (builtins.list | list), /) -> builtins.list: ...
	def __iadd__(self, value: (Iterable[Any] | list), /) -> builtins.list: ...  # Returns `Self` originally.
	def __mul__(self, value: SupportsIndex, /) -> builtins.list: ...
	def __rmul__(self, value: SupportsIndex, /) -> builtins.list: ...
	def __imul__(self, value: SupportsIndex, /) -> builtins.list: ...  # Returns `Self` originally.
	def __contains__(self, key: Any, /) -> builtins.bool: ...
	def __gt__(self, value: (builtins.list | list), /) -> builtins.bool: ...
	def __ge__(self, value: (builtins.list | list), /) -> builtins.bool: ...
	def __lt__(self, value: (builtins.list | list), /) -> builtins.bool: ...
	def __le__(self, value: (builtins.list | list), /) -> builtins.bool: ...
	def __eq__(self, value: Any, /) -> builtins.bool: ...


class dict:
	def __init__(self, iterable: (Iterable[Tuple[Any, Any]] | dict | None)=None, /) -> None: ...

	def pop(self, key: Any, default: Any=None, /) -> Any: ...

	def __len__(self) -> builtins.int: ...
	def __getitem__(self, key: Any, /) -> Any: ...
	def __setitem__(self, key: Any, value: Any, /) -> None: ...
	def __iter__(self) -> Iterator[Tuple[Any, Any]]: ...
	def __eq__(self, value: Any, /) -> builtins.bool: ...
	def __ror__(self, value: (builtins.dict | dict), /) -> builtins.dict: ...
	def __ior__(self, value: (Iterable[Tuple[Any, Any]] | dict), /) -> builtins.dict: ...  # Returns `Self` originally.


# TODO: Does it works in the game?
class set:
	def __init__(self, iterable: (Iterable[Any] | set) | None=None, /) -> None: ...

	def add(self, element: Any, /) -> None: ...
	def remove(self, element: Any, /) -> None: ...
	
	def __len__(self) -> builtins.int: ...
	def __contains__(self, o: Any, /) -> builtins.bool: ...
	def __iter__(self) -> Iterator[Any]: ...
	def __and__(self, value: (AbstractSet | set), /) -> builtins.set: ...
	def __iand__(self, value: (AbstractSet | set), /) -> builtins.set: ...  # Returns `Self` originally.
	def __or__(self, value: (AbstractSet | set), /) -> builtins.set: ...
	def __ior__(self, value: (AbstractSet | set), /) -> builtins.set: ...  # Returns `Self` originally.
	def __sub__(self, value: (AbstractSet | set), /) -> builtins.set: ...
	def __isub__(self, value: (AbstractSet | set), /) -> builtins.set: ...  # Returns `Self` originally.
	def __xor__(self, value: (AbstractSet | set), /) -> builtins.set: ...
	def __ixor__(self, value: (AbstractSet | set), /) -> builtins.set: ...  # Returns `Self` originally.
	def __le__(self, value: (AbstractSet | set), /) -> builtins.bool: ...
	def __lt__(self, value: (AbstractSet | set), /) -> builtins.bool: ...
	def __ge__(self, value: (AbstractSet | set), /) -> builtins.bool: ...
	def __gt__(self, value: (AbstractSet | set), /) -> builtins.bool: ...
	def __eq__(self, value: Any, /) -> builtins.bool: ...

Direction = builtins.str
DroneHandler = builtins.int

South = 'south'
East = 'east'
North = 'north'
West = 'west'


class Entities(Enum):
	Apple = 'apple'
	Bush = 'bush'
	Cactus = 'cactus'
	Carrot = 'carrot'
	Dead_Pumpkin = 'dead_pumpkin'
	Dinosaur = 'dinosaur'
	Grass = 'grass'
	Hedge = 'hedge'
	Pumpkin = 'pumpkin'
	Sunflower = 'sunflower'
	Treasure = 'treasure'
	Tree = 'tree'


class Grounds(Enum):
	Grassland = 'grassland'
	Soil = 'soil'


class Hats(Enum):
	Brown_Hat = 'brown_hat'
	Cactus_Hat = 'cactus_hat'
	Carrot_Hat = 'carrot_hat'
	Dinosaur_Hat = 'dinosaur_hat'
	Gold_Hat = 'gold_hat'
	Gold_Trophy_Hat = 'gold_trophy_hat'
	Golden_Cactus_Hat = 'golden_cactus_hat'
	Golden_Carrot_Hat = 'golden_carrot_hat'
	Golden_Gold_Hat = 'golden_gold_hat'
	Golden_Pumpkin_Hat = 'golden_pumpkin_hat'
	Golden_Sunflower_Hat = 'golden_sunflower_hat'
	Golden_Tree_Hat = 'golden_tree_hat'
	Gray_Hat = 'gray_hat'
	Green_Hat = 'green_hat'
	Pumpkin_Hat = 'pumpkin_hat'
	Purple_Hat = 'purple_hat'
	Silver_Trophy_Hat = 'silver_trophy_hat'
	Straw_Hat = 'straw_hat'
	Sunflower_Hat = 'sunflower_hat'
	The_Farmers_Remains = 'the_farmers_remains'
	Top_Hat = 'top_hat'
	Traffic_Cone = 'traffic_cone'
	Traffic_Cone_Stack = 'traffic_cone_stack'
	Tree_Hat = 'tree_hat'
	Wizard_Hat = 'wizard_hat'
	Wood_Trophy_Hat = 'wood_trophy_hat'


class Items(Enum):
	Bone = 'bone'
	Cactus = 'cactus'
	Carrot = 'carrot'
	Fertilizer = 'fertilizer'
	Gold = 'gold'
	Hay = 'hay'
	Power = 'power'
	Pumpkin = 'pumpkin'
	Water = 'water'
	Weird_substance = 'weird_substance'
	Wood = 'wood'


class Leaderboards(Enum):
	Cactus = 'cactus'
	Cactus_Single = 'cactus_single'
	Carrots = 'carrots'
	Carrots_Single = 'carrots_single'
	Dinosaur = 'dinosaur'
	Fastest_Reset = 'fastest_reset'
	Hay = 'hay'
	Hay_Single = 'hay_single'
	Maze = 'maze'
	Maze_Single = 'maze_single'
	Pumpkins = 'pumpkins'
	Pumpkins_Single = 'pumpkins_single'
	Sunflowers = 'sunflowers'
	Sunflowers_Single = 'sunflowers_single'
	Wood = 'wood'
	Wood_Single = 'wood_single'


class Unlocks(Enum):
	Auto_Unlock = 'auto_unlock'
	Cactus = 'cactus'
	Carrots = 'carrots'
	Costs = 'costs'
	Debug = 'debug'
	Debug_2 = 'debug_2'
	Dictionaries = 'dictionaries'
	Dinosaurs = 'dinosaurs'
	Expand = 'expand'
	Fertilizer = 'fertilizer'
	Functions = 'functions'
	Grass = 'grass'
	Hats = 'hats'
	Import = 'import'
	Leaderboard = 'leaderboard'
	Lists = 'lists'
	Loops = 'loops'
	Mazes = 'mazes'
	Megafarm = 'megafarm'
	Operators = 'operators'
	Plant = 'plant'
	Polyculture = 'polyculture'
	Pumpkins = 'pumpkins'
	Senses = 'senses'
	Simulation = 'simulation'
	Speed = 'speed'
	Sunflowers = 'sunflowers'
	The_Farmers_Remains = 'the_farmers_remains'
	Timing = 'timing'
	Top_Hat = 'top_hat'
	Trees = 'trees'
	Utilities = 'utilities'
	Variables = 'variables'
	Watering = 'watering'


def can_harvest() -> builtins.bool:
	"""
	@category: `builtin_funcions`.
	@description: Used to find out if plants are fully grown.
	@returns: `True` if there is an entity under the drone is ready to be harvested.
			  `False` otherwise.
	@ticks: 1.
	@unlock: `Unlocks.?`
	@see_also: `Unlocks.Speed`
	"""
	...


def can_move(direction: Direction) -> builtins.bool:
	...


def change_hat(hat: Hats) -> None:
	...


def clear() -> None:
	...


def do_a_flip() -> None:
	...


def get_companion() -> Tuple[
	(Entities.Bush | Entities.Grass | Entities.Tree | Entities.Carrot),
	Tuple[builtins.int, builtins.int]
] | None:
	...


def get_cost(
	q: Entities | Unlocks,
	level: builtins.int | None=None
) -> builtins.dict[Items, builtins.int | None]:
	...


def get_entity_type() -> Entities | None:
	...


def get_ground_type() -> Grounds:
	...


def get_pos_x() -> builtins.int:
	...


def get_pos_y() -> builtins.int:
	...


def get_tick_count() -> builtins.int:
	...


def get_time() -> builtins.int:
	...


def get_water() -> builtins.float:
	...


def get_world_size() -> builtins.int:
	...


def harvest() -> builtins.bool:
	...


def has_finished(drone_handler: DroneHandler) -> builtins.bool:
	...


def leaderboard_run(
	leaderboard: Leaderboards,
	file_name: builtins.str,
	speedup: builtins.float
) -> None:
	...


def max_drones() -> builtins.int:
	...


# should use `float` instead of `int` for return type?
def measure(
	direction: Direction | None=None
) -> builtins.int | Tuple[builtins.int, builtins.int | None]:
	...


def move(direction: Direction) -> builtins.bool:
	...


def num_drones() -> builtins.int:
	...


def num_items(item: Items) -> builtins.float:
	...


def num_unlocked(_unlock: Unlocks | Entities | Grounds | Items | Hats) -> builtins.int:
	...


def pet_the_piggy() -> None:
	...


def plant(entity: Entities) -> None:
	...


def print(*_obj: Any) -> None:
	...


def quick_print(*_obj: Any) -> None:
	...


def random() -> builtins.float:
	...


def set_execution_speed(speed: builtins.float) -> None:
	...


def set_world_size(size: builtins.float) -> None:
	...


def simulate(
	filename: builtins.str,
	sim_unlocks: (builtins.dict[Unlocks, int] | dict) | Iterable[Unlocks] | Unlocks,
	sim_items: (builtins.dict[Items, float] | dict),
	sim_globals: (builtins.dict[str, Any] | dict),
	seed: builtins.int,
	speedup: builtins.float
) -> builtins.float:
	...


def spawn_drone() -> DroneHandler | None:
	...


def swap(direction: Direction) -> builtins.bool:
	...


def till() -> None:
	...


def unlock(_unlock: Unlocks) -> builtins.bool:
	...


def use_item(item: Items, n: builtins.int=1) -> None:
	...


def wait_for(drone_handler: DroneHandler) -> Any:
	...
