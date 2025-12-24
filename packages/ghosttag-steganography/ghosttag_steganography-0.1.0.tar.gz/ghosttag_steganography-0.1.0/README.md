# GhostTag

**GhostTag** is an advanced steganography library designed for **lossy environments**. unlike standard LSB tools that break instantly, GhostTag uses Reed-Solomon error correction to ensure your hidden data survives partial corruption.

## Features
* **Reed-Solomon Error Correction:** Data survives up to 20% pixel corruption.
* **Header Protection:** Metadata is protected separately to prevent "dead headers."
* **Seed-Based Encryption:** Data is scattered randomly based on a seed password.
* **Auto-Safety:** Automatically forces PNG output to prevent accidental JPEG data loss.

## Installation

```bash
pip install ghosttag

```

## Configuration Guide

When initializing `GhostTag`, you can tune the parameters for your specific needs:

| Parameter | Default | Description |
| --- | --- | --- |
| `redundancy` | `20` | Controls robustness. Higher numbers = more resistance to damage, but less total space for text. |
| `seed` | `42` | The "password" for the data distribution. If the receiver uses the wrong seed, they cannot find the data. |

## Important Limitations
1. **Output Format:** The library forces the output to be **PNG**. You cannot save steganography data into a JPEG file because JPEG compression alters pixel values, which destroys the hidden message immediately.
2. **Capacity:** Because of the error correction overhead, `GhostTag` can store less data than raw LSB tools. If your message is too long for the image, the library will raise a `ValueError`.

## Usage
```python
from ghosttag import GhostTag

# Initialize with a "password" seed
ghost = GhostTag(redundancy=20, seed=1337)

# Embed a secret
ghost.embed("input_image.jpg", "This is a secret message!", "output_image.png")

# Extract a secret
success, message = ghost.extract("output_image.png")

if success:
    print(f"Found secret: {message}")
else:
    print("Data corrupted or no secret found.")

```

## License
MIT License

