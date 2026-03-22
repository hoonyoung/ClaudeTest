#!/usr/bin/env python3
"""
ParticleMove - 파티클 충돌 물리 시뮬레이션
당구공처럼 탄성 충돌하는 원형 파티클 시뮬레이션
"""

import pygame
import sys
import math
import random
import tkinter as tk
from tkinter import simpledialog

# 화면 설정
WIDTH, HEIGHT = 960, 700
BG_COLOR = (12, 12, 22)
FPS = 60
PARTICLE_RADIUS = 14
MIN_SPEED = 2.0
MAX_SPEED = 5.5

# 파티클 색상 팔레트
COLORS = [
    (255, 80,  80),   # 빨강
    (80,  220, 80),   # 초록
    (80,  140, 255),  # 파랑
    (255, 215, 50),   # 노랑
    (255, 110, 200),  # 핑크
    (60,  230, 230),  # 시안
    (225, 120, 40),   # 주황
    (180, 80,  255),  # 보라
    (255, 195, 95),   # 골드
    (90,  255, 175),  # 민트
]


class Particle:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = PARTICLE_RADIUS
        self.mass = 1.0
        self.color = random.choice(COLORS)

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(MIN_SPEED, MAX_SPEED)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # 벽 충돌 처리
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx = -abs(self.vx)

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy)
        elif self.y + self.radius > HEIGHT - 50:   # HUD 공간 확보
            self.y = HEIGHT - 50 - self.radius
            self.vy = -abs(self.vy)

    def draw(self, surface: pygame.Surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius

        # 본체
        pygame.draw.circle(surface, self.color, (cx, cy), r)

        # 내부 밝은 원 (입체감)
        bright = tuple(min(255, c + 60) for c in self.color)
        pygame.draw.circle(surface, bright, (cx, cy), r - 4)

        # 하이라이트 (빛 반사)
        hl_x = cx - r // 3
        hl_y = cy - r // 3
        pygame.draw.circle(surface, (255, 255, 255), (hl_x, hl_y), r // 5)


def resolve_collision(p1: Particle, p2: Particle) -> bool:
    """두 파티클 사이의 탄성 충돌을 계산하고 속도를 갱신."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dist_sq = dx * dx + dy * dy
    min_dist = p1.radius + p2.radius

    if dist_sq >= min_dist * min_dist:
        return False

    dist = math.sqrt(dist_sq)
    if dist < 1e-6:
        # 완전히 겹친 경우 임의 방향으로 분리
        angle = random.uniform(0, 2 * math.pi)
        dx, dy = math.cos(angle), math.sin(angle)
        dist = 1.0

    # 충돌 법선 벡터
    nx = dx / dist
    ny = dy / dist

    # 법선 방향 상대속도
    dvx = p1.vx - p2.vx
    dvy = p1.vy - p2.vy
    dot = dvx * nx + dvy * ny

    # 이미 멀어지는 중이면 처리하지 않음
    if dot >= 0:
        return False

    # 등질량 탄성 충돌 임펄스 (j = -dot)
    j = -dot
    p1.vx += j * nx
    p1.vy += j * ny
    p2.vx -= j * nx
    p2.vy -= j * ny

    # 겹침 보정
    overlap = min_dist - dist
    p1.x -= overlap * 0.5 * nx
    p1.y -= overlap * 0.5 * ny
    p2.x += overlap * 0.5 * nx
    p2.y += overlap * 0.5 * ny

    return True


def create_particles(n: int) -> list[Particle]:
    """겹치지 않도록 파티클을 배치."""
    particles: list[Particle] = []
    margin = PARTICLE_RADIUS + 5

    for _ in range(n):
        placed = False
        for _ in range(2000):
            x = random.uniform(margin, WIDTH - margin)
            y = random.uniform(margin, HEIGHT - 50 - margin)

            overlapping = any(
                math.hypot(x - p.x, y - p.y) < PARTICLE_RADIUS * 2 + 2
                for p in particles
            )
            if not overlapping:
                particles.append(Particle(x, y))
                placed = True
                break

        if not placed:
            # 빈 자리를 못 찾으면 그냥 추가 (겹쳐도 허용)
            x = random.uniform(margin, WIDTH - margin)
            y = random.uniform(margin, HEIGHT - 50 - margin)
            particles.append(Particle(x, y))

    return particles


def ask_particle_count() -> int:
    """tkinter 다이얼로그로 파티클 수를 입력받음."""
    root = tk.Tk()
    root.withdraw()
    count = simpledialog.askinteger(
        "ParticleMove",
        "파티클(원) 개수를 입력하세요:\n(1 ~ 200)",
        parent=root,
        minvalue=1,
        maxvalue=200,
        initialvalue=20,
    )
    root.destroy()
    return count if count else 20


def draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    num_particles: int,
    collision_count: int,
    fps: float,
):
    """하단 HUD 바 렌더링."""
    bar_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
    pygame.draw.rect(screen, (20, 20, 35), bar_rect)
    pygame.draw.line(screen, (60, 60, 90), (0, HEIGHT - 50), (WIDTH, HEIGHT - 50), 1)

    texts = [
        f"파티클: {num_particles}개",
        f"충돌: {collision_count}회",
        f"FPS: {int(fps)}",
        "R: 리셋   ESC: 종료",
    ]
    x = 20
    for text in texts:
        surf = font.render(text, True, (170, 170, 200))
        screen.blit(surf, (x, HEIGHT - 33))
        x += surf.get_width() + 40


def main():
    num_particles = ask_particle_count()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"ParticleMove  —  파티클 {num_particles}개")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Segoe UI", 17)

    particles = create_particles(num_particles)
    collision_count = 0

    running = True
    while running:
        # ── 이벤트 처리 ──────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    particles = create_particles(num_particles)
                    collision_count = 0

        # ── 물리 업데이트 ─────────────────────────────────────
        for p in particles:
            p.update()

        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                if resolve_collision(particles[i], particles[j]):
                    collision_count += 1

        # ── 렌더링 ────────────────────────────────────────────
        screen.fill(BG_COLOR)

        for p in particles:
            p.draw(screen)

        draw_hud(screen, font, num_particles, collision_count, clock.get_fps())

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
