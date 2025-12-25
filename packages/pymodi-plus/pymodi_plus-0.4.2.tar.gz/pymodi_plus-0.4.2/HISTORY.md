History
==

0.4.2 (2025-12-22)
--
* Feature
1. Add RGB raw value properties for Env module v2.x+
   - New properties: `raw_red`, `raw_green`, `raw_blue`, `raw_white` (0-65535)
   - New property: `raw_rgb` tuple (raw_red, raw_green, raw_blue, raw_white)
2. Add `set_rgb_mode(mode, duration)` method for Env module
   - RGB mode constants: `RGB_MODE_AMBIENT`, `RGB_MODE_ON`, `RGB_MODE_DUALSHOT`
3. Code style fixes for flake8 compatibility

0.4.0 (2025-11-19)
--
* Feature
1. Add RGB support for Env module v2.x+
   - New properties: `red`, `green`, `blue`, `white`, `black` (0-100%)
   - New property: `rgb` - returns tuple (red, green, blue)
   - New property: `color_class` (0-5: unknown/red/green/blue/white/black)
   - New property: `brightness` (0-100%)
   - Automatic version detection via `_is_rgb_supported()` method
   - Raises `AttributeError` when accessing RGB properties on v1.x modules
2. Enhanced GitHub Actions workflows
   - Support Python 3.8-3.13 across all platforms
   - Platform-specific compatibility fixes (macOS, Windows)
   - Improved CI/CD with conditional linting (flake8 for 3.8-3.11, ruff for 3.12+)

* Tests
1. Add 31 new RGB-related tests
   - Version compatibility tests
   - RGB property tests
   - Data type validation tests
   - Total: 94 tests (all passing)

* Documentation
1. Complete RGB feature documentation
2. GitHub Actions compatibility guides
3. Branch protection setup guide

0.3.0 (2023-01-19)
--
* Feature
1. Add `draw_dot` function on display module

* Patch
1. Fix `write_text` function error on display module if text length is 23
2. Change module constructor argument from uuid to id

0.2.1 (2022-12-02)
--
* Patch
1. Refactor `write_text` input type on display module

0.2.0 (2022-12-02)
--
* Feature
1. Refactor getter/setter for each MODI+ module

0.1.1 (2022-11-23)
--
* Feature
1. Change python minimum version to 3.7

0.1.0 (2022-11-22)
--
* Feature
1. Add creation examples (brush, dodge)
2. Add network, battery module functions
3. Fix `play_music` function on speaker module
4. Add preset resource on speaker and display module
5. Add search module time and timeout exception

0.0.2 (2022-11-18)
--
* Feature
1. Change python minimum version to 3.9

0.0.1 (2022-11-15)
--
* Release initial version of the package on in-house GitHub
