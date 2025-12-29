from __future__ import annotations

import time

from mini_arcade_core.backend import EventType

from mini_arcade_native_backend import NativeBackend


def main():
    backend = NativeBackend()
    backend.init(800, 600, "Mini Arcade Native Backend Demo")

    running = True

    # Simple rectangle state
    x = 100
    y = 100
    w = 200
    h = 150
    vx = 150  # pixels per second, horizontally

    last_time = time.perf_counter()

    while running:
        now = time.perf_counter()
        dt = now - last_time
        last_time = now

        # --- Handle events ---
        for ev in backend.poll_events():
            # Window close (X button)
            if ev.type == EventType.QUIT:
                running = False

            # ESC key to quit
            elif ev.type == EventType.KEYDOWN and ev.key == 27:  # 27 = ESC
                running = False

        # --- Update "game" state ---
        x += int(vx * dt)

        # Wrap rectangle when it goes off the right edge
        if x > 800:
            x = -w

        # --- Render ---
        backend.begin_frame()
        backend.draw_rect(x, y, w, h)
        backend.end_frame()

        # tiny sleep to avoid maxing out CPU
        time.sleep(0.001)


if __name__ == "__main__":
    main()
