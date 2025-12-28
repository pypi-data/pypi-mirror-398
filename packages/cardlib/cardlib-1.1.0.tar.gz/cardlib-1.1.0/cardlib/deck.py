from __future__ import annotations
from collections.abc import Iterable
from collections import deque
import random
import copy

from .card import Card, Suit, Rank, PlayingCard

# Default rank-to-value mapping
DEFAULT_RANK_VALUES = {
	Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5, Rank.SIX: 6,
	Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9, Rank.TEN: 10,
	Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14, 
	Rank.JOKER: 15
}

# Default English alphabetical suit order
ENGLISH_ALPH_ORDER = (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES, Suit.BLACK, Suit.RED)

# Ranks from A-K
UP_RANKS = [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, 
			Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING]


# === Custom Errors ===
def _format_type(card_type):
	"""Helper to convert CARD_TYPE (type or tuple) into a clean string."""
	if isinstance(card_type, type):
		return card_type.__name__
	return ', '.join(t.__name__ for t in card_type)

class InvalidCardTypeError(TypeError):
	"""Unsupported card type is added to a Deck."""
	
	def __init__(self, invalid_card: Card, deck: Deck):
		deck_class = type(deck)
		expected_str = _format_type(deck.CARD_TYPE)

		message = (
			f'{deck_class.__name__} | '
			f'Expected: {expected_str} | '
			f'Got: {type(invalid_card).__name__}'
		)
		super().__init__(message)

class DeckMergeError(TypeError):
	"""
	Deck `B` cannot be merged into deck `A` because
	its allowed card types (CARD_TYPE) are not a
	subset of deck `A`'s.
	"""

	def __init__(self, deck_a: Deck, deck_b: Deck):
		a_types_str = _format_type(deck_a.CARD_TYPE)
		b_types_str = _format_type(deck_b.CARD_TYPE)

		message = (
			f'cannot merge {type(deck_b).__name__} into {type(deck_a).__name__}: '
			f'expected a subset of [{a_types_str}], got [{b_types_str}]'
		)
		super().__init__(message)


# === Base Deck ===
class Deck:
	"""
	Represents a deck of cards.

	- Top card = `deck[0]`
	- Internally uses deque
	- O(1) draw, and add to top/bottom
	"""

	CARD_TYPE: type | tuple[type, ...] = Card # Subclasses may override to restrict deck contents.
	"""
	Types of cards allowed in this deck.  
	Can be a type or tuple of types.
	"""

	def __init__(self,
		*,
		shuffle=True,
		empty=False
	):
		"""
		Initialize a new Deck of cards.

		Parameters:
			shuffle (bool): If True, the deck is shuffled immediately after creation. Default True.  
				If False, cards remain in **New Deck Order:**  
				`Hearts (A-K), Clubs (A-K), Diamonds (K-A), Spades (K-A), (bottom)`
			empty (bool): If True, the deck is not initialized with any cards.

		"""
		# Add cards to deck
		self._cards = deque() if empty else self._build_deck()
		if shuffle:
			self.shuffle()

	def _build_deck(self):
		"""
		Returns cards in a starting order stored in a `deque` object.

		This determines the *original state* of the deck for `reset()`.
		"""
		return deque() # empty by default

	@classmethod
	def from_cards(cls,
		cards,
		*,
		shuffle=False,
		_no_copy=False,
		**kwargs # any future keyword arguments
	):
		"""
		Create a deck from an existing list of cards.

		Parameters:
			cards: iterable of card instances (top-bottom)
			shuffle (bool): Whether to shuffle after creation
			_no_copy (bool): INTERNAL FLAG: skip making a copy of the deque container (for performance)
		"""
		deck = cls(empty=True, **kwargs)
		# Reference the same deque object, assuming caller guarantees safety
		if _no_copy:
			deck._cards = cards
		else:
			deck._cards.extend(cards)
		if shuffle:
			deck.shuffle()
		return deck
	
	def _empty_clone(self):
		"""
		Returns a new deck with the same attributes as this one, without `_cards`.

		Uses `__dict__` to copy ALL other instance attributes automatically.

		This method is used internally whenever a deck is created from `self`  
		(i.e., `copy()`, `split()`, deck arithmetic).

		---

		Subclasses that add mutable attributes (like lists) should  
		override this to ensure they are copied or not included in the clone:

			clone = super()._empty_clone()  
			clone.list = clone.list.copy() # make sure container is copied  
			del clone.list # alternatively, exclude its existence  
			return clone
		"""
		clone = type(self).__new__(type(self)) # uninitialized Deck
		clone.__dict__.update(self.__dict__)
		del clone._cards
		# Here, subclasses would delete mutable attr or make copies if expected
		return clone
	
	def copy(self, *, deep=False):
		"""
		Returns a new Deck object that copies this one.
		
		Parameters:
			deep (bool): If True, also clones each card object.  
				If False, cards are shared by reference (default).
		"""
		# Always make a new card container (deque); optionally make copies of the cards.
		new_cards = copy.deepcopy(self._cards) if deep else deque(self._cards)
		deck = self._empty_clone()
		deck._cards = new_cards
		return deck
	
	def __repr__(self):
		name = type(self).__name__
		return f"{name}({len(self._cards)} card{'s' if len(self._cards) != 1 else ''})"
	
	def __str__(self):
		return repr(self)
	

	# --- Deck operations ---
	def shuffle(self):
		"""Shuffle deck in place."""
		cards = list(self._cards) # temp list
		random.shuffle(cards)
		self._cards = deque(cards)

	def reset(self, *, shuffle=True):
		"""Rebuild deck to its original state."""
		self._cards = self._build_deck()
		if shuffle:
			self.shuffle()

	def show(self, *args, step=1, cards=None, sep=', '):
		"""
		show() → Print all cards.  
		show(stop) → Print cards from index 0 up to stop.  
		show(start, stop[, step]) → Print cards using list-slicing rules.

		Parameters:
			cards: iterable of Card, or None to show the deck's own cards.
			sep (str): separator string between cards.
		"""
		start = None
		stop = None

		if len(args) == 1:
			stop = args[0]
		elif len(args) == 2:
			start = args[0]
			stop = args[1]
		elif len(args) == 3:
			start = args[0]
			stop = args[1]
			step = args[2]
		elif len(args) > 3:
			raise TypeError(f'show() expected 1-3 arguments, got {len(args)}')

		cards = self._cards if cards is None else cards
		cards_to_show = list(cards)[start:stop:step]
		output = sep.join(map(str, cards_to_show)) or '(empty)'
		print(output)

	def draw(self, n=1, /, *, strict=True):
		"""
		Draw `n` cards from the top of the deck and remove them.
		
		- If strict and fewer than n cards remain, ValueError is raised.
		- Always returns a list (possibly shorter than n if not strict).
		"""
		if n < 0:
			raise ValueError('cannot draw a negative number of cards')
		if strict and n > len(self._cards):
			raise ValueError('not enough cards left to draw')
		to_draw = min(n, len(self._cards))
		return [self._cards.popleft() for _ in range(to_draw)]
	
	def deal(self, num_hands, cards_each, /, *, strict=True):
		"""
		Deal cards from the top of the deck into multiple hands.
		
		Parameters:
			num_hands (int): Number of card groups (or players).
			cards_each (int): Number of cards per group.
			strict (bool): If True, raises ValueError if not enough cards remain.
		
		Returns:
			list[list[Card]]: A list of hands, each a list of card objects.
		"""
		if num_hands < 0 or cards_each < 0:
			raise ValueError('deal parameters cannot be negative')

		total = num_hands * cards_each
		if strict and total > len(self._cards):
			raise ValueError('not enough cards left to deal')
		
		hands = [[] for _ in range(num_hands)]
		for _ in range(cards_each):
			for hand in hands:
				if not self._cards: # ran out of cards
					break
				hand.append(self._cards.popleft())
		return hands
	
	def split(self, n=2, *, strict=False):
		"""
		Split the deck into `n` sub-decks as evenly as possible using all cards.
		
		If strict=True, sub-decks will have an equal number of cards  
		(extras on bottom will be discarded).

		Returns:
			list[Deck]: A list of Decks cut from the top of this one (left-right).
		"""
		if n < 2:
			raise ValueError('n must be >= 2')
		if n > len(self._cards):
			raise ValueError('n cannot exceed deck size')
		
		total = len(self._cards)
		k = total // n # cards per group
		remainder = total % n # r groups will get 1 extra card

		result = []
		temp = deque(self._cards)

		for i in range(n):
			chunk_size = k if strict else k + (1 if i < remainder else 0)
			sub_deck = self._empty_clone()
			sub_deck._cards = deque(temp.popleft() for _ in range(chunk_size))
			result.append(sub_deck)
		return result
	

	# --- Container magic ---
	def __len__(self):
		return len(self._cards)
	
	def __getitem__(self, i):
		"""Returns the card or list of cards at index/slice."""
		if isinstance(i, slice):
			return list(self._cards)[i]
		return self._cards[i]
	
	def __setitem__(self, i, card):
		"""Assign card(s) to index/slice. Checks type before assignment."""
		if isinstance(i, slice):
			if not isinstance(card, Iterable):
				raise TypeError('must assign iterable of cards to a slice')
			
			# Check the type of every card in the iterable
			for c in card:
				if not isinstance(c, self.CARD_TYPE):
					raise InvalidCardTypeError(c, self)
		
		else: # If not a slice, assume single index
			if not isinstance(card, self.CARD_TYPE):
				raise InvalidCardTypeError(card, self)
		
		# Perform the assignment
		temp = list(self._cards)
		temp[i] = card
		self._cards = deque(temp)

	def __delitem__(self, i):
		temp = list(self._cards)
		del temp[i]
		self._cards = deque(temp)
	
	def __iter__(self):
		return iter(self._cards) # top to bottom


	# --- Container methods ---
	def clear(self):
		"""Remove all cards from deck."""
		self._cards.clear()

	def reverse(self):
		"""Reverse *IN PLACE*."""
		self._cards.reverse()

	def pop(self, index=0, /):
		"""
		Remove and return card at index (default 0).  
		O(n) for arbitrary index.
		"""
		if index == 0:
			return self._cards.popleft()
		elif index == -1:
			return self._cards.pop()
		else:
			temp = list(self._cards)
			card = temp.pop(index)
			self._cards = deque(temp)
			return card
	
	def insert(self, index, card, /):
		"""Insert card before index (top of deck = 0)."""
		if not isinstance(card, self.CARD_TYPE):
			raise InvalidCardTypeError(card, self)
		temp = list(self._cards)
		temp.insert(index, card)
		self._cards = deque(temp)

	def add(self, *cards, position='bottom'):
		"""
		Adds one or more cards or groups of cards to the deck.

		Items passed in `*cards` are added one-by-one, preserving the internal
		order of any card groups (iterables). The insertion behavior is
		determined by `position`.

		Parameters:
			cards: Card instances or iterables of cards to be added.
			position (str): Where to insert the cards: 'top' (index 0), 
				'bottom' (end), or 'random'.
				
		- The last item in `*cards` is placed last.
		"""
		flat_cards = []
		for item in cards:
			if isinstance(item, self.CARD_TYPE):
				flat_cards.append(item)
			elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
				for c in (reversed(item) if position=='top' else item):
					if not isinstance(c, self.CARD_TYPE):
						raise InvalidCardTypeError(c, self)
					flat_cards.append(c)
			else:
				raise TypeError('must be Card or iterable of Cards')
		
		if position == 'top':
			self._cards.extendleft(flat_cards)
		elif position == 'bottom':
			self._cards.extend(flat_cards)
		elif position == 'random':
			temp = list(self._cards)
			for c in flat_cards:
				temp.insert(random.randint(0, len(temp)), c)
			self._cards = deque(temp)
		else:
			raise ValueError("position must be 'top', 'bottom', or 'random'")

	def remove(self, card, /):
		"""
		Remove the first occurrence of a card from the deck.
		
		Raises ValueError if the card is not found.
		"""
		self._cards.remove(card)
	
	def index(self, card, start=0, stop=None, /):
		"""
		Returns the first index of a card (from top-bottom).

		Raises ValueError if the card is not found.
		"""
		if stop is None:
			stop = len(self._cards)
		return self._cards.index(card, start, stop)

	def filter(self, predicate, /):
		"""
		Keep only cards where `predicate(card)` is True.
		
		Example (keep cards with a value above 7):

			deck.filter(lambda c: deck.value(c) > 7)
		"""
		self._cards = deque(c for c in self._cards if predicate(c))

	def remove_if(self, predicate, /):
		"""Remove all cards where `predicate(card)` is True."""
		self._cards = deque(c for c in self._cards if not predicate(c))

	def count(self, target, /):
		"""
		Returns number of cards matching a given condition or specific card.

		Parameters:
			target:
				- Card: counts occurrences of a specific card.
				- Callable: counts how many cards satisfy the predicate.
		"""
		if callable(target):
			return sum(1 for c in self._cards if target(c))
		return self._cards.count(target)


	# --- Deck arithmetic ---
	def _merge_compatible(self, other: Deck) -> bool:
		"""Check if `other.CARD_TYPE` is a subset of `self.CARD_TYPE`."""
		my_set = {self.CARD_TYPE} if isinstance(self.CARD_TYPE, type) else set(self.CARD_TYPE)
		other_set = {other.CARD_TYPE} if isinstance(other.CARD_TYPE, type) else set(other.CARD_TYPE)
		return other_set.issubset(my_set)

	def __add__(self, other):
		"""
		Returns a new deck with the same cards/rules as the first deck,  
		followed by the cards of a second deck.

		Cards are referenced (not copied).
		"""
		if not isinstance(other, Deck):
			return NotImplemented
		if not self._merge_compatible(other):
			raise DeckMergeError(self, other)
		new = self.copy()
		new._cards.extend(other._cards)
		return new

	def __iadd__(self, other):
		"""Add cards from another deck to the bottom of this one."""
		if not isinstance(other, Deck):
			return NotImplemented
		if not self._merge_compatible(other):
			raise DeckMergeError(self, other)
		self._cards.extend(other._cards)
		return self
	
	def __sub__(self, other):
		"""
		Returns a new deck with certain cards removed.
		
		`other` can be:
			- a single card
			- an iterable of cards
			- another Deck
		"""
		if isinstance(other, Card):
			to_remove = {other}
		elif isinstance(other, Deck):
			to_remove = set(other._cards)
		elif isinstance(other, Iterable) and not isinstance(other, (str, bytes)):
			to_remove = set(other)
		else:
			return NotImplemented
		
		new_deck = self._empty_clone()
		new_deck._cards = deque(c for c in self._cards if c not in to_remove)
		return new_deck
	
	def __isub__(self, other):
		"""Remove specified cards from this deck."""
		if isinstance(other, Card):
			to_remove = {other}
		elif isinstance(other, Deck):
			to_remove = set(other._cards)
		elif isinstance(other, Iterable) and not isinstance(other, (str, bytes)):
			to_remove = set(other)
		else:
			return NotImplemented
		
		self._cards = deque(c for c in self._cards if c not in to_remove)
		return self
	
	def __mul__(self, n):
		"""Returns a new deck repeated `n` times (cards are referenced, not copied)."""
		if not isinstance(n, int):
			return NotImplemented
		if n < 1:
			raise ValueError('Deck multiplication requires a positive int')
		new_deck = self._empty_clone()
		new_deck._cards = self._cards * n # produces a new deque object
		return new_deck
	
	__rmul__ = __mul__
	
	def __imul__(self, n):
		"""Repeat this deck's cards `n` times."""
		if not isinstance(n, int):
			return NotImplemented
		if n < 1:
			raise ValueError('Deck multiplication requires a positive int')
		self._cards *= n
		return self
	
	def __truediv__(self, n):
		"""
		Loosely split into `n` decks, distributing all cards
		
		Equivalent to `deck.split(n, strict=False)`
		"""
		return self.split(n, strict=False)
	
	def __floordiv__(self, n):
		"""
		Strictly split into `n` evenly sized decks (discarding extras)
		
		Equivalent to `deck.split(n, strict=True)`
		"""
		return self.split(n, strict=True)
	
	def __lshift__(self, n): # in-place
		"""Rotate the top `n` cards to the bottom (cut)."""
		self._cards.rotate(-n)
		return self

	def __rshift__(self, n):
		"""Rotate the bottom `n` cards to the top (reverse cut)."""
		self._cards.rotate(n)
		return self

	# --- Card comparison ---
	def value(self, card, /):
		"""Get numeric value of card according to deck rules."""
		return 0 # default
	
	def compare(self, card1, card2, /):
		"""
		Compare two cards using deck rules. Returns -1, 0, or 1.

		Uses `_cmp_key` by default.
		"""
		a, b = self._cmp_key(card1), self._cmp_key(card2)
		return (a > b) - (a < b)
	
	def _cmp_key(self, card, /):
		"""
		Return a comparison key for a card.

		Used internally by deck sorting and comparison methods.
		Subclasses should override this to define ordering rules.

		Returns:
		 	A comparable object (e.g., int, tuple, str) representing the card's sort value.
		"""
		return 0 # All cards are equal by default
	
	def sort_cards(self, cards, /, *, descending=False):
		"""Sort a list of cards using this deck's `_cmp_key`."""
		cards.sort(key=self._cmp_key, reverse=descending)
	
	def sort(self, *, descending=False):
		"""Sort deck in ascending order using `_cmp_key`."""
		temp = list(self._cards)
		temp.sort(key=self._cmp_key, reverse=descending)
		self._cards = deque(temp)


# === Concrete Deck ===
class PlayingCardDeck(Deck):
	"""
	Represents a standard 52-card deck of playing cards.

	- Optionally include jokers
	- Top card = `deck[0]`
	- Internally uses deque
	- O(1) draw, and add to top/bottom
	"""
	
	CARD_TYPE = PlayingCard

	def __init__(self,
		*,
		include_jokers=False,
		rank_values=None,
		suit_order=ENGLISH_ALPH_ORDER,
		shuffle=True,
		empty=False
	):
		"""
		Initialize a new deck of cards.

		Parameters:
			include_jokers (bool): Include two jokers (red and black) if True. Default False.
			rank_values (dict): Optional mapping of ranks (str) to numeric values. Defaults to standard `2-A + JOKER`.
			suit_order (tuple or None): Ascending order of suits for comparison. None means suits are equal. Default `ENGLISH_ALPH_ORDER`.
			shuffle (bool): If True, the deck is shuffled immediately after creation. Default True.  
				If False, cards remain in **New Deck Order**:  
				Hearts (A-K), Clubs (A-K), Diamonds (K-A), Spades (K-A), (bottom)
			empty (bool): If True, the deck is not initialized with any cards.
		"""

		# Shared rules for this deck
		self.rank_values = rank_values or DEFAULT_RANK_VALUES
		"""Dictionary mapping Ranks to their scores (int)."""
		self.suit_order = suit_order
		"""Ascending order of Suits or None."""
		self.include_jokers = include_jokers

		# Fast access to suit order values
		self._suit_index = {s: i for i, s in enumerate(self.suit_order)} if self.suit_order else {}
		"""Map suits to their indices in the ordering."""

		# Add cards in new deck order
		super().__init__(shuffle=shuffle, empty=empty)

	def _build_deck(self):
		"""
		Returns cards in: **New Deck Order**:

			Hearts (A-K), Clubs (A-K), Diamonds (K-A), Spades (K-A), (bottom)
		"""
		cards = deque()
		# Hearts & Clubs: A-K
		for suit in (Suit.HEARTS, Suit.CLUBS):
			for rank in UP_RANKS:
				cards.append(PlayingCard(rank, suit))
		# Diamonds & Spades: K-A
		for suit in (Suit.DIAMONDS, Suit.SPADES):
			for rank in reversed(UP_RANKS):
				cards.append(PlayingCard(rank, suit))
		if self.include_jokers:
			cards.append(PlayingCard(Rank.JOKER, Suit.BLACK))
			cards.append(PlayingCard(Rank.JOKER, Suit.RED))
		return cards

	@classmethod
	def from_cards(cls,
		cards,
		*,
		include_jokers=False,
		rank_values=None,
		suit_order=ENGLISH_ALPH_ORDER,
		shuffle=False,
		_no_copy=False
	):
		"""
		Create a deck from an existing list of cards.

		Parameters:
			cards: iterable of card instances (top-bottom)
			include_jokers (bool):
			rank_values (dict):
			suit_order (tuple or None):
			shuffle (bool): Whether to shuffle after creation
			_no_copy (bool): INTERNAL FLAG: skip making a copy of the deque container (for performance)
		"""
		super().from_cards(cards, 
			include_jokers=include_jokers,
			rank_values=rank_values,
			suit_order=suit_order,
			shuffle=shuffle,
			_no_copy=_no_copy)

	# --- Container methods ---
	def remove_if(self, predicate, /):
		"""
		Remove all cards matching a condition.
		
		Example (remove all hearts): 
			`deck.remove_if(lambda c: c.suit == Suit.HEARTS)`
		"""
		return super().remove_if(predicate)

	def count(self, target, /):
		"""
		Returns number of cards matching a given condition or specific card.

		Parameters:
			target:
				- Card: counts occurrences of a specific card.
				- Callable: counts how many cards satisfy the predicate.

		## Usage:

			deck.count(StandardPlayingCards.ACE_SPADES)  
			deck.count(lambda c: c.is_red)
		"""
		return super().count(target)


	# --- Deck arithmetic ---
	def __sub__(self, other):
		"""
		Returns a new deck with certain cards removed.
		
		`other` can be:
			- a single card
			- a Rank
			- a Suit
			- an iterable of any of the above
			- another Deck
		"""
		if isinstance(other, (Card, Rank, Suit)):
			to_remove = {other}
		elif isinstance(other, Deck):
			to_remove = set(other._cards)
		elif isinstance(other, Iterable) and not isinstance(other, (str, bytes)):
			to_remove = set(other)
		else:
			return NotImplemented
		
		new_cards = deque(c for c in self._cards if 
					c not in to_remove and c.suit not in to_remove and c.rank not in to_remove)
		return Deck.from_cards(
			new_cards, # container already created
			include_jokers=self.include_jokers,
			rank_values=self.rank_values,
			suit_order=self.suit_order,
			shuffle=False,
			_no_copy=True
		)
	
	def __isub__(self, other):
		"""Remove certain cards, suits, or ranks from this deck."""
		if isinstance(other, (Card, Rank, Suit)):
			to_remove = {other}
		elif isinstance(other, Deck):
			to_remove = set(other._cards)
		elif isinstance(other, Iterable) and not isinstance(other, (str, bytes)):
			to_remove = set(other)
		else:
			return NotImplemented
		
		self._cards = deque(c for c in self._cards if 
					c not in to_remove and c.suit not in to_remove and c.rank not in to_remove)
		return self
	

	# --- Card comparison ---
	def value(self, card, /):
		"""Get numeric value of card according to deck rules."""
		return self.rank_values.get(card.rank, 0)
	
	def _cmp_key(self, card, /):
		"""
		Returns a tuple key suitable for sorting: (rank_value, suit_index).
		
		Unknown suits get -1. If suits are unordered, suit_index is 0.
		"""
		rank_val = self.value(card)
		suit_index = 0
		if self.suit_order:
			suit_index = self._suit_index.get(card.suit, -1)
		return (rank_val, suit_index)
	
	def sort_cards(self, cards, /, *, descending=False):
		"""Sort a list of cards according to rank/suit."""
		return super().sort_cards(cards, descending=descending)
	
	def sort(self, *, descending=False):
		"""Sort deck in ascending order according to rank/suit."""
		return super().sort(descending=descending)
