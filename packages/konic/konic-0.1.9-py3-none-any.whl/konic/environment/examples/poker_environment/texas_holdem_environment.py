"""
Texas Hold'em Poker Environment Example

A simplified Texas Hold'em poker environment where an agent plays against one opponent.
The game follows basic Texas Hold'em rules with betting rounds.

Actions:
    0: Fold
    1: Call/Check
    2: Raise (minimum bet)

Game Flow:
    1. Pre-flop: Each player receives 2 hole cards
    2. Flop: 3 community cards revealed
    3. Turn: 1 additional community card
    4. River: Final community card
    5. Showdown: Best hand wins

Reward:
    - Positive reward for winning the pot
    - Negative reward for losing chips
    - Bonus for winning with strong hands

Termination:
    - Episode ends when a player folds
    - Episode ends at showdown
    - Episode ends when a player runs out of chips
"""

from __future__ import annotations

import random
from typing import Any

import numpy as np

from konic.environment import KonicEnvironment
from konic.environment.examples.poker_environment.game_logic import (
    Card,
    Deck,
    PokerHandEvaluator,
    PokerRound,
)
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicBound, KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer, custom_termination


class PokerActionSpace(KonicSpace):
    """Action space for poker: fold, call/check, raise."""

    action: KonicDiscrete = 3


class PokerObservationSpace(KonicSpace):
    """Observation space for poker game state."""

    hole_card_1: KonicBound = ((1,), 0.0, 51.0)
    hole_card_2: KonicBound = ((1,), 0.0, 51.0)

    community_card_1: KonicBound = ((1,), -1.0, 51.0)
    community_card_2: KonicBound = ((1,), -1.0, 51.0)
    community_card_3: KonicBound = ((1,), -1.0, 51.0)
    community_card_4: KonicBound = ((1,), -1.0, 51.0)
    community_card_5: KonicBound = ((1,), -1.0, 51.0)

    current_round: KonicBound = ((1,), 0.0, 4.0)
    pot_size: KonicBound = ((1,), 0.0, np.inf)
    player_chips: KonicBound = ((1,), 0.0, np.inf)
    opponent_chips: KonicBound = ((1,), 0.0, np.inf)
    current_bet: KonicBound = ((1,), 0.0, 1000.0)
    player_bet: KonicBound = ((1,), 0.0, 1000.0)


class PokerRewardComposer(KonicRewardComposer["TexasHoldemEnvironment"]):
    """Compose rewards for poker environment."""

    @custom_reward
    def pot_won(self) -> float:
        """Reward for winning the pot."""
        if hasattr(self.env, "_pot_won") and self.env._pot_won:
            reward = self.env.pot / 10.0
            self.env._pot_won = False
            return reward
        return 0.0

    @custom_reward
    def pot_lost(self) -> float:
        """Penalty for losing the pot."""
        if hasattr(self.env, "_pot_lost") and self.env._pot_lost:
            penalty = -self.env.player_bet_this_round / 10.0
            self.env._pot_lost = False
            return penalty
        return 0.0

    @custom_reward
    def hand_strength_bonus(self) -> float:
        """Bonus reward for winning with a strong hand."""
        if hasattr(self.env, "_hand_strength_bonus"):
            bonus = self.env._hand_strength_bonus
            self.env._hand_strength_bonus = 0.0
            return bonus
        return 0.0

    @custom_reward
    def folding_penalty(self) -> float:
        """Small penalty for folding to discourage excessive folding."""
        if hasattr(self.env, "_just_folded") and self.env._just_folded:
            self.env._just_folded = False
            return -0.5
        return 0.0


class PokerTerminationComposer(KonicTerminationComposer["TexasHoldemEnvironment"]):
    """Compose termination conditions for poker environment."""

    def terminated(self) -> bool:
        """Base termination (always False, use custom conditions)."""
        return False

    @custom_termination
    def player_folded(self) -> bool:
        """Episode ends if player folds."""
        return self.env.game_over and self.env.winner == "opponent"

    @custom_termination
    def opponent_folded(self) -> bool:
        """Episode ends if opponent folds."""
        return self.env.game_over and self.env.winner == "player"

    @custom_termination
    def showdown_complete(self) -> bool:
        """Episode ends after showdown."""
        return self.env.current_round == PokerRound.SHOWDOWN and self.env.game_over

    @custom_termination
    def out_of_chips(self) -> bool:
        """Episode ends if player runs out of chips."""
        return self.env.player_chips <= 0


class TexasHoldemEnvironment(KonicEnvironment):
    """
    Texas Hold'em Poker Environment.

    A simplified poker game where the agent plays heads-up (1v1) against
    a simple opponent AI that makes random decisions.
    """

    def __init__(
        self,
        initial_chips: int = 1000,
        small_blind: int = 10,
        big_blind: int = 20,
        flatten_spaces: bool = False,
    ):
        """
        Initialize the Texas Hold'em environment.

        Args:
            initial_chips: Starting chip count for both players
            small_blind: Small blind amount
            big_blind: Big blind amount
            flatten_spaces: If True, automatically flatten Dict spaces for RLlib compatibility
        """
        super().__init__(
            action_space=PokerActionSpace(),
            observation_space=PokerObservationSpace(),
            reward_composer=PokerRewardComposer(),
            termination_composer=PokerTerminationComposer(),
            flatten_spaces=flatten_spaces,
        )

        self.initial_chips = initial_chips
        self.small_blind = small_blind
        self.big_blind = big_blind

        self.player_chips = initial_chips
        self.opponent_chips = initial_chips
        self.pot = 0
        self.current_bet = 0
        self.player_bet_this_round = 0
        self.opponent_bet_this_round = 0

        self.deck: Deck | None = None
        self.player_hand: list[Card] = []
        self.opponent_hand: list[Card] = []
        self.community_cards: list[Card] = []

        self.current_round = PokerRound.PREFLOP
        self.game_over = False
        self.winner: str | None = None

        self._pot_won = False
        self._pot_lost = False
        self._hand_strength_bonus = 0.0
        self._just_folded = False

    def _reset(self, seed: int | None = None, options: dict | None = None):
        """Reset the environment for a new hand."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.player_chips = self.initial_chips
        self.opponent_chips = self.initial_chips
        self.pot = 0
        self.current_bet = self.big_blind
        self.player_bet_this_round = self.big_blind
        self.opponent_bet_this_round = self.small_blind

        self.deck = Deck()
        self.player_hand = self.deck.deal(2)
        self.opponent_hand = self.deck.deal(2)
        self.community_cards = []

        self.current_round = PokerRound.PREFLOP
        self.game_over = False
        self.winner = None

        self.player_chips -= self.big_blind
        self.opponent_chips -= self.small_blind
        self.pot = self.small_blind + self.big_blind

        self._pot_won = False
        self._pot_lost = False
        self._hand_strength_bonus = 0.0
        self._just_folded = False

        observation = self.get_obs()
        info = self.get_info()

        return observation, info

    def _step(self, action: dict[str, Any]):
        """Execute one step in the environment."""
        action_value = action["action"]

        self._pot_won = False
        self._pot_lost = False
        self._hand_strength_bonus = 0.0
        self._just_folded = False

        if not self.game_over:
            if action_value == 0:
                self._handle_fold(is_player=True)
            elif action_value == 1:
                self._handle_call(is_player=True)
            elif action_value == 2:
                self._handle_raise(is_player=True)

            if not self.game_over:
                self._opponent_action()

            if not self.game_over and self.player_bet_this_round == self.opponent_bet_this_round:
                self._advance_round()

        observation = self.get_obs()
        reward = self.reward_composer.compose()
        terminated = self.termination_composer.compose()
        truncated = False
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def _handle_fold(self, is_player: bool):
        """Handle a fold action."""
        self.game_over = True
        if is_player:
            self.winner = "opponent"
            self.opponent_chips += self.pot
            self._pot_lost = True
            self._just_folded = True
        else:
            self.winner = "player"
            self.player_chips += self.pot
            self._pot_won = True

    def _handle_call(self, is_player: bool):
        """Handle a call/check action."""
        if is_player:
            call_amount = self.current_bet - self.player_bet_this_round
            call_amount = min(call_amount, self.player_chips)
            self.player_chips -= call_amount
            self.player_bet_this_round += call_amount
            self.pot += call_amount
        else:
            call_amount = self.current_bet - self.opponent_bet_this_round
            call_amount = min(call_amount, self.opponent_chips)
            self.opponent_chips -= call_amount
            self.opponent_bet_this_round += call_amount
            self.pot += call_amount

    def _handle_raise(self, is_player: bool):
        """Handle a raise action."""
        raise_amount = self.big_blind

        if is_player:
            call_amount = self.current_bet - self.player_bet_this_round
            total_bet = call_amount + raise_amount
            total_bet = min(total_bet, self.player_chips)

            self.player_chips -= total_bet
            self.player_bet_this_round += total_bet
            self.pot += total_bet
            self.current_bet = self.player_bet_this_round
        else:
            call_amount = self.current_bet - self.opponent_bet_this_round
            total_bet = call_amount + raise_amount
            total_bet = min(total_bet, self.opponent_chips)
            self.opponent_chips -= total_bet
            self.opponent_bet_this_round += total_bet
            self.pot += total_bet
            self.current_bet = self.opponent_bet_this_round

    def _opponent_action(self):
        """Simple opponent AI that makes random decisions."""

        rand = random.random()

        if rand < 0.1:
            self._handle_fold(is_player=False)
        elif rand < 0.7:
            self._handle_call(is_player=False)
        else:
            self._handle_raise(is_player=False)

    def _advance_round(self):
        """Advance to the next betting round."""
        if self.deck is None:
            return

        if self.current_round == PokerRound.PREFLOP:
            self.community_cards.extend(self.deck.deal(3))
            self.current_round = PokerRound.FLOP
        elif self.current_round == PokerRound.FLOP:
            self.community_cards.extend(self.deck.deal(1))
            self.current_round = PokerRound.TURN
        elif self.current_round == PokerRound.TURN:
            self.community_cards.extend(self.deck.deal(1))
            self.current_round = PokerRound.RIVER
        elif self.current_round == PokerRound.RIVER:
            self._showdown()
            self.current_round = PokerRound.SHOWDOWN

        self.current_bet = 0
        self.player_bet_this_round = 0
        self.opponent_bet_this_round = 0

    def _showdown(self):
        """Determine winner at showdown."""
        player_best = self.player_hand + self.community_cards
        opponent_best = self.opponent_hand + self.community_cards

        result = PokerHandEvaluator.compare_hands(player_best, opponent_best)
        self.game_over = True

        if result > 0:
            self.winner = "player"
            self.player_chips += self.pot
            self._pot_won = True

            hand_rank, _ = PokerHandEvaluator.evaluate_hand(player_best)
            self._hand_strength_bonus = hand_rank.value * 0.5
        elif result < 0:
            self.winner = "opponent"
            self.opponent_chips += self.pot
            self._pot_lost = True
        else:
            self.winner = "tie"
            split = self.pot // 2
            self.player_chips += split
            self.opponent_chips += split

    def get_obs(self):
        """Get current observation."""

        hole_cards = [c.to_value() for c in self.player_hand]
        community_cards = [c.to_value() for c in self.community_cards]

        while len(community_cards) < 5:
            community_cards.append(-1)

        return {
            "hole_card_1": np.array([hole_cards[0]], dtype=np.float32),
            "hole_card_2": np.array([hole_cards[1]], dtype=np.float32),
            "community_card_1": np.array([community_cards[0]], dtype=np.float32),
            "community_card_2": np.array([community_cards[1]], dtype=np.float32),
            "community_card_3": np.array([community_cards[2]], dtype=np.float32),
            "community_card_4": np.array([community_cards[3]], dtype=np.float32),
            "community_card_5": np.array([community_cards[4]], dtype=np.float32),
            "current_round": np.array([self.current_round.value], dtype=np.float32),
            "pot_size": np.array([self.pot], dtype=np.float32),
            "player_chips": np.array([self.player_chips], dtype=np.float32),
            "opponent_chips": np.array([self.opponent_chips], dtype=np.float32),
            "current_bet": np.array([self.current_bet], dtype=np.float32),
            "player_bet": np.array([self.player_bet_this_round], dtype=np.float32),
        }

    def get_info(self):
        """Get current game info."""
        return {
            "player_hand": [str(c) for c in self.player_hand],
            "community_cards": [str(c) for c in self.community_cards],
            "current_round": self.current_round.name,
            "pot": self.pot,
            "player_chips": self.player_chips,
            "opponent_chips": self.opponent_chips,
            "game_over": self.game_over,
            "winner": self.winner,
        }


def main() -> None:
    """Demo the Texas Hold'em environment."""
    from konic.environment.examples.poker_environment.runner import runner

    env = TexasHoldemEnvironment(initial_chips=1000, small_blind=10, big_blind=20)
    runner(env)


if __name__ == "__main__":
    main()
