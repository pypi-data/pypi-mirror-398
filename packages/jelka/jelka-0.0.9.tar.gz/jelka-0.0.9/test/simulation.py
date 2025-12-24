from numpy import array, cos, sin, random


def proj(point, cam):
    dy = point[1][0] - cam[1]
    if dy != 0:
        return ((point[0][0] - cam[0]) / dy, (point[2][0] - cam[2]) / dy, dy)
    else:
        return (0, 0, 1)


def rotation(phi, tau):
    xy = array([[cos(phi), -sin(phi), 0], [sin(phi), cos(phi), 0], [0, 0, 1]])
    yz = array([[1, 0, 0], [0, cos(tau), -sin(tau)], [0, sin(tau), cos(tau)]])
    return yz @ xy


def random_tree(n=300, origin=(0, 0, 0), height=200, max_width=120, min_width=60):
    count = 0
    while count < n:
        x = random.uniform(-max_width, max_width)
        y = random.uniform(-max_width, max_width)
        h = random.uniform(0, height)
        max_w = (height - h) / height * max_width
        min_w = max(max_w - max_width + min_width, 0)
        if min_w**2 <= x**2 + y**2 <= max_w**2:
            count += 1
            yield (x + origin[0], y + origin[1], origin[2] + h)


def draw_lucka(pygame, lucka, screen, size, color, scale):
    w, h = pygame.display.get_surface().get_size()
    pygame.draw.circle(screen, color, (w * lucka[0] * scale + w // 2, (-w * lucka[1] * scale + h // 2)), size + 3)


def draw_line(pygame, p1, p2, screen, color, scale):
    w, h = pygame.display.get_surface().get_size()
    pygame.draw.line(
        screen,
        color,
        (w * p1[0] * scale + w // 2, (-w * p1[1] * scale + h // 2)),
        (w * p2[0] * scale + w // 2, (-w * p2[1] * scale + h // 2)),
    )


class Simulation:
    def __init__(self, smreka=None) -> None:
        self.running = True
        self.phi, self.tau = 0, 0

        if smreka is None:
            self.smreka = {i: pos for i, pos in enumerate(random_tree())}
        else:
            self.smreka = smreka.copy()
        self.points = {i: array([[p[0]], [p[1]], [p[2]]]) for i, p in self.smreka.items()}
        self.colors = {i: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for i in self.smreka}

        self.scale = 1
        self.camera = (0, -500, 100)

    def set_colors(self, colors):
        if not self.running:
            raise InterruptedError("Simulation stopped.")
        try:
            for i, c in colors.items():
                assert all(isinstance(c[i], int) for i in range(3))
                assert all(0 <= c[i] <= 255 for i in range(3))
        except AssertionError:
            self.running = False
            raise ValueError(f"Wrong shape for color: ({i}: {c})") from None  # type: ignore
        self.colors = {pk: tuple(color) for pk, color in colors.items()}

    def init(self):
        import pygame

        self.pygame = pygame
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        pygame.mouse.get_rel()

    def frame(self):
        pygame = self.pygame
        self.w, self.h = pygame.display.get_surface().get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEWHEEL:
                self.camera = (self.camera[0], self.camera[1] + event.y * 5, self.camera[2])
            elif event.type == pygame.VIDEORESIZE:
                old_surface_saved = self.screen
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.screen.blit(old_surface_saved, (0, 0))
                del old_surface_saved

        mouse_pressed = pygame.mouse.get_pressed(num_buttons=3)
        key_pressed = pygame.key.get_pressed()
        if mouse_pressed[0] and not key_pressed[pygame.K_LCTRL] and not key_pressed[pygame.K_RCTRL]:
            dphi, dtau = pygame.mouse.get_rel()
            self.phi += dphi / 100
            self.tau += dtau / 100 if dphi == 0 or dtau / dphi > 0.69 else 0
        elif mouse_pressed[0] and (key_pressed[pygame.K_LCTRL] or key_pressed[pygame.K_RCTRL]):
            dx, dz = pygame.mouse.get_rel()
            self.camera = (self.camera[0] - dx / 2, self.camera[1], self.camera[2] + dz / 2)
        else:
            pygame.mouse.get_rel()

        self.screen.fill("black")

        r = rotation(self.phi, self.tau)
        prev = None
        projected = {i: proj(r @ p, self.camera) for i, p in self.points.items()}

        for _, p in sorted(projected.items()):
            if p[2] > 0 and prev and prev[2] > 0:
                draw_line(pygame, p, prev, self.screen, (10, 10, 10), self.scale)
            prev = p

        for i, p in projected.items():
            c = self.colors.get(i, (0, 0, 0))
            draw_lucka(pygame, (p[0], p[1]), self.screen, max(20 / p[2], 1), c, self.scale)

        p = proj(r @ array([[0], [0], [0]]), self.camera)
        draw_lucka(pygame, (p[0], p[1]), self.screen, max(20 / p[2], 1), (0, 255, 0), self.scale)
        pygame.display.flip()
        self.clock.tick(60)  # limits FPS to 60

    def quit(self):
        self.running = False
        self.pygame.quit()
