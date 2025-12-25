def runner(env):
    print("=" * 60)
    print("Texas Hold'em Poker Environment Demo - 10 Hands")
    print("=" * 60)

    stats = {
        "hands_played": 0,
        "hands_won": 0,
        "hands_lost": 0,
        "hands_tied": 0,
        "total_reward": 0.0,
        "total_pot_won": 0,
        "total_pot_lost": 0,
        "folds": 0,
        "showdowns": 0,
    }

    for hand_num in range(1, 11):
        obs, info = env.reset()

        print(f"\n{'=' * 60}")
        print(f"Hand {hand_num}/10")
        print(f"{'=' * 60}")
        print(f"Player hand: {info['player_hand']}")
        print(f"Starting pot: ${info['pot']}")
        print(f"Player chips: ${info['player_chips']}")
        print()

        hand_reward = 0
        step_count = 0

        while step_count < 20:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            hand_reward += float(reward)
            step_count += 1

            action_names = ["Fold", "Call/Check", "Raise"]
            print(
                f"  Step {step_count}: {action_names[action['action']]} | "
                f"Round: {info['current_round']} | Pot: ${info['pot']} | "
                f"Reward: {reward:.2f}"
            )

            if terminated or truncated:
                print(f"\n  Hand Result: {info['winner'].upper()}")
                print(f"  Final pot: ${info['pot']}")
                print(f"  Player chips: ${info['player_chips']}")
                print(f"  Hand reward: {hand_reward:.2f}")

                stats["hands_played"] += 1
                stats["total_reward"] += hand_reward

                if info["winner"] == "player":
                    stats["hands_won"] += 1
                    stats["total_pot_won"] += info["pot"]
                elif info["winner"] == "opponent":
                    stats["hands_lost"] += 1
                    if action["action"] == 0:
                        stats["folds"] += 1
                elif info["winner"] == "tie":
                    stats["hands_tied"] += 1

                if info["current_round"] == "SHOWDOWN":
                    stats["showdowns"] += 1

                break

        print(f"\n{'=' * 60}")
        print("FINAL STATISTICS")
        print(f"{'=' * 60}")
        print(f"Hands Played:     {stats['hands_played']}")
        print(
            f"Hands Won:        {stats['hands_won']} ({stats['hands_won']/stats['hands_played']*100:.1f}%)"
        )
        print(
            f"Hands Lost:       {stats['hands_lost']} ({stats['hands_lost']/stats['hands_played']*100:.1f}%)"
        )
        print(
            f"Hands Tied:       {stats['hands_tied']} ({stats['hands_tied']/stats['hands_played']*100:.1f}%)"
        )
        print(f"Folds:            {stats['folds']}")
        print(f"Showdowns:        {stats['showdowns']}")
        print(f"Total Reward:     {stats['total_reward']:.2f}")
        print(f"Average Reward:   {stats['total_reward']/stats['hands_played']:.2f}")
        print(f"Total Pot Won:    ${stats['total_pot_won']}")
        print(f"Final Chips:      ${env.player_chips}")
        print(f"Net Profit/Loss:  ${env.player_chips - env.initial_chips}")
        print("=" * 60)
