# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.6] - 2025-12-26

### Fixed
- update mini-arcade-core dependency version and improve import statements

### Other
- Merge branch 'release/0.4' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.4

## [0.4.5] - 2025-12-16

### Added
- implement font caching and update draw_text and measure_text methods to support dynamic font sizes

## [0.4.4] - 2025-12-16

### Added
- add measure_text method to Engine and expose it in NativeBackend
- add alpha handling methods and refactor color extraction in NativeBackend
- update draw_rect and draw_text methods to support alpha channel in color

### Other
- Merge branch 'release/0.4' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.4
- Merge branch 'release/0.4' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.4

## [0.4.3] - 2025-12-16

### Added
- add alpha handling methods and refactor color extraction in NativeBackend
- update draw_rect and draw_text methods to support alpha channel in color

### Other
- Merge branch 'release/0.4' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.4

## [0.4.2] - 2025-12-16

### Added
- enhance event handling by adding key_code to event mapping in NativeBackend

## [0.4.1] - 2025-12-15

### Added
- extend event handling with additional mouse and window events in engine and bindings
- enhance font handling by returning font ID and updating draw_text signature

### Fixed
- update mini-arcade-core dependency version to ensure compatibility

### Other
- Merge release/0.3 into develop

## [0.4.0] - 2025-12-15

### Added
- extend event handling with additional mouse and window events in engine and bindings
- enhance font handling by returning font ID and updating draw_text signature

### Fixed
- update mini-arcade-core dependency version to ensure compatibility

### Other
- Merge release/0.3 into develop

## [0.3.3] - 2025-12-05

### Other
- docs: improve docstring formatting for capture_frame method in NativeBackend
- Merge branch 'release/0.3' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.3

## [0.3.2] - 2025-12-05

### Added
- add draw_rect_rgba method to Engine for RGBA rectangle drawing and update Python bindings
- add capture_frame method to Engine and expose it in Python bindings
- add clear color customization and update draw_rect method

### Other
- Merge branch 'release/0.3' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.3
- Merge branch 'release/0.3' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.3

## [0.3.1] - 2025-12-05

### Added
- add capture_frame method to Engine and expose it in Python bindings
- add clear color customization and update draw_rect method

### Other
- Merge branch 'release/0.3' of https://github.com/alexsc6955/mini-arcade-native-backend into release/0.3

## [0.3.0] - 2025-12-05

### Added
- add text rendering support with SDL2_ttf integration

### Other
- Merge pull request #7 from alexsc6955/feature/text_support
- Merge release/0.2 into develop

## [0.2.3] - 2025-12-04

- Internal changes only.

## [0.2.2] - 2025-12-04

- Internal changes only.

## [0.2.1] - 2025-12-04

### Other
- Merge pull request #2 from alexsc6955/main
- Merge pull request #1 from alexsc6955/feature/ci_cd
- Implement CI workflow for automated testing and linting
- Add SDL2.dll search path for Windows when using vcpkg
- Initial Commit

## [0.2.0] - 2025-12-04

### Other
- Merge pull request #2 from alexsc6955/main
- Merge pull request #1 from alexsc6955/feature/ci_cd
- Implement CI workflow for automated testing and linting
- Add SDL2.dll search path for Windows when using vcpkg
- Initial Commit

## [0.2.0] - 2025-12-03

### Added

- Initial documented release.
