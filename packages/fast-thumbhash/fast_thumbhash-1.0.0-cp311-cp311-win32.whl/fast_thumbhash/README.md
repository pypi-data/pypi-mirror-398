# fast_thumbhash

A Python package with Rust bindings (PyO3, maturin) to the official thumbhash crate.

## Usage Example
```python
from fast_thumbhash import rgba_to_thumb_hash, thumb_hash_to_rgba
from PIL import Image

img = Image.open('example.png').convert('RGBA')
thash = rgba_to_thumb_hash(img)
restored = thumb_hash_to_rgba(thash)
```

See the main README for more details.
