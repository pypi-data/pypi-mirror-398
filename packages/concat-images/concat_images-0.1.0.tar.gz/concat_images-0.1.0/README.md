# concat-images

Combine multiple images into one with customizable orientation, spacing, and alignment.

## Installation

```bash
pip install concat-images
```

## Python Usage

```python
from concat_images import load_images, concatenate_images

images = load_images(['a.png', 'b.png', 'c.png'])
result = concatenate_images(images, orientation='horizontal', spacing=10, alignment='center')
result.save('output.png')

# With custom background (transparent)
result = concatenate_images(images, 'vertical', 0, 'center', background=(0, 0, 0, 0))
```

## CLI Usage

```bash
concat-images output.png img1.png img2.png [img3.png ...]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --orientation` | `vertical` or `horizontal` | `vertical` |
| `-s, --space` | Pixels between images | `0` |
| `-a, --align` | `begin`, `center`, or `end` | `center` |
| `-b, --background` | Background color as `R,G,B`, `R,G,B,A`, or `transparent` | `255,255,255,255` |

### Example

```bash
concat-images result.png a.png b.png c.png -o horizontal -s 10 -a center
```

## Development

```bash
git clone https://github.com/mrpesho/concat-images.git
cd concat-images
pip install -e .[dev]
pytest
```
