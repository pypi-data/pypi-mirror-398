import random
from enum import Enum


class PokerRound(Enum):
    """Poker betting rounds."""

    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


class HandRank(Enum):
    """Poker hand rankings."""

    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class Card:
    """Represents a playing card."""

    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    SUITS = ["♠", "♥", "♦", "♣"]

    def __init__(self, rank: int, suit: int):
        self.rank = rank  # 0-12 (2 through A)
        self.suit = suit  # 0-3

    def __repr__(self):
        return f"{self.RANKS[self.rank]}{self.SUITS[self.suit]}"

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def to_value(self) -> int:
        """Convert card to unique integer for observation."""
        return self.rank * 4 + self.suit


class Deck:
    """Represents a deck of cards."""

    def __init__(self):
        self.cards = [Card(rank, suit) for rank in range(13) for suit in range(4)]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, n: int = 1) -> list[Card]:
        """Deal n cards from the deck."""
        return [self.cards.pop() for _ in range(n)]


class PokerHandEvaluator:
    """Evaluates poker hands."""

    @staticmethod
    def evaluate_hand(cards: list[Card]) -> tuple[HandRank, list[int]]:
        """
        Evaluate a poker hand and return its rank and tiebreaker values.

        Returns:
            tuple of (HandRank, list of tiebreaker values in descending order)
        """
        if len(cards) < 5:
            return HandRank.HIGH_CARD, sorted([c.rank for c in cards], reverse=True)

        # Sort cards by rank
        sorted_cards = sorted(cards, key=lambda c: c.rank, reverse=True)
        ranks = [c.rank for c in sorted_cards]
        suits = [c.suit for c in sorted_cards]

        # Count rank frequencies
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        # Sort by count then rank
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = PokerHandEvaluator._check_straight(ranks)

        # Check for royal flush
        if is_flush and is_straight and max(ranks) == 12:  # Ace high
            return HandRank.ROYAL_FLUSH, [12]

        # Check for straight flush
        if is_flush and is_straight:
            return HandRank.STRAIGHT_FLUSH, [max(ranks)]

        # Check for four of a kind
        if sorted_counts[0][1] == 4:
            return HandRank.FOUR_OF_KIND, [sorted_counts[0][0], sorted_counts[1][0]]

        # Check for full house
        if sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
            return HandRank.FULL_HOUSE, [sorted_counts[0][0], sorted_counts[1][0]]

        # Check for flush
        if is_flush:
            return HandRank.FLUSH, sorted(ranks, reverse=True)[:5]

        # Check for straight
        if is_straight:
            return HandRank.STRAIGHT, [max(ranks)]

        # Check for three of a kind
        if sorted_counts[0][1] == 3:
            kickers = [r for r, c in sorted_counts[1:]]
            return HandRank.THREE_OF_KIND, [sorted_counts[0][0]] + kickers[:2]

        # Check for two pair
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            pairs = [sorted_counts[0][0], sorted_counts[1][0]]
            kicker = [r for r, c in sorted_counts[2:]]
            return HandRank.TWO_PAIR, sorted(pairs, reverse=True) + kicker[:1]

        # Check for pair
        if sorted_counts[0][1] == 2:
            kickers = [r for r, c in sorted_counts[1:]]
            return HandRank.PAIR, [sorted_counts[0][0]] + kickers[:3]

        # High card
        return HandRank.HIGH_CARD, sorted(ranks, reverse=True)[:5]

    @staticmethod
    def _check_straight(ranks: list[int]) -> bool:
        """Check if ranks form a straight."""
        unique_ranks = sorted(set(ranks), reverse=True)
        if len(unique_ranks) < 5:
            return False

        # Check for regular straight
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i + 4] == 4:
                return True

        # Check for A-2-3-4-5 straight (wheel)
        if (
            12 in unique_ranks
            and 0 in unique_ranks
            and 1 in unique_ranks
            and 2 in unique_ranks
            and 3 in unique_ranks
        ):
            return True

        return False

    @staticmethod
    def compare_hands(hand1: list[Card], hand2: list[Card]) -> int:
        """
        Compare two poker hands.

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, tiebreaker1 = PokerHandEvaluator.evaluate_hand(hand1)
        rank2, tiebreaker2 = PokerHandEvaluator.evaluate_hand(hand2)

        if rank1.value > rank2.value:
            return 1
        elif rank1.value < rank2.value:
            return -1
        else:
            # Same rank, compare tiebreakers
            for t1, t2 in zip(tiebreaker1, tiebreaker2):
                if t1 > t2:
                    return 1
                elif t1 < t2:
                    return -1
            return 0
