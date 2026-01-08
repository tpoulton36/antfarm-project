# src/antfarm/render_pygame.py

from __future__ import annotations

import pygame

from antfarm.config import (
    ANT_RADIUS,
    CELL_SIZE,
    FOOD_RADIUS,
    FPS,
    GRID_H,
    GRID_W,
    NEST_RADIUS,
    NUM_ANTS,
    SIM_TPS,
)
from antfarm.sim import Sim


def _cell_center_px(gx: float, gy: float) -> tuple[int, int]:
    x = int(gx * CELL_SIZE + CELL_SIZE / 2)
    y = int(gy * CELL_SIZE + CELL_SIZE / 2)
    return x, y


def run() -> None:
    pygame.init()
    screen = pygame.display.set_mode((GRID_W * CELL_SIZE, GRID_H * CELL_SIZE))
    pygame.display.set_caption("AntFarm Phase 1")
    clock = pygame.time.Clock()

    sim = Sim(GRID_W, GRID_H, NUM_ANTS, seed=1)

    # Fixed-timestep simulation with smooth rendering interpolation
    sim_step_ms = 1000.0 / SIM_TPS
    accumulator = 0.0
    last_ms = pygame.time.get_ticks()

    running = True
    while running:
        now_ms = pygame.time.get_ticks()
        dt_ms = now_ms - last_ms
        last_ms = now_ms
        accumulator += dt_ms

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Step simulation at fixed rate
        while accumulator >= sim_step_ms:
            sim.step()
            accumulator -= sim_step_ms

        # Interpolation factor between ticks (0..1)
        alpha = 0.0 if sim_step_ms == 0 else accumulator / sim_step_ms

        screen.fill((20, 20, 20))

        # Draw food (only cells with food)
        for y in range(sim.h):
            row = sim.food[y]
            for x in range(sim.w):
                if row[x] > 0:
                    px, py = _cell_center_px(x, y)
                    pygame.draw.circle(screen, (70, 200, 70), (px, py), FOOD_RADIUS)

        # Draw nest
        nx, ny = sim.nest
        npx, npy = _cell_center_px(nx, ny)
        pygame.draw.circle(screen, (200, 200, 90), (npx, npy), NEST_RADIUS)

        # Draw ants with smooth interpolation from prev cell to current cell
        for ant in sim.ants:
            gx = ant.prev_gx + (ant.gx - ant.prev_gx) * alpha
            gy = ant.prev_gy + (ant.gy - ant.prev_gy) * alpha
            px, py = _cell_center_px(gx, gy)

            color = (220, 120, 120) if ant.has_food else (220, 220, 220)
            pygame.draw.circle(screen, color, (px, py), ANT_RADIUS)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
