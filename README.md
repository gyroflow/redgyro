## redgyro
# This script is no longer necessary. R3D gyro parsing, both sync and async is implemented in main Gyroflow natively already.

Rough batch converter script to generate `.gcsv` gyro log files from RED `.R3D` for Gyroflow stabilization (https://github.com/gyroflow/gyroflow)

Plan is to properly integrate the functionality with Gyroflow and [Telemetry-parser](https://github.com/AdrianEddy/telemetry-parser) soon^tm, so this is just to have the test code somewhere available for now.

Requires redline installed (bundled with REDCINE-X PRO on MacOS/Windows and standalone on Linux) and preferably added to the PATH. Download from: https://www.red.com/download Note: Latest release may not work with async metadata from e.g. the RED V-Raptor.

Windows installation assumed to be at `C:/Program Files/REDCINE-X PRO One-Off 64-bit/redline` and `C:/Program Files/REDCINE-X PRO 64-bit/redline`. Modify `redline_path` if needed.

## Usage

* Save `redgyro.py` somewhere and run with:
* For single files: `python path\to\redgyro.py <filename.R3D>`
* For all `.R3D` files in working dir: `python path\to\redgyro.py --all`
* On MacOS and Linux, use `python3`

This will generate `.gcsv` files that can be loaded as gyro logs in Gyroflow.
