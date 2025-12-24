# Concepts

## Table of Contents

### Theoretical Concepts
- [Cooperative games](#cooperative-games)
- [Example of cooperative game - "glove market"](#example-of-cooperative-game---glove-market)
- [Shapley Value](#shapley-value)
  - [Computational Complexity](#computational-complexity)
- [Harsanyi Dividends](#harsanyi-dividends)
- [References](#references)

### Implementation Concepts
- [Coalition or subset](#coalition-or-subset)
- [numba-game](#numba-game)

---

# Theoretical concepts

## Cooperative games

**Cooperative game** (see [wikipedia/Cooperative game theory](https://en.wikipedia.org/wiki/Cooperative_game_theory)) is a concept from game theory.

In a cooperative game, all the players work towards a common goal where each player has an option to participate or not to participate in the game. The subset of participating players is called a **coalition**. The game knows to evaluate the outcome of each coalition playing the game.

One of the tasks of cooperative game theory is to isolate the strength of the contribution of each of the players or of the coalition. There are many approaches and some implemented in this package.

## Example of cooperative game - "glove market"

The glove market is a story about a tourist coming to a market in need of a pair of gloves. At the market, there are two merchants that sell a left glove and one merchant that sells a right glove. The tourist needs one pair consisting of exactly one left glove and one right glove. For the sake of simplicity, the tourist is willing to pay 1 for that pair. Let's denote $L_1$, $L_2$ as the sellers of the left glove and $R$ as the seller of the right glove. We can summarize the value of each coalition in the following table:

|Coalitions|Value|Explanation|
|:--:|:--:|:--:|
|$\emptyset$ | 0 | No gloves - no sale|
|{$L_1$},{$L_2$},{$L_1$, $L_2$}| 0 | No right glove - no sale|
|{$R$}| 0 | No left glove - no sale|
|{$L_1$, $R$}, {$L_2$, $R$}, {$L_1$, $L_2$, $R$}| 1| Correct pair - sale|


The table above shows that the roles of $L_1$ and $L_2$ are interchangeable and that $R$ has more "power" over the outcome of the game. The results in game theory reflect this dynamic in various ways.

A generalization of this glove market game (where there could be an arbitrary number of left and right gloves) is implemented as an example in the {py:class}`shapley_numba.examples.GloveGame` class and featured in the {doc}`tutorial jupyter notebook <01 sample_notebook>`.

## Shapley Value
**Shapley Value** ([see wikipedia/Shapley Value](https://en.wikipedia.org/wiki/Shapley_value)) is a function that assigns each player a value representing their "fair share" of the total reward. The Shapley value can be defined as the unique solution satisfying several intuitive axioms, including:
- A player who contributes nothing receives zero value
- Players who contribute equally receive equal values
- The sum of all Shapley values equals the total value of the grand coalition 

In the glove market example above, the Shapley value $\phi$ yields $\phi(L_1) = \phi(L_2) = \frac{1}{6}$ and $\phi(R) = \frac{2}{3}$.

This result reflects the intuition from the game: $L_1$ and $L_2$ receive equal allocations (since their roles are symmetric), while $R$ gets the lion's share (reflecting the higher scarcity and importance of the right glove).

### Computational Complexity

From a computational perspective, calculating the Shapley Value requires evaluating all possible coalitions. For a game with $n$ players, there are $2^n$ possible coalitions, making this an exponentially complex computation. For example:
- 10 players → 1,024 coalitions
- 20 players → 1,048,576 coalitions
- 30 players → over 1 billion coalitions

This exponential growth is the primary motivation for developing efficient computational methods, which is the core purpose of `shapley_numba`.


## Harsanyi Dividends

**Harsanyi Dividends**, also called **synergies** or **interaction indices**, are a way to decompose the value function of a cooperative game. While the Shapley value measures individual player contributions, Harsanyi dividends measure the contribution of specific coalitions beyond what their subcoalitions could achieve.

Formally, for a coalition $S$, the Harsanyi dividend $\Delta(S)$ represents the marginal contribution of the coalition $S$ that cannot be attributed to any proper subset of $S$. This helps identify synergistic effects where groups of players working together create value that exceeds the sum of their individual or sub-group contributions.

**Key properties:**
- The Shapley value of a player can be computed as the sum of their Harsanyi dividends across all coalitions containing that player
- A positive dividend indicates positive synergy (the coalition creates more value together)
- A negative dividend indicates negative synergy or interference effects
- Dividends provide a complete decomposition of the game's value function

The Wikipedia article on [Shapley Value](https://en.wikipedia.org/wiki/Shapley_value) provides additional context on synergies and their relationship to Shapley values.

## References

1. Week 7 of  [Game Theory Coursera](https://www-cloudfront-alias.coursera.org/learn/game-theory-1) class explains cooperative games and Shapley value
1. Chapter 12 of Karlin, Anna R., Peres, Yuval ["Game theory, alive."](https://homes.cs.washington.edu/~karlin/GameTheoryBook.pdf) American Mathematical Society, ISBN:978-1-4704-1982-0.


# Implementation Concepts of `shapley_numba`

The implementation of the theoretical concepts in this package is designed to be JIT-compilable using the `numba` package. This allows for high-performance computation while maintaining the flexibility of Python code.

## Coalition or subset

A **coalition**, which is a subset of all players, is represented in our package by an integer `numpy` array of 0s and 1s. A value of 1 at index $i$ indicates that player $i$ is present in the coalition, while 0 indicates they are not.

**Example:** For a game with 4 players, the coalition {Player 0, Player 2} would be represented as the array `[1, 0, 1, 0]`.

(numba-game)=
## numba-game

A `numba_game` is a class that can be JIT-compiled using [numba.experimental.jitclass](inv:numba#user/jitclass). Using a class-based approach allows the game state to be encapsulated within the object rather than passed as external parameters.

**Game State Example:** In the glove game, the state includes the number of left gloves and right gloves available in the market.

**Main Interface:** The primary interface of a `numba_game` is the `value` function with the following signature:

```python
value(self, subset: ndarray[int32]) -> float
```

- **Input:** A coalition represented as a numpy array (as described above)
- **Output:** A float representing the value that coalition can achieve in the game

**Example Implementation:** See {py:class}`shapley_numba.examples.GloveGame` for a complete example of how to implement a custom game using this interface.