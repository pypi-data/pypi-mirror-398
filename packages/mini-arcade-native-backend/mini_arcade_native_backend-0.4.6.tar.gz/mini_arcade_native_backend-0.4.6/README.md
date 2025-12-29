# mini-arcade-native-backend

Native SDL2 backend for **mini-arcade-core**, implemented in C++ with `SDL2` + `pybind11`
and exposed to Python as a backend that plugs into your mini-arcade game framework.

The goal of this repo is to provide a **native window + input + drawing layer** while
keeping all game logic in Python (via `mini-arcade-core`).

- C++ (`SDL2` + `pybind11`) ⇒ `_native` extension module
- Python adapter ⇒ `NativeBackend` implementing `mini_arcade_core.backend.Backend`

---

## Features (current)

- Opens an SDL window from Python
- Basic event polling (Quit, KeyDown, KeyUp) mapped to `Event` / `EventType` in mini-core
- Simple rendering:
  - `begin_frame()` / `end_frame()`
  - `draw_rect(x, y, w, h)` (filled rectangle)
- Example script that shows a moving rectangle and exits on **ESC** or window close

This is intentionally minimal and intended as a foundation for adding sprites, textures,
audio, etc.

---

## Repository layout

```text
mini-arcade-native-backend/
├─ cpp/
│  ├─ engine.h                        # C++ Engine class (SDL wrapper)
│  ├─ engine.cpp
│  └─ bindings.cpp                    # pybind11 bindings for Engine / Event / EventType
├─ src/
│  └─ mini_arcade_native_backend/
│     ├─ __init__.py                  # Python adapter (NativeBackend)
│     └─ ...                          # (future helpers)
├─ examples/
│  └─ native_backend_demo.py          # example using NativeBackend directly
├─ CMakeLists.txt                     # C++ build (pybind11 + SDL2)
└─ pyproject.toml                     # Python package & build config (scikit-build-core)
```

---

## Install modes

There are **two ways** to consume this backend:

1. **From PyPI (recommended for players / game users)**  
   Prebuilt wheels for your platform (no C++ toolchain or vcpkg needed).
2. **From source (for contributors / engine dev)**  
   Build the C++ extension locally using CMake + vcpkg.

---

## 1. Using the backend from PyPI (no C++ build)

Once wheels are published, you can simply do:

```bash
pip install mini-arcade-core
pip install mini-arcade-native-backend
```

And in your game:

```python
from mini_arcade_core import Game, GameConfig, Scene
from mini_arcade_core.backend import EventType
from mini_arcade_native_backend import NativeBackend

class MyScene(Scene):
    def handle_event(self, event):
        if event.type == EventType.KEYDOWN and event.key == 27:  # ESC
            self.game.quit()

    def update(self, dt: float):
        ...

    def draw(self, backend):
        backend.draw_rect(100, 100, 200, 150)

config = GameConfig(
    width=800,
    height=600,
    title="Mini Arcade + Native SDL2",
    backend_factory=lambda: NativeBackend(),
)

game = Game(config)
scene = MyScene(game)
game.run(scene)
```

For normal users of your games, this is the ideal path: **no vcpkg**, no CMake, no compiler.

---

## 2. Developing / building from source

If you want to work on the native backend itself (C++ + Python), you’ll build the extension
locally. For that, you need a C++ toolchain, CMake, and vcpkg.

### 2.1. System requirements

- **OS**: Windows 10 or later (current dev setup)
- **Compiler**: MSVC via Visual Studio Build Tools or Visual Studio 2022
  - Install the *“Desktop development with C++”* workload
- **CMake**: 3.16+
- **Python**: 3.9–3.11 (matching your `mini-arcade-core` version)
- **vcpkg**: for `SDL2` and `pybind11`
- (Optional but nice) **virtual environment** / Poetry for Python deps

### 2.2. vcpkg + C++ libraries

This project uses [vcpkg](https://github.com/microsoft/vcpkg) to manage C++ dependencies.

#### Clone and bootstrap vcpkg

```powershell
cd C:\Users\<your_user>\work

git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
```

#### Install dependencies via vcpkg

```powershell
# From the vcpkg folder:
.\vcpkg.exe install sdl2 pybind11
```

You only need to do this once per machine (unless you wipe `vcpkg` or add new libraries).

### 2.3. Linking CMake to vcpkg

For builds in this repo, set the toolchain environment variable once per shell:

```powershell
$env:CMAKE_TOOLCHAIN_FILE = "C:/Users/<your_user>/work/vcpkg/scripts/buildsystems/vcpkg.cmake"
```

(Adjust the path if you cloned `vcpkg` somewhere else.)

---

## 3. Building & installing the package from source

This project uses **[scikit-build-core](https://github.com/scikit-build/scikit-build-core)** as
the build backend, which lets `pip` drive CMake for you.

From the repo root (`mini-arcade-native-backend/`):

### 3.1. Editable install (dev mode)

```powershell
# Activate your virtualenv (or use Poetry's venv)
# Then, with CMAKE_TOOLCHAIN_FILE set:

pip install -e .
```

What this does:

- Runs CMake via scikit-build-core
- Builds the `_native` extension
- Installs the package in editable mode, so changes to `src/` are picked up immediately

After this, you can test in Python:

```python
>>> from mini_arcade_native_backend import NativeBackend
>>> backend = NativeBackend()
>>> backend.init(800, 600, "Hello from native backend")
```

### 3.2. Building wheels / sdist

To build distributable artifacts:

```powershell
python -m build
```

This will produce:

```text
dist/
  mini-arcade-native-backend-0.1.0-*.whl
  mini-arcade-native-backend-0.1.0.tar.gz
```

Those wheels can be uploaded to PyPI (e.g. via `twine`) and installed by anyone with:

```bash
pip install mini-arcade-native-backend
```

End users installing the wheel **do not** need vcpkg or a compiler.

---

## 4. Python usage & example

The package exposes a `NativeBackend` that implements the `Backend` protocol from
`mini-arcade-core` and wraps the C++ `Engine` underneath.

```python
from mini_arcade_native_backend import NativeBackend
from mini_arcade_core.backend import EventType
```

A small standalone demo is provided under `examples/`:

```bash
python examples/native_backend_demo.py
```

That demo:

- opens an 800×600 window,
- moves a rectangle horizontally,
- exits on ESC or window close.

(When installed via `pip install -e .`, you can run this from the repo root.)

---

## 5. How it fits into mini-arcade-core

On the C++ side (`cpp/engine.h` / `cpp/engine.cpp`):

- `mini::Engine` wraps SDL:
  - `init(width, height, title)`
  - `begin_frame()` / `end_frame()`
  - `draw_rect(x, y, w, h)`
  - `poll_events()` → `std::vector<Event>`
- `EventType` and `Event` are simple types mapping SDL events to something Python-friendly.

On the Python side (`src/mini_arcade_native_backend/__init__.py`):

- The compiled C++ module is imported as `._native` (installed into the same package)
- `NativeBackend` implements `mini_arcade_core.backend.Backend`:
  - `init(width, height, title)` → `_native.Engine.init(...)`
  - `poll_events()` → converts `_native.Event` to core `Event`
  - `begin_frame()` / `end_frame()` → pass-through
  - `draw_rect(x, y, w, h)` → pass-through

A minimal integration with mini-arcade-core:

```python
from mini_arcade_core import Game, GameConfig, Scene
from mini_arcade_core.backend import Backend, Event, EventType
from mini_arcade_native_backend import NativeBackend

class MyScene(Scene):
    def handle_event(self, event: Event) -> None:
        if event.type == EventType.KEYDOWN and event.key == 27:  # ESC
            self.game.quit()

    def update(self, dt: float) -> None:
        ...

    def draw(self, backend: Backend) -> None:
        backend.draw_rect(100, 100, 200, 150)

config = GameConfig(
    width=800,
    height=600,
    title="Mini Arcade + Native SDL2",
    backend_factory=lambda: NativeBackend(),
)

game = Game(config)
scene = MyScene(game)
game.run(scene)
```

---

## 6. Troubleshooting

- **`ModuleNotFoundError: No module named '_native'`**  
  - Ensure `pip install -e .` (or `python -m build`) completed successfully.
  - Confirm that the wheel contains `mini_arcade_native_backend/_native.*.pyd`.

- **DLL load error / Python version mismatch**  
  - Make sure you are building and running with the **same Python version**.
  - If you have multiple Python versions installed, ensure the one used by
    `pip install -e .` is the one used to run your game.

- **CMake can’t find SDL2 or pybind11**  
  - Confirm vcpkg is installed and `sdl2` + `pybind11` are installed via vcpkg.
  - Make sure `CMAKE_TOOLCHAIN_FILE` is set correctly in your shell.

---

## 7. Roadmap

- Configurable clear color (per scene / per game)
- Basic texture / sprite support
- Simple audio playback
- CI that builds wheels for Windows and uploads to PyPI
- A `mini-arcade-core` example project that uses this backend as the default renderer
