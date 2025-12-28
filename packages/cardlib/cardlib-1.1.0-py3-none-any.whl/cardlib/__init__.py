"""
A lightweight, extensible Python library for cards and dice.

Provides type-safe classes for Card models, customizable Decks, and
various Dice components for games and probability simulations.
"""

from .card import Card, Suit, Rank, PlayingCard, StandardPlayingCards
from .deck import Deck, PlayingCardDeck, InvalidCardTypeError, DeckMergeError
from .dice import Die, Dice, ExplodingDie, WeightedDie

__all__ = [
	# Cards
	'Card', 'Suit', 'Rank', 'PlayingCard', 'StandardPlayingCards',

	# Decks
	'Deck', 'PlayingCardDeck', 'InvalidCardTypeError', 'DeckMergeError',

	# Dice
	'Die', 'Dice', 'ExplodingDie', 'WeightedDie'
]

__version__ = '1.1.0'