<div align="center">
  <p>
    <a align="center" href="" target="_blank">
      <img
        width="100%"
        src="https://telekinesis-public-assets.s3.us-east-1.amazonaws.com/Telekinesis+Banner.png"
      >
    </a>
  </p>

  <br>

  [Telekinesis Examples](https://github.com/telekinesis-ai/telekinesis-examples) | [Telekinesis Data](https://gitlab.com/telekinesis/telekinesis-data)
  <br>

[![PyPI version](https://img.shields.io/pypi/v/telekinesis-datatypes)](https://pypi.org/project/telekinesis-datatypes/)
[![License](https://img.shields.io/pypi/l/telekinesis-datatypes)](https://pypi.org/project/telekinesis-datatypes/)
[![Python versions](https://img.shields.io/pypi/pyversions/telekinesis-datatypes)](https://pypi.org/project/telekinesis-datatypes/)

</div>


# Telekinesis Datatypes

Telekinesis Datatypes is a core library providing canonical, strongly typed data structures for robotics and computer vision within the Telekinesis ecosystem.
It includes:
- 3D data types: point clouds, meshes, transforms, and geometric primitives
- 2D data types: images, bounding boxes, masks, and pixel-space geometry
- Standardized representations for common perception and geometry formats
- Efficient serialization and deserialization for reliable data exchange

This library is used internally by the Telekinesis SDK as the foundation for data exchange across perception, planning, and learning components.

## Installation

You will need to have `Python 3.11` or higher set up to use the Telekinesis Datatypes Package.

Run the following command to install the Telekinesis Datatypes Package.

```bash
pip install telekinesis-datatypes
```

## Minimal Usage Example

```python
import numpy as np
from datatypes import datatypes

# Create Rgba32 colors for R, G, B
red = datatypes.Rgba32([255, 0, 0, 255])
green = datatypes.Rgba32([0, 255, 0, 255])
blue = datatypes.Rgba32([0, 0, 255, 255])

print(f"Red color (packed uint32): {red.rgba}")
print(f"Green color (packed uint32): {green.rgba}")
print(f"Blue color (packed uint32): {blue.rgba}")

# Use __int__() to convert to integer
red_int = int(red)

print(f"Red as int: {red_int}")
print(f"Direct comparison: int(red) == red.rgba: {red_int == red.rgba}")
```

Expected output:
```bash
Red color (packed uint32): 4278190335
Green color (packed uint32): 16711935
Blue color (packed uint32): 65535
Red as int: 4278190335
Direct comparison: int(red) == red.rgba: True
```

## Resources

- Examples  
  Runnable usage examples for Telekinesis Datatypes: [Telekinesis Examples](https://github.com/telekinesis-ai/telekinesis-examples) (see examples/datatypes_examples.py)

- Documentation   
  Full API reference and datatype descriptions: [Datatypes Documentation](https://telekinesis.gitlab.io/telekinesis/datatypes/datatypes/)

  Complete documentation: [Telekinesis Docs](https://docs.telekinesis.ai)


## Support

For issues and questions:
- Create an [issue](https://github.com/telekinesis-ai/telekinesis-examples/issues) in the GitHub repository.
- Contact the Telekinesis development team.

<p align="center">
  <a href="https://github.com/telekinesis-ai">GitHub</a>
  &nbsp;•&nbsp;
  <a href="https://www.linkedin.com/company/telekinesis-ai/">LinkedIn</a>
  &nbsp;•&nbsp;
  <a href="https://x.com/telekinesis_ai">X</a>
  &nbsp;•&nbsp;
  <a href="https://discord.gg/7NnQ3bQHqm">Discord</a>
</p>
