# person.py
# Copyright 2024 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Person performance calculation from results in selected events.

Derived from performances.py in version 1.3.4 of chesscalc.

"""

_REWARD_TO_RESULT = {1: 1, 0: 0.5, -1: 0}


class Person:
    """Player details and calculation answers."""

    def __init__(self, code, name):
        """Initialise calculation data."""
        self.code = code
        self.name = name
        self.opponents = []
        self.reward = 0
        self.iteration = [0]
        self.points = 0
        self.score = 0

    @property
    def game_count(self):
        """Return number of games in population with player involved."""
        return len(self.opponents)

    def append_opponent(self, code):
        """Append code to self.opponents."""
        self.opponents.append(code)

    def add_points(self, points):
        """Add opponent's performance to points."""
        self.points += points

    def add_reward(self, reward, measure):
        """Increment total reward, total score and game count."""
        self.reward += reward * measure
        self.score += _REWARD_TO_RESULT[reward]

    def calculate_performance(self):
        """Calculate and set player's performance."""
        self.iteration.insert(
            0, float(self.points + self.reward) / self.game_count
        )
        del self.iteration[3:]

    @property
    def performance(self):
        """Return player's performance for use in next iteration."""
        return self.iteration[0]

    def normal_performance(self, base):
        """Return player's normalised performance relative to base.

        It is assumed base is the high performance in the population.

        The returned value is a positive number which is the difference
        between the high performance and the player's performance.  It is
        rounded to the nearest integer.

        """
        assert base >= self.performance
        return round(abs(self.performance - base))

    def is_performance_stable(self, delta):
        """Return True if performance is fixed for iteration calculations."""
        for item, number in enumerate(self.iteration[1:]):
            if abs(number - self.iteration[item]) > delta:
                break
        else:
            return True
        return False

    def set_points(self, points=0):
        """Initialise sum of opponent's performance to points."""
        self.points = points
