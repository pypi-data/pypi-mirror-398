import random

class Die:
	"""Represents a single die with arbitrary number of sides."""

	__slots__ = ('sides', '_value')

	def __init__(self, sides=6):
		if sides < 2:
			raise ValueError('Die must have at least 2 sides')
		self.sides = sides
		self._value = None # most recent roll

	def roll(self):
		"""Roll the die and store its value."""
		self._value = random.randint(1, self.sides)
		return self._value
	
	@property
	def value(self):
		"""Current face value of the die. None if not rolled yet."""
		return self._value
	
	@value.setter
	def value(self, val):
		"""Manually set the die value."""
		if not (1 <= val <= self.sides):
			raise ValueError(f'Die must be between 1 and {self.sides}')
		self._value = val
	
	def __repr__(self):
		return f'Die({self.sides} sides, showing={self._value})'
	
	def __str__(self):
		return str(self._value) if self._value is not None else f'Unrolled d{self.sides}'
	

class Dice:
	"""Represents a collection of one or more dice."""

	def __init__(self, *dice):
		"""Accepts `Die` instances or numbers of sides to create dice."""
		self._dice = []
		for d in dice:
			if isinstance(d, Die):
				self._dice.append(d)
			elif isinstance(d, int):
				self._dice.append(Die(d))
			else:
				raise TypeError('Dice constructor accepts Die instances or integers')
			
	def roll(self):
		"""Roll all dice, return the total sum."""
		total = 0
		for die in self._dice:
			total += die.roll()
		return total
	
	@property
	def values(self):
		"""List of the current face values for each die in the collection."""
		return [die.value for die in self._dice]
	
	# Alias for values
	faces = values
	
	@property
	def total(self):
		"""Sum of all current face values (treats unrolled dice as 0)."""
		return sum((die.value or 0) for die in self._dice)
	
	def __getitem__(self, index):
		return self._dice[index] # return Die instance
	
	def __len__(self):
		return len(self._dice)
	
	def __iter__(self):
		return iter(self._dice)

	def __repr__(self):
		return f'Dice({self._dice})'
	
	def __str__(self):
		if all(v is not None for v in self.values):
			return ' + '.join(str(die) for die in self._dice) + f' = {self.total}'
		return ' + '.join(str(die) for die in self._dice)
	

# --- Unique Die Types ---

class ExplodingDie(Die):
	"""A die that "explodes" – rolls again when its maximum side is hit, adding up the total."""

	__slots__ = ('explosions', 'max_explosions')

	def __init__(self, sides=6, max_explosions=None):
		super().__init__(sides)
		self.max_explosions = max_explosions # None = unlimited
		self.explosions = 0 # number of extra rolls triggered

	def roll(self):
		total = 0
		self.explosions = 0
		while True:
			val = random.randint(1, self.sides)
			total += val
			if val == self.sides:
				self.explosions += 1
				if self.max_explosions is None or self.explosions < self.max_explosions:
					continue
			break
		self._value = total
		return total
	
	def __repr__(self):
		return f'ExplodingDie({self.sides}, total={self._value}, explosions={self.explosions}, max_explosions={self.max_explosions})'
	
	def __str__(self):
		if self.explosions:
			return f'{self._value} (exploded {self.explosions}x)'
		return super().__str__()
	

class WeightedDie(Die):
	"""A die with weighted probabilities for each side."""

	__slots__ = ('weights',)

	def __init__(self, sides=6, weights=None):
		super().__init__(sides)
		if weights is not None and len(weights) != sides:
			raise ValueError('Weights must match the number of sides')
		self.weights = weights or [1] * sides
		if any(w < 0 for w in self.weights):
			raise ValueError('Weights must be non-negative')

	def roll(self):
		self._value = random.choices(range(1, self.sides + 1), weights=self.weights, k=1)[0]
		return self._value
	
	def __repr__(self):
		return f'WeightedDie({self.sides}, showing={self._value}, weights={self.weights})'
	
