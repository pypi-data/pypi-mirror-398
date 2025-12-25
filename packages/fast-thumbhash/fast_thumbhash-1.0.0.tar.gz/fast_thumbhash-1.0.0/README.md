# fast_thumbhash

A fast Python package for [ThumbHash](https://github.com/evanw/thumbhash) image encoding/decoding using Rust bindings (PyO3, maturin) to the official `thumbhash` crate.

fast_thumbhash is 60.5x faster than the pure Python implementations I tested:

```
28.13854099076707 ms (thumbhash)
0.46491601096931845 ms (fast-thumbhash - this package)
```

`thumbhash-python` was also taking the same time range as `thumbhash` (27 - 35 ms).

## Features
- Exposes `rgba_to_thumb_hash`, `thumb_hash_to_rgba`, `thumb_hash_to_average_rgba`, `thumb_hash_to_approximate_aspect_ratio`.
- Supports raw RGBA bytes and Pillow Image (Pillow is optional).

## Installation

```sh
pip install git+https://github.com/sitatec/fast_python_thumbhash.git
```

Build from source using maturin:

```sh
maturin develop
```

## Usage Example
```python
from fast_thumbhash import rgba_to_thumb_hash, thumb_hash_to_rgba
from PIL import Image

img = Image.open('example.png').convert('RGBA')
thash = rgba_to_thumb_hash(img)
restored = thumb_hash_to_rgba(thash)
```

## License
MIT
