# src/antfarm/sim.py

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from antfarm.config import (
    PHER_DECAY,
    PHER_DEPOSIT_FOOD,
    PHER_DIFFUSE_EVERY,
    PHER_DIFFUSE_RATE,
    PHER_HOME_SOURCE,
    W_FOOD_PHER,
    W_HOME_PHER,
    W_RANDOM,
)


@dataclass
class Ant:
    # grid position
    gx: int
    gy: int

    # movement animation (continuous render)
    prev_gx: int
    prev_gy: int
    next_gx: int
    next_gy: int

    # simple state
    has_food: bool = False


class Sim:
    def __init__(self, w: int, h: int, num_ants: int, seed: int = 1) -> None:
        self.w = w
        self.h = h
        self.rng = Random(seed)

        self.nest = (w // 2, h // 2)

        # Food is stored as integer "amount" per cell
        self.food = [[0 for _ in range(w)] for _ in range(h)]
        self._spawn_initial_food()

        # Pheromone fields (float intensity per cell)
        self.pher_food = [[0.0 for _ in range(w)] for _ in range(h)]
        self.pher_home = [[0.0 for _ in range(w)] for _ in range(h)]

        self.ants: list[Ant] = []
        for _ in range(num_ants):
            x, y = self.nest
            self.ants.append(Ant(x, y, x, y, x, y))

        self.tick = 0

    def _spawn_initial_food(self) -> None:
        # Drop a few piles around the map
        for _ in range(8):
            cx = self.rng.randrange(5, self.w - 5)
            cy = self.rng.randrange(5, self.h - 5)
            amount = self.rng.randrange(20, 60)
            self.food[cy][cx] += amount

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def _evaporate(self) -> None:
        for y in range(self.h):
            for x in range(self.w):
                self.pher_food[y][x] *= PHER_DECAY
                self.pher_home[y][x] *= PHER_DECAY

    def _diffuse_once(self) -> None:
        # Simple diffusion: blend each cell with the average of its 4-neighbors
        new_food = [[0.0 for _ in range(self.w)] for _ in range(self.h)]
        new_home = [[0.0 for _ in range(self.w)] for _ in range(self.h)]

        for y in range(self.h):
            for x in range(self.w):
                n = 0
                sum_food = 0.0
                sum_home = 0.0

                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h:
                        n += 1
                        sum_food += self.pher_food[yy][xx]
                        sum_home += self.pher_home[yy][xx]

                if n == 0:
                    new_food[y][x] = self.pher_food[y][x]
                    new_home[y][x] = self.pher_home[y][x]
                else:
                    avg_food = sum_food / n
                    avg_home = sum_home / n
                    new_food[y][x] = (1 - PHER_DIFFUSE_RATE) * self.pher_food[y][x] + PHER_DIFFUSE_RATE * avg_food
                    new_home[y][x] = (1 - PHER_DIFFUSE_RATE) * self.pher_home[y][x] + PHER_DIFFUSE_RATE * avg_home

        self.pher_food = new_food
        self.pher_home = new_home

    def step(self) -> None:
        self.tick += 1

        nx, ny = self.nest
        # Reinforce "home scent" at the nest each tick
        self.pher_home[ny][nx] += PHER_HOME_SOURCE

        for ant in self.ants:
            # shift animation anchors
            ant.prev_gx, ant.prev_gy = ant.gx, ant.gy

            # Deposit pheromone when carrying food
            if ant.has_food:
                self.pher_food[ant.gy][ant.gx] += PHER_DEPOSIT_FOOD

            # Decide a grid move
            choices = [
                (ant.gx + 1, ant.gy),
                (ant.gx - 1, ant.gy),
                (ant.gx, ant.gy + 1),
                (ant.gx, ant.gy - 1),
            ]
            choices = [(x, y) for (x, y) in choices if self.in_bounds(x, y)]
            self.rng.shuffle(choices)

            if ant.has_food:
                # Prefer moves that increase home pheromone and move toward nest
                best = (ant.gx, ant.gy)
                best_score = -1e9

                for (x, y) in choices:
                    dist = abs(x - nx) + abs(y - ny)
                    score = (
                        W_HOME_PHER * self.pher_home[y][x]
                        - 0.6 * dist
                        + self.rng.random() * W_RANDOM
                    )
                    if score > best_score:
                        best_score = score
                        best = (x, y)

                ant.next_gx, ant.next_gy = best
            else:
                # Pick up food if standing on it
                if self.food[ant.gy][ant.gx] > 0:
                    self.food[ant.gy][ant.gx] -= 1
                    ant.has_food = True
                    ant.next_gx, ant.next_gy = ant.gx, ant.gy
                else:
                    # Search: follow food pheromone, avoid clumping at nest, avoid edges/corners
                    best = (ant.gx, ant.gy)
                    best_score = -1e9

                    for (x, y) in choices:
                        dist_from_nest = abs(x - nx) + abs(y - ny)

                        # distance to nearest edge (0 means on border)
                        edge_dist = min(x, self.w - 1 - x, y, self.h - 1 - y)

                        # Repel only when close to nest (prevents stacking)
                        nest_repulsion = 0.0
                        if dist_from_nest <= 4:
                            nest_repulsion = (4 - dist_from_nest) * 1.2

                        # Penalize being near the edge (prevents corner hugging)
                        edge_penalty = 0.0
                        if edge_dist <= 2:
                            edge_penalty = (2 - edge_dist) * 1.4

                        score = (
                            W_FOOD_PHER * self.pher_food[y][x]
                            - nest_repulsion
                            - edge_penalty
                            + self.rng.random() * W_RANDOM
                        )

                        # Bonus if that cell has food
                        if self.food[y][x] > 0:
                            score += 2.5

                        if score > best_score:
                            best_score = score
                            best = (x, y)

                    ant.next_gx, ant.next_gy = best

            # Apply move at the end of the tick decision
            ant.gx, ant.gy = ant.next_gx, ant.next_gy

            # If carrying food and reached nest, drop it
            if ant.has_food and (ant.gx, ant.gy) == self.nest:
                ant.has_food = False

        # Evaporate and diffuse pheromones
        self._evaporate()
        if PHER_DIFFUSE_EVERY > 0 and (self.tick % PHER_DIFFUSE_EVERY == 0):
            self._diffuse_once()
