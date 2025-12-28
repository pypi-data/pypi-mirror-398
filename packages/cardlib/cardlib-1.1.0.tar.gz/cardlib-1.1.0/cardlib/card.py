from abc import ABC, abstractmethod
from enum import Enum

# === ENUMS ===
class Suit(Enum):
	SPADES = '♠' # Unicode symbols for nice display
	HEARTS = '♥'
	DIAMONDS = '♦'
	CLUBS = '♣'
	RED = 'Red'
	BLACK = 'Black'

class Rank(Enum):
	TWO = '2'
	THREE = '3'
	FOUR = '4'
	FIVE = '5'
	SIX = '6'
	SEVEN = '7'
	EIGHT = '8'
	NINE = '9'
	TEN = '10'
	JACK = 'J'
	QUEEN = 'Q'
	KING = 'K'
	ACE = 'A'
	JOKER = 'JOKER'


# === Abstract Base ===
class Card(ABC):
	"""Abstract card type. Supports both mutable and immutable card models."""

	def __new__(cls, *args, **kwargs):
		if cls is Card:
			raise TypeError("Cannot instantiate abstract base class 'Card'")
		return super().__new__(cls)
	
	def __repr__(self):
		return f'{self.__class__.__name__}(...)' # default fallback
	
	@abstractmethod
	def __str__(self) -> str:
		pass


# === Concrete Cards ===
class SimpleCard(Card):
	"""
	A lightweight, immutable Card for rank/suit-like data.
	
	- Accepts any values for `rank` and `suit`.
	- No type checks — use at your own risk.
	- Perfect for prototyping, custom games, or quick two-field cards.
	"""
	
	__slots__ = ('_rank', '_suit')

	@property
	def rank(self): return self._rank
	@property
	def suit(self): return self._suit

	def __init__(self, rank, suit):
		self._rank = rank
		self._suit = suit

	def __repr__(self):
		return f'{self.__class__.__name__}({self.rank}, {self.suit})'

	def __str__(self):
		return f'{self.rank}{self.suit}'
	
	def __eq__(self, other):
		return (isinstance(other, SimpleCard) and 
				self.rank == other.rank and 
				self.suit == other.suit)
	
	def __hash__(self):
		return hash((self.rank, self.suit))


class PlayingCard(SimpleCard):
	"""
	Represents an immutable standard playing card using `Rank` and `Suit` enums.

	- Part of a 52-card deck (+2 jokers).
	- Value and comparison depend on `Deck` rules.
	- Use `StandardPlayingCards.ACE_SPADES` for predefined constants.
	"""

	__slots__ = ()

	def __init__(self, rank: Rank, suit: Suit):
		if not isinstance(rank, Rank):
			raise TypeError(f'rank must be a Rank enum, got {type(rank)}')
		if not isinstance(suit, Suit):
			raise TypeError(f'suit must be a Suit enum, got {type(suit)}')
		self._rank = rank
		self._suit = suit

	@property
	def rank(self) -> Rank:
		return self._rank
	@property
	def suit(self) -> Suit:
		return self._suit
	
	@property
	def is_red(self):
		return self._suit in (Suit.HEARTS, Suit.DIAMONDS, Suit.RED)
	
	@property
	def is_black(self):
		return self._suit in (Suit.SPADES, Suit.CLUBS, Suit.BLACK)
	
	def __str__(self):
		return f'{self.rank.value}{self.suit.value}'
	
	# Inequality comparisons require a deck context
	def __lt__(self, other):
		if isinstance(other, PlayingCard):
			raise TypeError('PlayingCard instances do not support ordering; use Deck.compare(card1, card2) instead')
		return NotImplemented
	
	__le__ = __lt__
	__gt__ = __lt__
	__ge__ = __lt__
	

# === CONSTANTS ===
class StandardPlayingCards:
	"""
	Predefined PlayingCard instances for a standard deck (52 cards + 2 jokers).
	
	Use like:  `StandardPlayingCards.ACE_SPADES`
	"""

	# --- Spades ---
	ACE_SPADES = PlayingCard(Rank.ACE, Suit.SPADES)
	KING_SPADES = PlayingCard(Rank.KING, Suit.SPADES)
	QUEEN_SPADES = PlayingCard(Rank.QUEEN, Suit.SPADES)
	JACK_SPADES = PlayingCard(Rank.JACK, Suit.SPADES)
	TEN_SPADES = PlayingCard(Rank.TEN, Suit.SPADES)
	NINE_SPADES = PlayingCard(Rank.NINE, Suit.SPADES)
	EIGHT_SPADES = PlayingCard(Rank.EIGHT, Suit.SPADES)
	SEVEN_SPADES = PlayingCard(Rank.SEVEN, Suit.SPADES)
	SIX_SPADES = PlayingCard(Rank.SIX, Suit.SPADES)
	FIVE_SPADES = PlayingCard(Rank.FIVE, Suit.SPADES)
	FOUR_SPADES = PlayingCard(Rank.FOUR, Suit.SPADES)
	THREE_SPADES = PlayingCard(Rank.THREE, Suit.SPADES)
	TWO_SPADES = PlayingCard(Rank.TWO, Suit.SPADES)
	# --- Hearts ---
	ACE_HEARTS = PlayingCard(Rank.ACE, Suit.HEARTS)
	KING_HEARTS = PlayingCard(Rank.KING, Suit.HEARTS)
	QUEEN_HEARTS = PlayingCard(Rank.QUEEN, Suit.HEARTS)
	JACK_HEARTS = PlayingCard(Rank.JACK, Suit.HEARTS)
	TEN_HEARTS = PlayingCard(Rank.TEN, Suit.HEARTS)
	NINE_HEARTS = PlayingCard(Rank.NINE, Suit.HEARTS)
	EIGHT_HEARTS = PlayingCard(Rank.EIGHT, Suit.HEARTS)
	SEVEN_HEARTS = PlayingCard(Rank.SEVEN, Suit.HEARTS)
	SIX_HEARTS = PlayingCard(Rank.SIX, Suit.HEARTS)
	FIVE_HEARTS = PlayingCard(Rank.FIVE, Suit.HEARTS)
	FOUR_HEARTS = PlayingCard(Rank.FOUR, Suit.HEARTS)
	THREE_HEARTS = PlayingCard(Rank.THREE, Suit.HEARTS)
	TWO_HEARTS = PlayingCard(Rank.TWO, Suit.HEARTS)
	# --- Clubs ---
	ACE_CLUBS = PlayingCard(Rank.ACE, Suit.CLUBS)
	KING_CLUBS = PlayingCard(Rank.KING, Suit.CLUBS)
	QUEEN_CLUBS = PlayingCard(Rank.QUEEN, Suit.CLUBS)
	JACK_CLUBS = PlayingCard(Rank.JACK, Suit.CLUBS)
	TEN_CLUBS = PlayingCard(Rank.TEN, Suit.CLUBS)
	NINE_CLUBS = PlayingCard(Rank.NINE, Suit.CLUBS)
	EIGHT_CLUBS = PlayingCard(Rank.EIGHT, Suit.CLUBS)
	SEVEN_CLUBS = PlayingCard(Rank.SEVEN, Suit.CLUBS)
	SIX_CLUBS = PlayingCard(Rank.SIX, Suit.CLUBS)
	FIVE_CLUBS = PlayingCard(Rank.FIVE, Suit.CLUBS)
	FOUR_CLUBS = PlayingCard(Rank.FOUR, Suit.CLUBS)
	THREE_CLUBS = PlayingCard(Rank.THREE, Suit.CLUBS)
	TWO_CLUBS = PlayingCard(Rank.TWO, Suit.CLUBS)
	# --- Diamonds ---
	ACE_DIAMONDS = PlayingCard(Rank.ACE, Suit.DIAMONDS)
	KING_DIAMONDS = PlayingCard(Rank.KING, Suit.DIAMONDS)
	QUEEN_DIAMONDS = PlayingCard(Rank.QUEEN, Suit.DIAMONDS)
	JACK_DIAMONDS = PlayingCard(Rank.JACK, Suit.DIAMONDS)
	TEN_DIAMONDS = PlayingCard(Rank.TEN, Suit.DIAMONDS)
	NINE_DIAMONDS = PlayingCard(Rank.NINE, Suit.DIAMONDS)
	EIGHT_DIAMONDS = PlayingCard(Rank.EIGHT, Suit.DIAMONDS)
	SEVEN_DIAMONDS = PlayingCard(Rank.SEVEN, Suit.DIAMONDS)
	SIX_DIAMONDS = PlayingCard(Rank.SIX, Suit.DIAMONDS)
	FIVE_DIAMONDS = PlayingCard(Rank.FIVE, Suit.DIAMONDS)
	FOUR_DIAMONDS = PlayingCard(Rank.FOUR, Suit.DIAMONDS)
	THREE_DIAMONDS = PlayingCard(Rank.THREE, Suit.DIAMONDS)
	TWO_DIAMONDS = PlayingCard(Rank.TWO, Suit.DIAMONDS)
