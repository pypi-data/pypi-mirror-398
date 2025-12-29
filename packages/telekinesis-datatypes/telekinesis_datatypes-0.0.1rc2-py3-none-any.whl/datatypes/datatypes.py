import pathlib
import numpy as np
from numpy import typing
from typing import Dict, Optional, Sequence, Any, Union, cast, Literal
import pyarrow as pa
from loguru import logger
import math
import enum

from datatypes import converters
from collections import defaultdict

# ---------------- Python datatypes ----------------

# Bool
class Bool:
	"""
	A single boolean value.

	Attributes:
		value (bool): The boolean value.

	Args:
		value (bool): The boolean value.
	"""
	telekinesis_datatype = "datatypes.datatypes.Bool"

	def __init__(self, value: bool):

		# Type checks
		if not isinstance(value, bool):
			raise TypeError("value must be a bool")
		
		self.value = value
		
		# Field names for serialization
		self._field_names = ["value"]
		
		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"value": pa.bool_(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Bool instance to a dict of PyArrow arrays.
		
		Returns a single-row array for the boolean value.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Bool")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# Wrap field_value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Bool":
		"""
		Reconstruct Bool from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			value: length-1 array containing a single boolean
		"""

		# 1. value (required)
		if "value" not in columns:
			raise KeyError("Missing required column 'value'")
		
		pa_value = columns["value"]
		if len(pa_value) != 1:
			raise ValueError(f"'value' must have exactly 1 row, got {len(pa_value)}")
		
		value = bool(pa_value[0].as_py())
		return cls(value=value)

# Int32
class Int:
	"""
	A single integer (32-bit signed).

	Attributes:
		value (int): The integer value.

	Args:
		value (int): The integer value.
	"""
	telekinesis_datatype = "datatypes.datatypes.Int"
	
	def __init__(self, value: int):
		# Type checks
		if not isinstance(value, int):
			raise TypeError("value must be an int")
		
		self.value = value

		# Field names for serialization
		self._field_names = ["value"]
		
		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"value": pa.int32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Int instance to a dict of PyArrow arrays.
		
		Returns a single-row array for the integer value.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Int")
			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			# Wrap field_value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Int":
		"""
		Reconstruct Int from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			value: length-1 array containing a single integer
		"""

		# 1. value (required)
		if "value" not in columns:
			raise KeyError("Missing required column 'value'")
		
		pa_value = columns["value"]
		if len(pa_value) != 1:
			raise ValueError(f"'value' must have exactly 1 row, got {len(pa_value)}")
		
		value = int(pa_value[0].as_py())
		return cls(value=value)

# Float
class Float:
	"""
	A single-precision 32-bit IEEE 754 floating point number.

	Attributes:
		value (float): The float value.

	Args:
		value (float): The float value.
	"""
	telekinesis_datatype = "datatypes.datatypes.Float"

	def __init__(self, value: float | int):
		# Type checks
		if not isinstance(value, (float, int)):
			raise TypeError("value must be a float or int")
		if not isinstance(value, (float, int)):
			raise TypeError("value must be a float")
		
		self.value = float(value)

		# Field names for serialization
		self._field_names = ["value"]
		
		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"value": pa.float32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Float instance to a dict of PyArrow arrays.
		
		Returns a single-row array for the float value.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Float")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# Wrap field_value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Float":
		"""
		Reconstruct Float from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			value: length-1 array containing a single float
		"""

		# 1. value (required)
		if "value" not in columns:
			raise KeyError("Missing required column 'value'")
		
		pa_value = columns["value"]
		if len(pa_value) != 1:
			raise ValueError(f"'value' must have exactly 1 row, got {len(pa_value)}")
		
		value = float(pa_value[0].as_py())
		return cls(value=value)

# String (UTF-8)
class String:
	"""
	A string of text, encoded as UTF-8.

	Attributes:
		value (str): The string value.

	Args:
		value (str): The string value.
	"""
	telekinesis_datatype = "datatypes.datatypes.String"
	
	def __init__(self, value: str):
		# Type checks
		if not isinstance(value, str):
			raise TypeError("value must be a string")
		
		self.value = value

		# Field names for serialization
		self._field_names = ["value"]
		
		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"value": pa.string(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this String instance to a dict of PyArrow arrays.
		
		Returns a single-row array for the string value.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on String")
			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# Wrap field_value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "String":
		"""
		Reconstruct String from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			value: length-1 array containing a single string
		"""

		# 1. value (required)
		if "value" not in columns:
			raise KeyError("Missing required column 'value'")
		
		pa_value = columns["value"]
		if len(pa_value) != 1:
			raise ValueError(f"'value' must have exactly 1 row, got {len(pa_value)}")
		
		value = str(pa_value[0].as_py())
		return cls(value=value)

# ------------------  Geometric & Spatial Datatypes ------------------
# Bounding Box
class Boxes3D:
	"""
	3D bounding boxes with half-extents and optional center, rotations, and colors.

	Attributes:
		half_size (np.ndarray): The half-size of the box (shape (3,)).
		center (np.ndarray, optional): The center of the box (shape (3,)).
		colors (Rgba32ArrayLike, optional): The colors of the box.
		rotation_in_euler_angles (np.ndarray, optional): The rotation in Euler angles (shape (3,)).

	Args:
		half_size (np.ndarray): The half-size of the box (shape (3,)).
		center (np.ndarray, optional): The center of the box (shape (3,)).
		colors (Rgba32ArrayLike, optional): The colors of the box.
		rotation_in_euler_angles (np.ndarray, optional): The rotation in Euler angles (shape (3,)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Boxes3D"
	
	def __init__(self,
			  half_size: np.ndarray,
			  center: Optional[np.ndarray] = None,
			  colors: Optional["Rgba32ArrayLike"] = None,
			  rotation_in_euler_angles: Optional[np.ndarray] = np.array([0, 0, 0])):

		# Type checks
		if not isinstance(half_size, np.ndarray):
			raise TypeError("half_size must be a numpy ndarray")
		if not isinstance(center, (np.ndarray, type(None))):
			raise TypeError("center must be a numpy ndarray or None")
		if not isinstance(rotation_in_euler_angles, (np.ndarray, type(None))):
			raise TypeError("rotation_in_euler_angles must be a numpy ndarray or None")

		# Shape checks
		if half_size.ndim == 1:
			if half_size.shape != (3,):
				raise ValueError("half_size must be length-3 if 1D")
		elif half_size.ndim == 2 and half_size.shape == (1, 3):
			# Accept (1, 3) and flatten to (3,)
			half_size = half_size.reshape(3,)
		elif half_size.ndim == 2 and half_size.shape[1] == 3:
			pass  # OK: (N,3)
		else:
			raise ValueError("half_size must be shape (3,) or (N, 3)")

		if center is not None:
			if center.ndim == 1:
				if center.shape != (3,):
					raise ValueError("center must be length-3 if 1D")
			elif center.ndim == 2 and center.shape == (1, 3):
				# Accept (1, 3) and flatten to (3,)
				center = center.reshape(3,)
			elif center.ndim == 2 and center.shape[1] == 3:
				pass  # OK: (N,3)
			else:
				raise ValueError("center must have shape (3,) if provided, not "
							 f"{center.shape}")

		if rotation_in_euler_angles is not None:
			if rotation_in_euler_angles.ndim == 1:
				if rotation_in_euler_angles.shape != (3,):
					raise ValueError("rotation_in_euler_angles must be length-3 if 1D")
			elif rotation_in_euler_angles.ndim == 2 and rotation_in_euler_angles.shape == (1, 3):
				# Accept (1, 3) and flatten to (3,)
				rotation_in_euler_angles = rotation_in_euler_angles.reshape(3,)
			elif rotation_in_euler_angles.ndim == 2 and rotation_in_euler_angles.shape[1] == 3:
				pass  # OK: (N,3)
			else:
				raise ValueError("rotation_in_euler_angles must have shape (3,) if provided, not "
							 f"{rotation_in_euler_angles.shape}")

		#TODO: Verify colors input
		num_positions = half_size.shape[0]
		if colors is None:
			self.colors = None
		else:
			# If colors is already a numpy array of uint32, use it directly
			if isinstance(colors, np.ndarray) and colors.dtype == np.uint32:
				self.colors = colors
			elif isinstance(colors, Rgba32):
				rgba_list = [int(colors)]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			elif isinstance(colors, Sequence) and not isinstance(colors, (str, bytes)):
				rgba_list = [int(Rgba32(c)) for c in colors]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			else:
				rgba_list = [int(Rgba32(colors))]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)

			if self.colors.shape[0] not in (1, num_positions):
				raise ValueError(
					f"colors length {self.colors.shape[0]} must be 1 or match {num_positions}"
				)
	
		# Members
		self.half_size = half_size
		self.center = center
		self.rotation_in_euler_angles = rotation_in_euler_angles

		# Field names for serialization
		self._field_names = ["half_size", "center", "colors", "rotation_in_euler_angles"]

		# Internal Arrow types map
		self.field_to_pyarrow_type_map = {
			"half_size": pa.list_(pa.float32(), 3),
			"center": pa.list_(pa.float32(), 3),
			"colors": pa.list_(pa.uint32()),
			"rotation_in_euler_angles": pa.list_(pa.float32(), 3),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Boxes3D instance to a dictionary of PyArrow arrays.
		
		Returns
		-------
		dict
			Dictionary where keys are field names and values are PyArrow arrays.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Boxes3D")

			field_value = getattr(self, field_name)

			# half_size is required
			if field_name == "half_size" and field_value is None:
				raise ValueError("Field 'half_size' cannot be None")
			
			# Skip None values for optional fields
			if field_value is None:
				continue
			
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Convert array values to PyArrow arrays (nested lists)
			try:
				if field_name in ("half_size", "center", "rotation_in_euler_angles"):
					# value is shape (3,) → we want ONE row with a 3-element list
					field_value_array = np.asarray(field_value, dtype=np.float32)
					field_value_list = [field_value_array.tolist()]               
					array_dict[field_name] = pa.array(field_value_list, type=pa_type)

				elif field_name == "colors":
					# colors is 1D array of uint32 → one row
					field_value_array = np.asarray(field_value, dtype=np.uint32)
					field_value_list = [field_value_array.tolist()]               # [[c0, c1, ...]]
					array_dict[field_name] = pa.array(field_value_list, type=pa_type)

				else:
					raise ValueError(f"Unhandled field '{field_name}'")

			except Exception as e:
				raise ValueError(f"Error converting field '{field_name}' to PyArrow array: {e}")
		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Boxes3D":
		"""
		Reconstruct Boxes3D from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			half_size: length-1 array containing nested list
			center: optional, length-1 array containing nested list
			colors: optional, length-1 array containing nested list
			rotation_in_euler_angles: optional, length-1 array containing nested list
		"""

		# 1. half_size (required)
		if "half_size" not in columns:
			raise KeyError("Missing required column 'half_size'")
		half_size_array = columns["half_size"].to_pylist()[0] 
		half_size = np.array(half_size_array, dtype=np.float32)

		# 2. center (optional)
		center = None
		if "center" in columns:
			center_array = columns["center"].to_pylist()[0]
			center = np.array(center_array, dtype=np.float32)

		# 3. colors (optional)
		colors = None
		if "colors" in columns:
			colors_array = columns["colors"].to_pylist()[0]
			colors = np.array(colors_array, dtype=np.uint32)

		# 4. rotation_in_euler_angles (optional)
		rotation_in_euler_angles = None
		if "rotation_in_euler_angles" in columns:
			rotation_array = columns["rotation_in_euler_angles"].to_pylist()[0]
			rotation_in_euler_angles = np.array(rotation_array, dtype=np.float32)
		
		return cls(
			half_size=half_size,
			center=center,
			colors=colors,
			rotation_in_euler_angles=rotation_in_euler_angles,
		)

# Mesh
class Mesh3D:
	"""
	A 3D triangle mesh as specified by its per-mesh and per-vertex properties.

	Attributes:
		vertex_positions (np.ndarray): Array of vertex positions (shape (N, 3)).
		triangle_indices (np.ndarray, optional): Array of triangle indices (shape (M, 3)).
		vertex_normals (np.ndarray, optional): Array of vertex normals (shape (N, 3)).
		vertex_colors (Rgba32ArrayLike, optional): Array of vertex colors.

	Args:
		vertex_positions (np.ndarray): Array of vertex positions (shape (N, 3)).
		triangle_indices (np.ndarray, optional): Array of triangle indices (shape (M, 3)).
		vertex_normals (np.ndarray, optional): Array of vertex normals (shape (N, 3)).
		vertex_colors (Rgba32ArrayLike, optional): Array of vertex colors.
	"""
	telekinesis_datatype = "datatypes.datatypes.Mesh3D"
	
	def __init__(self,
				 vertex_positions: np.ndarray,
				 triangle_indices: Optional[np.ndarray] = None,
				 vertex_normals: Optional[np.ndarray] = None,
				 vertex_colors: Optional["Rgba32ArrayLike"] = None):

		# Type checks
		if not isinstance(vertex_positions, np.ndarray):
			raise TypeError("vertex_positions must be a numpy ndarray")
		if triangle_indices is not None and not isinstance(triangle_indices, np.ndarray):
			raise TypeError("triangle_indices must be a numpy ndarray or None")
		if vertex_normals is not None and not isinstance(vertex_normals, np.ndarray):
			raise TypeError("vertex_normals must be a numpy ndarray or None")

		# Shape checks
		# ----- positions -----
		if vertex_positions.size == 0:
			# Ensure empty array has shape (0,3)
			vertex_positions = vertex_positions.reshape(0, 3)
		
		elif vertex_positions.shape == (3,):
			# Accept (3,) and reshape to (1,3)
			vertex_positions = vertex_positions.reshape(1, 3)

		# Value checks
		if vertex_positions.ndim != 2 or vertex_positions.shape[1] != 3:
			raise ValueError("vertex_positions must be of shape (N, 3)")
		num_positions = vertex_positions.shape[0]

		# triangle_indices: accept (3,) or (M, 3)
		if triangle_indices.size == 0:
			# Ensure empty array has shape (0,3)
			triangle_indices = triangle_indices.reshape(0, 3)

		elif triangle_indices.shape == (3,):
			# Accept (3,) and reshape to (1,3)
			triangle_indices = triangle_indices.reshape(1, 3)

		# Value checks
		if triangle_indices.ndim != 2 or triangle_indices.shape[1] != 3:
			raise ValueError(f"triangle_indices must be of shape (M, 3), but got: {triangle_indices.shape}")
		
		# vertex_normals: accept (3,) or (N, 3), must match N
		if vertex_normals is not None:
			if vertex_normals.size == 0:
				# Ensure empty array has shape (0,3)
				vertex_normals = vertex_normals.reshape(0, 3)

			if vertex_normals.shape == (3,):
				# Accept (3,) and reshape to (1,3)
				vertex_normals = vertex_normals.reshape(1, 3)

			if vertex_normals.ndim != 2 or vertex_normals.shape[1] != 3:
				raise ValueError(
					f"vertex_normals must be of shape (N, 3). Received shape: {vertex_normals.shape}"
				)
			
		# Handle vertex_colors 
		if vertex_colors is None:
			self.vertex_colors = None
		else:
			# If vertex_colors is already a numpy array of uint32, use it directly
			if isinstance(vertex_colors, np.ndarray) and vertex_colors.dtype == np.uint32:
				self.vertex_colors = vertex_colors

			# If ndarray and shape in (3,4)	
			elif isinstance(vertex_colors, np.ndarray) and vertex_colors.ndim == 2 and vertex_colors.shape[1] in (3, 4):
				self.vertex_colors = converters._numpy_array_to_u32(vertex_colors)   # (N,) uint32

			elif isinstance(vertex_colors, Rgba32):
				rgba_list = [int(vertex_colors)]
				self.vertex_colors = np.asarray(rgba_list, dtype=np.uint32)

			elif isinstance(vertex_colors, Sequence) and not isinstance(vertex_colors, (str, bytes)):
				rgba_list = [int(Rgba32(c)) for c in vertex_colors]
				self.vertex_colors = np.asarray(rgba_list, dtype=np.uint32)

			else:
				rgba_list = [int(Rgba32(vertex_colors))]
				self.vertex_colors = np.asarray(rgba_list, dtype=np.uint32)

			if self.vertex_colors.shape[0] not in (1, num_positions):
				raise ValueError(
					f"vertex_colors length {self.vertex_colors.shape[0]} must be 1 or match {num_positions}"
				)
	
		# Members
		self.vertex_positions = vertex_positions
		self.triangle_indices = triangle_indices
		self.vertex_normals = vertex_normals

		# Field names for serialization
		self._field_names = ["vertex_positions", "triangle_indices", "vertex_normals", "vertex_colors"]

		# Mapping of field names to their PyArrow types 
		self.field_to_pyarrow_type_map = {
			"vertex_positions": pa.list_(pa.list_(pa.float32(), 3)),  # Nested: [[x,y,z], ...]
			"triangle_indices": pa.list_(pa.list_(pa.int32(), 3)),     # Nested: [[i,j,k], ...]
			"vertex_normals": pa.list_(pa.list_(pa.float32(), 3)),     # Nested: [[nx,ny,nz], ...]
			"vertex_colors": pa.list_(pa.uint32()),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Mesh3D instance to a dict of PyArrow arrays.

		We intentionally produce ONE ROW per mesh:
		- vertex_positions column: length-1 array, value is list-of-vec3
		- triangle_indices column: length-1 array, value is list-of-tri (optional)
		- vertex_normals column: length-1 array, value is list-of-vec3 (optional)
		- vertex_colors column: length-1 array, value is list-of-uint32 (optional)
		"""
		array_dict: dict[str, pa.Array] = {}

		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Mesh3D")

			field_value = getattr(self, field_name)

			# vertex_positions is required
			if field_name == "vertex_positions" and field_value is None:
				raise ValueError("Field 'vertex_positions' cannot be None")

			# skip None for optional fields
			if field_value is None:
				continue

			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			try:
				# For all fields we wrap into a single row
				array_dict[field_name] = pa.array(
					[field_value.tolist()],
					type=pa_type,
				)
			except Exception as e:
				raise ValueError(
					f"Error converting field '{field_name}' to PyArrow array: {e}"
				) from e

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Mesh3D":
		"""
		Reconstruct Mesh3D from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shapes:
			vertex_positions : length-1 array, element is [[x,y,z], ...]
			triangle_indices : length-1 array, element is [[i,j,k], ...] (optional)
			vertex_normals   : length-1 array, element is [[nx,ny,nz], ...] (optional)
			vertex_colors    : length-1 array, element is [packed_rgba, ...] (optional)
		"""

		# 1. vertex_positions (required)
		if "vertex_positions" not in columns:
			raise KeyError("Missing required column 'vertex_positions'")

		pa_positions = columns["vertex_positions"]
		if len(pa_positions) != 1:
			raise ValueError(f"'vertex_positions' must have exactly 1 row, got {len(pa_positions)}")

		positions_list = pa_positions[0].as_py()
		vertex_positions = np.asarray(positions_list, dtype=np.float32)

		# 2. triangle_indices (optional) 
		#TODO: Returns list of lists
		triangle_indices: Optional[np.ndarray] = None
		if "triangle_indices" in columns:
			pa_indices = columns["triangle_indices"]
			if len(pa_indices) != 1:
				raise ValueError(f"'triangle_indices' must have exactly 1 row, got {len(pa_indices)}")
			
			indices_list = pa_indices[0].as_py()
			if indices_list is not None:
				triangle_indices = np.asarray(indices_list, dtype=np.int32)

		# 3. vertex_normals (optional)
		vertex_normals: Optional[np.ndarray] = None
		if "vertex_normals" in columns:
			pa_normals = columns["vertex_normals"]
			if len(pa_normals) != 1:
				raise ValueError(f"'vertex_normals' must have exactly 1 row, got {len(pa_normals)}")
			
			normals_list = pa_normals[0].as_py()
			if normals_list is not None:
				vertex_normals = np.asarray(normals_list, dtype=np.float32)

		# 4. vertex_colors (optional) 
		vertex_colors: Optional[np.ndarray] = None
		if "vertex_colors" in columns:
			pa_colors = columns["vertex_colors"]
			if len(pa_colors) != 1:
				raise ValueError(f"'vertex_colors' must have exactly 1 row, got {len(pa_colors)}")

			colors_list = pa_colors[0].as_py()   # either None or [packed_rgba,...]
			if colors_list is not None:
				vertex_colors = np.asarray(colors_list, dtype=np.uint32)
			else:
				vertex_colors = None

		# 5. Build instance
		return cls(
			vertex_positions=vertex_positions,
			triangle_indices=triangle_indices,
			vertex_normals=vertex_normals,
			vertex_colors=vertex_colors,
		)
	
	def has_vertex_colors(self) -> bool:
		"""
		Check if the mesh has vertex colors defined.

		Returns
		-------
		bool
			True if vertex colors are defined, False otherwise.
		"""
		return self.vertex_colors is not None
	
	def has_vertex_normals(self) -> bool:
		"""
		Check if the mesh has vertex normals defined.

		Returns
		-------
		bool
			True if vertex normals are defined, False otherwise.
		"""
		return self.vertex_normals is not None

# List of 2D points like point cloud
class Points2D:
	"""
	A 2D point cloud with positions and optional colors, labels, and radii.

	Attributes:
		positions (np.ndarray): Array of 2D positions (shape (N, 2)).
		colors (Rgba32ArrayLike, optional): Array of colors.
		radii (float, optional): Radii for the points.

	Args:
		positions (np.ndarray): Array of 2D positions (shape (N, 2)).
		colors (Rgba32ArrayLike, optional): Array of colors.
		radii (float, optional): Radii for the points.
	"""
	telekinesis_datatype = "datatypes.datatypes.Points2D"
	def __init__(
		self,
		positions: np.ndarray,
		colors: Optional["Rgba32ArrayLike"] = None,
		radii: Optional[float] = None,
	):
		
		# Type checks
		if not isinstance(positions, np.ndarray):
			raise TypeError("positions must be a numpy ndarray")
		if radii is not None and not isinstance(radii, float):
			raise TypeError("radii must be a float or None")
		
		# Shape checks
		if positions.size == 0:
			# Ensure empty array has shape (0,3)
			positions = positions.reshape(0, 3)

		if positions.shape == (3,):
			# Accept (3,) and reshape to (1,3)
			positions = positions.reshape(1, 3)

		if positions.ndim != 2 or positions.shape[1] != 2:
			raise ValueError("positions must be of shape (N, 2)")
		num_positions = positions.shape[0]
		
		if colors is None:
			self.colors = None
		else:
			# If colors is already a numpy array of uint32, use it directly
			if isinstance(colors, np.ndarray) and colors.dtype == np.uint32:
				self.colors = colors

			elif isinstance(colors, np.ndarray) and colors.ndim == 2 and colors.shape[1] in (3, 4):
				self.colors = converters._numpy_array_to_u32(colors)   # (N,) uint32
				
			elif isinstance(colors, Rgba32):
				rgba_list = [int(colors)]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			
			elif isinstance(colors, Sequence) and not isinstance(colors, (str, bytes)):
				rgba_list = [int(Rgba32(c)) for c in colors]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			
			else:
				rgba_list = [int(Rgba32(colors))]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			
			if self.colors.shape[0] not in (1, num_positions):
				raise ValueError(
					f"colors length {self.colors.shape[0]} must be 1 or match {num_positions}"
				)

		#TODO: Value checks
	
		# radii: allow scalar or array
		if radii is None:
			radii = 0.1

		# Members (colors already handled)
		self.positions = positions
		self.radii = radii

		# Field names for serialization
		self._field_names = ["positions", "colors", "radii"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"positions": pa.list_(pa.list_(pa.float32(), 2)),
			# Colors are stored as packed uint32 RGBA values (e.g., 0xFF0000FF = 4278190335)
			"colors": pa.list_(pa.uint32()),
			"radii": pa.float32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Points2D instance to a dict of PyArrow arrays.

		We intentionally produce ONE ROW per point cloud:
		- positions column: length-1 array, value is list-of-vec2
		- colors   column: length-1 array, value is list-of-uint32 (optional)
		- radii    column: length-1 array, value is scalar float32
		"""
		array_dict: dict[str, pa.Array] = {}

		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Points3D")

			field_value = getattr(self, field_name)

			# positions is required
			if field_name == "positions" and field_value is None:
				raise ValueError("Field 'positions' cannot be None")

			# skip None for optional fields
			if field_value is None:
				continue

			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# ---- wrap into a single row ----
			if field_name == "positions":
				# positions: (N,2) -> nested list [[x,y], ...]
				array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			elif field_name == "colors":
				# colors: np.uint32[1 or N] -> list of ints
				array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			elif field_name == "radii":
				array_dict[field_name] = pa.array([float(field_value)], type=pa_type)
			else:
				# fallback: still single-row
				array_dict[field_name] = pa.array([field_value], type=pa_type)

		
		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Points2D":
		"""
		Reconstruct Points2D from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shapes:
			positions : length-1 array, element is [[x,y], ...]
			colors    : length-1 array, element is [packed_rgba, ...]    (optional)
			radii     : length-1 array, element is scalar float          (optional)
		"""

		# 1. positions (required)
		if "positions" not in columns:
			raise KeyError("Missing required column 'positions'")

		pa_positions = columns["positions"]
		if len(pa_positions) != 1:
			raise ValueError(f"'positions' must have exactly 1 row, got {len(pa_positions)}")

		positions_list = pa_positions[0].as_py()
		positions = np.asarray(positions_list, dtype=np.float32)

		# 2. colors (optional)
		colors: Optional[np.ndarray] = None
		if "colors" in columns:
			pa_colors = columns["colors"]
			if len(pa_colors) != 1:
				raise ValueError(f"'colors' must have exactly 1 row, got {len(pa_colors)}")

			colors_list = pa_colors[0].as_py()   # either None or [packed_rgba,...]
			if colors_list is not None:
				colors = np.asarray(colors_list, dtype=np.uint32)
			else:
				colors = None

		# 3. radii (optional)
		radii: Optional[float] = None
		if "radii" in columns:
			pa_radii = columns["radii"]
			if len(pa_radii) != 1:
				raise ValueError(f"'radii' must have exactly 1 row, got {len(pa_radii)}")
			radii = float(pa_radii[0].as_py())

		# 4. Build instance
		return cls(
			positions=positions,
			colors=colors,
			radii=radii,
		)


# Point cloud
class Points3D:
	"""
	A 3D point cloud with positions and optional colors, radii, and labels.

	Attributes:
		positions (np.ndarray): Array of 3D positions (shape (N, 3)).
		colors (Rgba32ArrayLike, optional): Array of colors.
		radii (float, optional): Radii for the points.

	Args:
		positions (np.ndarray): Array of 3D positions (shape (N, 3)).
		colors (Rgba32ArrayLike, optional): Array of colors.
		radii (float, optional): Radii for the points.
	"""
	telekinesis_datatype = "datatypes.datatypes.Points3D"

	def __init__(
		self,
		positions: np.ndarray,
		normals: Optional[np.ndarray] = None,
		colors: Optional["Rgba32ArrayLike"] = None,
		radii: Optional[float] = None,
	):
		
		# Type checks
		if not isinstance(positions, np.ndarray):
			raise TypeError("positions must be a numpy ndarray")
		if normals is not None and not isinstance(normals, np.ndarray):
			raise TypeError("normals must be a numpy ndarray or None.")
		if radii is not None and not isinstance(radii, float):
			raise TypeError("radii must be a float or None.")


		# Shape checks
		# ----- positions -----
		if positions.size == 0:
			# Ensure empty array has shape (0,3)
			positions = positions.reshape(0, 3)

		if positions.shape == (3,):
			# Accept (3,) and reshape to (1,3)
			positions = positions.reshape(1, 3)

		if positions.ndim != 2 or positions.shape[1] != 3:
			raise ValueError(
				f"positions must be of shape (N, 3). Received shape: {positions.shape}"
			)

		num_positions = positions.shape[0]


		# ----- normals -----
		if normals is not None:
			if normals.size == 0:
				# Ensure empty array has shape (0,3)
				normals = normals.reshape(0, 3)

			if normals.shape == (3,):
				# Accept (3,) and reshape to (1,3)
				normals = normals.reshape(1, 3)

			if normals.ndim != 2 or normals.shape[1] != 3:
				raise ValueError(
					f"normals must be of shape (N, 3). Received shape: {normals.shape}"
				)

			num_normals = normals.shape[0]
			self.normals = normals

			# ----- consistency check -----
			if num_positions != num_normals:
				raise ValueError(
					f"positions and normals must have the same number of rows. "
					f"Got {num_positions} positions vs {num_normals} normals."
				)
		else:
			num_normals = 0

		# Handle colors
		if colors is None:
			self.colors = colors
		else:
			# If colors is already a numpy array of uint32, use it directly
			if isinstance(colors, np.ndarray) and colors.dtype == np.uint32:
				self.colors = colors
			
			elif isinstance(colors, np.ndarray) and colors.ndim == 2 and colors.shape[1] in (3, 4):
				self.colors = converters._numpy_array_to_u32(colors)   # (N,) uint32

			elif isinstance(colors, Rgba32):
				rgba_list = [int(colors)]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			
			elif isinstance(colors, Sequence) and not isinstance(colors, (str, bytes)):
				rgba_list = [int(Rgba32(c)) for c in colors]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)
			
			else:
				rgba_list = [int(Rgba32(colors))]
				self.colors = np.asarray(rgba_list, dtype=np.uint32)

			if self.colors.shape[0] not in (1, num_positions):
				raise ValueError(
					f"colors length {self.colors.shape[0]} must be 1 or match {num_positions}"
				)
			
		#TODO: Value checks
	
		# radii: allow scalar or array
		if radii is None:
			radii = 1.0

		# Members (colors already handled)
		self.positions = positions
		self.normals = normals
		self.radii = radii

		# Field names for serialization
		self._field_names = ["positions", "normals", "colors", "radii"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"positions": pa.list_(pa.list_(pa.float32(), 3)),
			"normals": pa.list_(pa.list_(pa.float32(), 3)),
			# Colors are stored as packed uint32 RGBA values (e.g., 0xFF0000FF = 4278190335)
			"colors": pa.list_(pa.uint32()),
			"radii": pa.float32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Points3D instance to a dict of PyArrow arrays.

		We intentionally produce ONE ROW per point cloud:
		- positions column: length-1 array, value is list-of-vec3
		- colors   column: length-1 array, value is list-of-uint32 (optional)
		- radii    column: length-1 array, value is scalar float32
		"""
		array_dict: dict[str, pa.Array] = {}

		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Points3D")

			field_value = getattr(self, field_name)

			# positions is required
			if field_name == "positions" and field_value is None:
				raise ValueError("Field 'positions' cannot be None")

			# skip None for optional fields
			if field_value is None:
				continue

			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# ---- wrap into a single row ----
			if field_name == "positions" or field_name == "normals":
				# positions: (N,3) -> nested list [[x,y,z], ...]
				array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			elif field_name == "colors":
				# colors: np.uint32[1 or N] -> list of ints
				array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			elif field_name == "radii":
				array_dict[field_name] = pa.array([float(field_value)], type=pa_type)
		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Points3D":
		"""
		Reconstruct Points3D from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shapes:
			positions : length-1 array, element is [[x,y,z], ...]
			colors    : length-1 array, element is [packed_rgba, ...]    (optional)
			radii     : length-1 array, element is scalar float          (optional)
		"""

		# 1. positions (required)
		if "positions" not in columns:
			raise KeyError("Missing required column 'positions'")

		pa_positions = columns["positions"]
		if len(pa_positions) != 1:
			raise ValueError(f"'positions' must have exactly 1 row, got {len(pa_positions)}")

		positions_list = pa_positions[0].as_py()
		positions = np.asarray(positions_list, dtype=np.float32)

		# 2. normals (optional)
		normals: Optional[np.ndarray] = None
		if "normals" in columns:
			pa_normals = columns["normals"]
			if len(pa_normals) != 1:
				raise ValueError(f"'normals' must have exactly 1 row, got {len(pa_normals)}")

			normals_list = pa_normals[0].as_py()
			normals = np.asarray(normals_list, dtype=np.float32)

		# 3. colors (optional)
		colors: Optional[np.ndarray] = None
		if "colors" in columns:
			pa_colors = columns["colors"]
			if len(pa_colors) != 1:
				raise ValueError(f"'colors' must have exactly 1 row, got {len(pa_colors)}")

			colors_list = pa_colors[0].as_py()   # either None or [packed_rgba,...]
			if colors_list is not None:
				colors = np.asarray(colors_list, dtype=np.uint32)
			else:
				colors = None

		# 4. radii (optional)
		radii: Optional[float] = None
		if "radii" in columns:
			pa_radii = columns["radii"]
			if len(pa_radii) != 1:
				raise ValueError(f"'radii' must have exactly 1 row, got {len(pa_radii)}")
			radii = float(pa_radii[0].as_py())

		# 4. Build instance
		return cls(
			positions=positions,
			normals=normals,
			colors=colors,
			radii=radii,
		)
	
	def has_colors(self) -> bool:
		"""
		Check if the point cloud has colors defined.
		"""
		return self.colors is not None
	
	def to_numpy(self, 
			  attribute: str) -> np.ndarray:
		"""
		Get the point positions as a numpy array.
		"""
		if attribute == "positions":
			return self.positions
		elif attribute == "normals":
			return self.normals
		elif attribute == "colors":
			if self.colors is not None:
				colors = Rgba32(self.colors)
				return colors.to_numpy()
			return None
		elif attribute == "radii":
			return self.radii
		else:
			raise ValueError(f"Unknown attribute: {attribute}")

# Vectors
class Vector3D:
	"""
	A vector in 3D space.

	Attributes:
		xyz (np.ndarray): The 3D vector (shape (3,)).

	Args:
		xyz (np.ndarray): The 3D vector (shape (3,)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Vector3D"
	
	def __init__(self, xyz: np.ndarray):
		# Type checks
		if not isinstance(xyz, np.ndarray):
			raise TypeError("xyz must be a numpy ndarray")
		
		# Value checks
		if xyz.shape != (3,):
			raise ValueError("xyz must be a 1D array of length 3")
		
		self.xyz = xyz

		# Field names for serialization
		self._field_names = ["xyz"]
		
		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"xyz": pa.list_(pa.float32(), 3),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Vector3D instance to a dict of PyArrow arrays.
		
		Returns a single-row array for the xyz vector.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Vector3D")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Vector3D":
		"""
		Reconstruct Vector3D from a dict of PyArrow arrays produced by `to_pyarrow`.
		
		Expected shape:
			xyz: length-1 array containing a 3D vector
		"""

		# 1. 'xyz' column (required)
		if "xyz" not in columns:
			raise KeyError("Missing required column 'xyz'")
		
		pa_xyz = columns["xyz"]
		if len(pa_xyz) != 1:
			raise ValueError(f"'xyz' must have exactly 1 row, got {len(pa_xyz)}")
		
		xyz_list = pa_xyz[0].as_py()
		xyz = np.array(xyz_list, dtype=np.float32)
		return cls(xyz=xyz)

	def to_list(self) -> list[float]:
		"""
		Convert the Vector3D to a list of floats.
		"""
		return self.xyz.tolist()

	def to_numpy(self) -> np.ndarray:
		"""
		Convert the Vector3D to a numpy array.
		"""
		return self.xyz
	
class Vector4D:
	"""
	A vector in 4D space.

	Attributes:
		xyzw (np.ndarray): The 4D vector (shape (4,)).

	Args:
		xyzw (np.ndarray): The 4D vector (shape (4,)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Vector4D"

	def __init__(self,
			  xyzw: np.ndarray):
		
		# Type checks
		if not isinstance(xyzw, np.ndarray):
			raise TypeError("xyzw must be a numpy ndarray")
		
		# Value checks
		if xyzw.shape != (4,):
			raise ValueError("xyzw must be a 1D array of length 4")

		self.xyzw = xyzw

		# Field names for serialization
		self._field_names = ["xyzw"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"xyzw": pa.list_(pa.float32(), 4),
		}


	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Vector4D instance to a dict of PyArrow arrays.

		Returns a single-row array for the xyzw vector.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Vector3D")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Vector4D":
		"""
		Reconstruct Vector4D from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shape:
			xyzw: length-1 array containing a 4D vector
		"""

		# 1. 'xyzw' column (required)
		if "xyzw" not in columns:
			raise KeyError("Missing required column 'xyzw'")

		pa_xyzw = columns["xyzw"]
		if len(pa_xyzw) != 1:
			raise ValueError(f"'xyzw' must have exactly 1 row, got {len(pa_xyzw)}")

		xyzw_list = pa_xyzw[0].as_py()
		xyzw = np.array(xyzw_list, dtype=np.float32)
		return cls(xyzw=xyzw)

	def to_list(self) -> list[float]:
		"""
		Convert the Vector4D to a list of floats.
		"""
		return self.xyzw.tolist()

	def to_numpy(self) -> np.ndarray:
		"""
		Convert the Vector4D to a numpy array.
		"""
		return self.xyzw


# ------------------ ### Transform & Matrix Datatypes ------------------


# A transform between two 3D spaces, i.e. a pose.
class Transform3D:
	"""
	A transform between two 3D spaces (pose).

	Attributes:
		translation (np.ndarray): Translation vector (shape (3,)).
		rotation_in_euler_angles (np.ndarray): Rotation in Euler angles (shape (3,)).
		scale (np.ndarray, optional): Scale vector (shape (3,)).

	Args:
		translation (np.ndarray): Translation vector (shape (3,)).
		rotation_in_euler_angles (np.ndarray): Rotation in Euler angles (shape (3,)).
		scale (np.ndarray, optional): Scale vector (shape (3,)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Transform3D"

	def __init__(self,
			  translation: np.ndarray,
			  rotation_in_euler_angles: np.ndarray,
			  scale: Optional[np.ndarray] = None,
			  ):
		
		# Type checks
		if not isinstance(translation, np.ndarray):
			raise TypeError("translation must be a numpy ndarray")
		if not isinstance(rotation_in_euler_angles, np.ndarray):
			raise TypeError("rotation_in_euler_angles must be a numpy ndarray")
		if scale is not None and not isinstance(scale, np.ndarray):
			raise TypeError("scale must be a numpy ndarray or None")
		
		# Value checks
		if translation.shape != (3,):
			raise ValueError("translation must be a 1D array of length 3")
		if rotation_in_euler_angles.shape != (3,):
			raise ValueError("rotation_in_euler_angles must be a 1D array of length 3")
		if scale is not None and scale.shape != (3,):
			raise ValueError("scale must be a 1D array of length 3 if provided")
		
		# Members
		self.translation = translation
		self.rotation_in_euler_angles = rotation_in_euler_angles
		self.scale = scale

		# Field names
		self._field_names = ["translation", "rotation_in_euler_angles", "scale"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"translation": pa.list_(pa.float32(), 3),
			"rotation_in_euler_angles": pa.list_(pa.float32(), 3),
			"scale": pa.list_(pa.float32(), 3)
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Transform3D instance to a dict of PyArrow arrays.

		Returns a single-row array for each field.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Vector3D")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Transform3D":
		"""
		Reconstruct Transform3D from a dict of PyArrow arrays produced by `to_pyarrow`.
		Expected shapes:
			translation: length-1 array containing a 3D vector
			rotation_in_euler_angles: length-1 array containing a 3D vector
			scale: length-1 array containing a 3D vector (optional)
		"""

		# 1. 'translation' column (required)
		if "translation" not in columns:
			raise KeyError("Missing required column 'translation'")

		pa_translation = columns["translation"]
		if len(pa_translation) != 1:
			raise ValueError(f"'translation' must have exactly 1 row, got {len(pa_translation)}")
		translation_list = pa_translation[0].as_py()
		translation = np.array(translation_list, dtype=np.float32)

		# 2. 'rotation_in_euler_angles' column (required)
		pa_rotation = columns["rotation_in_euler_angles"]
		if len(pa_rotation) != 1:
			raise ValueError(f"'rotation_in_euler_angles' must have exactly 1 row, got {len(pa_rotation)}")
		rotation_list = pa_rotation[0].as_py()
		rotation = np.array(rotation_list, dtype=np.float32)

		# 3. 'scale' column (optional)
		pa_scale = columns.get("scale")
		if pa_scale is not None and len(pa_scale) != 1:
			raise ValueError(f"'scale' must have exactly 1 row, got {len(pa_scale)}")
		if pa_scale is not None:
			scale_list = pa_scale[0].as_py()
			scale = np.array(scale_list, dtype=np.float32)

		return cls(translation=translation, rotation_in_euler_angles=rotation, scale=scale)

# Matrix 3x3
class Mat3X3:
	"""
	A 3x3 matrix.

	Attributes:
		matrix (np.ndarray): The 3x3 matrix (shape (3, 3)).

	Args:
		matrix (np.ndarray): The 3x3 matrix (shape (3, 3)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Mat3X3"

	def __init__(self,
			  matrix: np.ndarray):
		
		# Type checks
		if not isinstance(matrix, np.ndarray):
			raise TypeError("matrix must be a numpy ndarray")
		
		# Value checks
		if matrix.shape != (3, 3):
			raise ValueError("matrix must be a 2D array of shape (3, 3)")

		# Members
		self.matrix = matrix

		# Field names for serialization
		self._field_names = ["matrix"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"matrix": pa.list_(pa.list_(pa.float32(), 3))  # [[x,x,x], ...] 3 rows
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Mat3X3 instance to a dict of PyArrow arrays.

		Returns a single-row array for the matrix.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Mat3X3")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Mat4X4":
		"""
		Reconstruct Mat3X3 from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shape:
			matrix: length-1 array containing a 3x3 matrix
		"""

		# 1. 'matrix' column (required)
		if "matrix" not in columns:
			raise KeyError("Missing required column 'matrix'")

		pa_matrix = columns["matrix"]
		if len(pa_matrix) != 1:
			raise ValueError(f"'matrix' must have exactly 1 row, got {len(pa_matrix)}")

		matrix_list = pa_matrix[0].as_py()  # [[row0], [row1], [row2]]
		matrix = np.array(matrix_list, dtype=np.float32)  # shape (3,3)
		return cls(matrix=matrix)

	def to_numpy(self) -> np.ndarray:
		"""
		Convert the Mat3X3 to a numpy array.
		"""
		return self.matrix

	def to_list(self) -> list[list[float]]:
		"""
		Convert the Mat3X3 to a nested list.
		"""
		return self.matrix.tolist()


# Matrix 4x4
class Mat4X4:
	"""
	A 4x4 matrix.

	Attributes:
		matrix (np.ndarray): The 4x4 matrix (shape (4, 4)).

	Args:
		matrix (np.ndarray): The 4x4 matrix (shape (4, 4)).
	"""
	telekinesis_datatype = "datatypes.datatypes.Mat4X4"

	def __init__(self,
			  matrix: np.ndarray):
		
		# Type checks
		if not isinstance(matrix, np.ndarray):
			raise TypeError("matrix must be a numpy ndarray")
		
		# Value checks
		if matrix.shape != (4, 4):
			raise ValueError("matrix must be a 2D array of shape (4, 4)")
		
		# Members
		self.matrix = matrix

		# Field names for serialization
		self._field_names = ["matrix"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"matrix": pa.list_(pa.list_(pa.float32(), 4))  # [[x,x,x,x], ...] 4 rows
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Mat4X4 instance to a dict of PyArrow arrays.

		Returns a single-row array for the matrix.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Mat4X4")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Mat4X4":
		"""
		Reconstruct Mat4X4 from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shape:
			matrix: length-1 array containing a 4x4 matrix
		"""

		# 1. 'matrix' column (required)
		if "matrix" not in columns:
			raise KeyError("Missing required column 'matrix'")

		pa_matrix = columns["matrix"]
		if len(pa_matrix) != 1:
			raise ValueError(f"'matrix' must have exactly 1 row, got {len(pa_matrix)}")

		matrix_list = pa_matrix[0].as_py()  # [[row0], [row1], [row2], [row3]]
		matrix = np.array(matrix_list, dtype=np.float32)  # shape (4,4)
		return cls(matrix=matrix)

	def to_numpy(self) -> np.ndarray:
		"""
		Convert the Mat4X4 to a numpy array.
		"""
		return self.matrix

	def to_list(self) -> list[list[float]]:
		"""
		Convert the Mat4X4 to a nested list.
		"""
		return self.matrix.tolist()


# ------------------ ### Image Related Datatypes ------------------
# Image
class Image:
	"""
	A monochrome or color image.

	Attributes:
		image (np.ndarray, optional): The image data as a NumPy array.
		color_model (ColorModelLike, optional): The color model of the image.
		pixel_format (int, optional): The pixel format.
		channel_datatype (Any, optional): The channel datatype.
		bytes (bytes, optional): The raw image bytes.
		width (int, optional): The width of the image.
		height (int, optional): The height of the image.

	Args:
		image (np.ndarray, optional): The image data as a NumPy array.
		color_model (ColorModelLike, optional): The color model of the image.
		pixel_format (int, optional): The pixel format.
		channel_datatype (Any, optional): The channel datatype.
		bytes (bytes, optional): The raw image bytes.
		width (int, optional): The width of the image.
		height (int, optional): The height of the image.
	"""
	telekinesis_datatype = "datatypes.datatypes.Image"

	def __init__(
		self,
		image: Optional[np.ndarray] = None,
		color_model: Optional["ColorModelLike"] = None,
		*,
		pixel_format: Optional[int] = None,
		channel_datatype: Optional[Any] = None,
		bytes: Optional[bytes] = None,
		width: Optional[int] = None,
		height: Optional[int] = None
	):


		channel_count_from_color_model = {
			"a": 1,
			"l": 1,
			"la": 1,
			"bgr": 3,
			"rgb": 3,
			"yuv": 3,
			"bgra": 4,
			"rgba": 4,
		}

		# NumPy array input (preferred)
		if image is not None:
			if not isinstance(image, np.ndarray):
				raise TypeError("image must be a numpy ndarray")
			
			shape = image.shape
			while 2 < len(shape) and shape[0] == 1:
				shape = shape[1:]
			while 2 < len(shape) and shape[-1] == 1:
				shape = shape[:-1]
			if len(shape) == 2:
				_height, _width = shape
				channels = 1
			elif len(shape) == 3:
				_height, _width, channels = shape
			else:
				raise ValueError(f"Expected a 2D or 3D tensor, got {shape}")
			
			if width is not None and width != _width:
				raise ValueError(f"Provided width {width} does not match image width {_width}")
			else:
				width = _width
			if height is not None and height != _height:
				raise ValueError(f"Provided height {height} does not match image height {_height}")
			else:
				height = _height
			
			if color_model is None:
				if channels == 1:
					color_model = ColorModel.L
				elif channels == 3:
					color_model = ColorModel.RGB
				elif channels == 4:
					color_model = ColorModel.RGBA
				else:
					raise ValueError(f"Cannot infer color model for {channels} channels")
			else:
				try:
					# Validate color model against channels
					if isinstance(color_model, int):
						color_model_enum = ColorModel(color_model)
					else:
						color_model_enum = ColorModel.from_string(str(color_model))
					color_model = color_model_enum

					num_expected_channels = channel_count_from_color_model[str(color_model).lower()]
					if channels != num_expected_channels:
						logger.warning(
							f"Expected {num_expected_channels} channels for {color_model}; got {channels} channels",
						)
				except KeyError:
					logger.error(f"Unknown ColorModel: '{color_model}'")

			# Convert to uint8 if needed
			if image.dtype != np.uint8:
				logger.warning(f"Converting image dtype {image.dtype} → uint8 for Arrow storage")
				image = image.astype(np.uint8, copy=False)
				# TODO: Test if binary masks works with 0 and 1. If not, multiply by 255? : image = image.astype(np.uint8) * 255 

			try:
				channel_datatype = ChannelDatatype.from_np_dtype(image.dtype)
			except Exception:
				raise ValueError(f"Unsupported dtype {image.dtype}")

			channel_datatype = channel_datatype.value if hasattr(channel_datatype, 'value') else int(channel_datatype)
			color_model = color_model.value if hasattr(color_model, 'value') else int(color_model)
		
			
			# Members
			self.image = image
			self.image_bytes = image.tobytes()
			self.width = width
			self.height = height
			self.channel_datatype = channel_datatype
			self.color_model = color_model

			# Field names for serialization
			self._field_names = [
						"image",
						"buffer",
						"width",
						"height",
						"channel_datatype",
						"color_model",
					]


			# Mapping of field names to their PyArrow types
			self.field_to_pyarrow_type_map = {
		   				# "image": pa.list_(pa.list_(pa.list_(pa.uint8()))),
						 "image": pa.binary(),
						"width": pa.int32(),
						"height": pa.int32(),
						"channel_datatype": pa.int8(),
						"color_model": pa.int8()
					}
		
			logger.info(f"Created Image from NumPy array: {width}x{height}, color_model={color_model}, channel_datatype={channel_datatype}")
			return

		# Raw bytes input
		# If the user specified 'bytes', we can use direct construction
		if bytes is not None:
			if isinstance(bytes, np.ndarray):
				bytes = bytes.tobytes()

			if width is None or height is None or bytes is None:
				raise ValueError("Specifying 'bytes' requires 'width' and 'height'")

			if pixel_format is not None:
				if channel_datatype is not None:
					raise ValueError("Specifying 'channel_datatype' is mutually exclusive with 'pixel_format'")
				if color_model is not None:
					raise ValueError("Specifying 'color_model' is mutually exclusive with 'pixel_format'")

				# TODO(jleibs): Validate that bytes is the expected size.

				# Members
				self.buffer = bytes
				self.width = width
				self.height = height
				self.pixel_format = pixel_format
				self.color_model = color_model

				# Field names for serialization
				self._field_names = [
					"bytes",
					"width",
					"height",
					"pixel_format",
					"color_model",
				]
				
				# Mapping of field names to their PyArrow types
				self.field_to_pyarrow_type_map = {
					"bytes": pa.binary(),
					"width": pa.int32(),
					"height": pa.int32(),
					"pixel_format": pa.int8(),
					"color_model": pa.int8(),
				}

				logger.info(f"Created Image from raw bytes: {width}x{height}, pixel_format={pixel_format}")
				return
			else:
				if channel_datatype is None or color_model is None:
					raise ValueError("Specifying 'bytes' requires 'pixel_format' or both 'color_model' and 'channel_datatype'")

				# TODO(jleibs): Would be nice to do this with a field-converter
				if channel_datatype in (
					np.uint8,
					np.uint16,
					np.uint32,
					np.uint64,
					np.int8,
					np.int16,
					np.int32,
					np.int64,
					np.float16,
					np.float32,
					np.float64,
				):
					channel_datatype = ChannelDatatype.from_np_dtype(np.dtype(channel_datatype))  # type: ignore[arg-type]

				# TODO(jleibs): Validate that bytes is the expected size.

				# Members
				self.buffer = bytes
				self.width = width
				self.height = height
				self.pixel_format = pixel_format
				self.channel_datatype = channel_datatype
				self.color_model = color_model

				# Field names for serialization
				self._field_names = [
					"bytes",
					"width",
					"height",
					"pixel_format",
					"channel_datatype",
					"color_model",
				]
				
				# Mapping of field names to their PyArrow types
				self.field_to_pyarrow_type_map = {
					"bytes": pa.binary(),
					"width": pa.int32(),
					"height": pa.int32(),
					"pixel_format": pa.int8(),
					"channel_datatype": pa.int8(),
					"color_model": pa.int8(),
				}



	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Image instance to a dict of PyArrow arrays.

		Returns a single-row array for each field.
		"""
		array_dict: dict[str, pa.Array] = {}

		for field_name in self._field_names:
			if not hasattr(self, field_name):
				logger.warning(f"Missing field '{field_name}' on Image")
				continue

			if field_name == "image":
				field_value = self.image_bytes
			else:
				field_value = getattr(self, field_name)
	
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
	

			array_dict[field_name] = pa.array([field_value], type=pa_type)

			# # Wrap value into a single-row array
			# if field_name == "image":
			# 	# image: np.ndarray -> nested list [[int8, int8, ...], ...]
			# 	array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			# else:
			# 	# fallback: still single-row	
			# 	array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict
	
	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Image":
		"""
		Reconstruct Image from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shapes:
			image: length-1 array containing nested lists of uint8
			bytes: length-1 array containing binary data
			width: length-1 array containing an int32
			height: length-1 array containing an int32
			pixel_format: length-1 array containing an int8 (optional)
			channel_datatype: length-1 array containing an int8 (optional)
			color_model: length-1 array containing an int8 (optional)
		"""

		class_attributes = []

		if "bytes" not in columns and "image" not in columns:
			raise KeyError("Missing required column 'bytes' or 'image'")

		# 1. bytes (required) (or image)
		buffer = None
		if "bytes" not in columns:
			logger.warning("Missing required column 'bytes'. Expecting 'image' instead.")
		else:
			pa_bytes = columns["bytes"]
			if len(pa_bytes) != 1:
				raise ValueError(f"'bytes' must have exactly 1 row, got {len(pa_bytes)}")
			buffer = pa_bytes[0].as_py()
			cls.buffer = buffer
			class_attributes.append("bytes")

		# 2. width
		width = None
		if "width" not in columns or columns["width"] is None:
			logger.warning("Missing required column 'width'")
		else:
			pa_width = columns["width"]
			if len(pa_width) != 1:
				raise ValueError(f"'width' must have exactly 1 row, got {len(pa_width)}")
			width = int(pa_width[0].as_py())
			cls.width = width
			class_attributes.append("width")

		# 3. height
		height = None
		if "height" not in columns or columns["height"] is None:
			logger.warning("Missing required column 'height'")
		else:
			pa_height = columns["height"]
			if len(pa_height) != 1:
				raise ValueError(f"'height' must have exactly 1 row, got {len(pa_height)}")
			ht = pa_height[0].as_py()
			height = int(ht)
			cls.height = height
			class_attributes.append("height")

		# 4. pixel_format (optional)
		pixel_format = None
		if "pixel_format" not in columns or columns["pixel_format"] is None:
			logger.warning("Missing optional column 'pixel_format'")
		else:
			pa_pixel_format = columns["pixel_format"]
			if len(pa_pixel_format) != 1:
				raise ValueError(f"'pixel_format' must have exactly 1 row, got {len(pa_pixel_format)}")
			pf = pa_pixel_format[0].as_py()
			pixel_format = int(pf)
			cls.pixel_format = pixel_format
			class_attributes.append("pixel_format")

		# 5. channel_datatype (optional)
		channel_datatype = None
		if "channel_datatype" not in columns or columns["channel_datatype"] is None:
			logger.warning("Missing optional column 'channel_datatype'")
		else:
			pa_channel_datatype = columns["channel_datatype"]
			if len(pa_channel_datatype) != 1:
				raise ValueError(f"'channel_datatype' must have exactly 1 row, got {len(pa_channel_datatype)}")
			channel_datatype = int(pa_channel_datatype[0].as_py())
			cls.channel_datatype = channel_datatype
			class_attributes.append("channel_datatype")

		# 6. color_model (optional)
		color_model = None
		if "color_model" not in columns or columns["color_model"] is None:
			logger.warning("Missing optional column 'color_model'")
		else:
			pa_color_model = columns["color_model"]
			if len(pa_color_model) != 1:
				raise ValueError(f"'color_model' must have exactly 1 row, got {len(pa_color_model)}")
			color_model = int(pa_color_model[0].as_py())
			cls.color_model = color_model
			class_attributes.append("color_model")


		# 7. image required (or bytes)
		image = None
		if "image" not in columns:
			logger.warning("Missing required column 'image'. Expecting 'bytes' instead.")
		else:
			pa_img = columns["image"]
			if len(pa_img) != 1:
				raise ValueError(f"'image' must have exactly 1 row, got {len(pa_img)}")
			image_bytes = pa_img[0].as_py()  # bytes
			image = cls._to_numpy(obj=cls, image_bytes=image_bytes)
			cls.image = image
			class_attributes.append("image")

		attrs = {
			"image": image,
			"color_model": color_model,
			"pixel_format": pixel_format,
			"channel_datatype": channel_datatype,
			"bytes": buffer,
			"width": width,
			"height": height
		}

		# Filter only the keys you wanted
		filtered = {key: attrs[key] for key in class_attributes}

		return cls(**filtered)

	@classmethod
	def _to_numpy(cls, obj: "Image", image_bytes: Optional[bytes] = None) -> np.ndarray:
		
		if image_bytes is not None:
			buffer = image_bytes

		# ARRAY MODE: we already have a numpy array
		elif hasattr(obj, "image") and obj.image is not None:
			# Optional: enforce dtype/channel checks if you want
			return obj.image

		# BYTES MODE: fall back to buffer-based reconstruction
		elif hasattr(obj, "buffer") and obj.buffer is not None:
			buffer = obj.buffer
		else:
			raise RuntimeError(
				"Image has neither 'image' (array mode) nor 'buffer' (bytes mode). "
				"Cannot convert to numpy."
				"Image bytes parameter is also None."
			)

		width = obj.width
		height = obj.height
		color_model = obj.color_model
		channel_datatype = obj.channel_datatype
		channel_count = ColorModel(color_model).num_channels()

		dtype = ChannelDatatype(channel_datatype).to_np_dtype() if channel_datatype is not None else np.uint8
		arr = np.frombuffer(buffer, dtype=dtype)
		expected = height * width * channel_count
		if arr.size != expected:
			raise ValueError(
				f"Cannot reshape array of size {arr.size} into shape ({height}, {width}, {channel_count}). "
				f"Buffer length: {len(buffer)}, dtype: {dtype}, expected elements: {expected}. "
				f"Check that the image was created with the correct shape, dtype, and buffer size."
			)
		arr = arr.reshape((height, width, channel_count)) if channel_count > 1 else arr.reshape((height, width))
		return arr

	def to_numpy(self) -> np.ndarray:
		"""Return the image as a NumPy array (alias for to_numpy)."""
		return Image._to_numpy(obj=self)

class ImageFormat:

	telekinesis_datatype = "datatypes.datatypes.ImageFormat"
	"""
	A buffer that is known to store image data.
	"""
	
	def __init__(self,
			  width: int,
			  height: int,
			  pixel_format: Optional[int] = None,
			  channel_datatype: Optional[int] = None,
			  color_model: Optional[int] = None):
		
		# Type checks
		if not isinstance(width, int):
			raise TypeError("width must be an int")
		if not isinstance(height, int):
			raise TypeError("height must be an int")
		if pixel_format is not None and not isinstance(pixel_format, int):
			raise TypeError("pixel_format must be an int or None")
		if channel_datatype is not None and not isinstance(channel_datatype, int):
			raise TypeError("channel_datatype must be an int or None")
		if color_model is not None and not isinstance(color_model, int):
			raise TypeError("color_model must be an int or None")
		
		# Value checks

		# Members
		self.width = width
		self.height = height
		self.pixel_format = pixel_format
		self.channel_datatype = channel_datatype
		self.color_model = color_model

		# Field names for serialization
		self._field_names = [
			"width",
			"height",
			"pixel_format",
			"channel_datatype",
			"color_model",
		]

		# Mapping of field names to their PyArrow types
		self.field_to_telekinesis_type_map = {
			"width": pa.int32(),
			"height": pa.int32(),
			"pixel_format": pa.int8(),
			"channel_datatype": pa.int8(),
			"color_model": pa.int8(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this ImageFormat instance to a dict of PyArrow arrays.

		Returns a single-row array for each field.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on ImageFormat")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_telekinesis_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict
	
	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "ImageFormat":
		"""
		Reconstruct ImageFormat from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shapes:
			width: length-1 array containing an int32
			height: length-1 array containing an int32
			pixel_format: length-1 array containing an int8 (optional)
			channel_datatype: length-1 array containing an int8 (optional)
			color_model: length-1 array containing an int8 (optional)
		"""

		# 1. width (required)
		if "width" not in columns:
			raise KeyError("Missing required column 'width'")
		pa_width = columns["width"]
		if len(pa_width) != 1:
			raise ValueError(f"'width' must have exactly 1 row, got {len(pa_width)}")
		width = int(pa_width[0].as_py())

		# 2. height (required)
		if "height" not in columns:
			raise KeyError("Missing required column 'height'")
		pa_height = columns["height"]
		if len(pa_height) != 1:
			raise ValueError(f"'height' must have exactly 1 row, got {len(pa_height)}")
		height = int(pa_height[0].as_py())
		
		# 3. pixel_format (optional)
		pixel_format = None
		if "pixel_format" in columns:
			pa_pixel_format = columns["pixel_format"]
			if len(pa_pixel_format) != 1:
				raise ValueError(f"'pixel_format' must have exactly 1 row, got {len(pa_pixel_format)}")
			pixel_format = int(pa_pixel_format[0].as_py())

		# 4. channel_datatype (optional)
		channel_datatype = None
		if "channel_datatype" in columns:
			pa_channel_datatype = columns["channel_datatype"]
			if len(pa_channel_datatype) != 1:
				raise ValueError(f"'channel_datatype' must have exactly 1 row, got {len(pa_channel_datatype)}")
			channel_datatype = int(pa_channel_datatype[0].as_py())
		
		# 5. color_model (optional)
		color_model = None
		if "color_model" in columns:
			pa_color_model = columns["color_model"]
			if len(pa_color_model) != 1:
				raise ValueError(f"'color_model' must have exactly 1 row, got {len(pa_color_model)}")
			color_model = int(pa_color_model[0].as_py())
			

		return cls(
			width=width,
			height=height,
			pixel_format=pixel_format,
			channel_datatype=channel_datatype,
			color_model=color_model,
		)
	
# Color
class Rgba32:
		
	telekinesis_datatype = "datatypes.datatypes.Rgba32"

	def __init__(self, rgba: "Rgba32Like"):
		"""
		Normalize the input through the converter.
		"""

		# TODO: Typecheck

		# Members
		self.rgba = self._convert(rgba)

		# Field names for serialization
		self._field_names = ["rgba"]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"rgba": pa.uint32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Rgba32 instance to a dict of PyArrow arrays.

		Returns a single-row array for the RGBA value.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Mat4X4")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			# Wrap value into a single-row array
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Rgba32":
		"""
		Reconstruct Rgba32 from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shape:
			rgba: length-1 array containing the RGBA value
		"""

		# 1. rgba (required)
		if "rgba" not in columns:
			raise KeyError("Missing required column 'rgba'")

		pa_rgba = columns["rgba"]
		if len(pa_rgba) != 1:
			raise ValueError(f"'rgba' must have exactly 1 row, got {len(pa_rgba)}")

		rgba_value = pa_rgba[0].as_py()
		return cls(rgba=rgba_value)

	def _convert(self, data: "Rgba32Like") -> int:
		# Already an Rgba32
		if isinstance(data, Rgba32):
			return int(data.rgba)

		# Packed integer (python int or numpy integer)
		if isinstance(data, (int, np.integer)):
			return int(data)

		# Numpy array: MUST be a single color (3,) or (4,)
		if isinstance(data, np.ndarray):
			arr = np.asarray(data)

			# Reject batches explicitly
			if arr.ndim != 1 or arr.shape[0] not in (3, 4):
				raise ValueError(
					f"Rgba32 expects a single color of shape (3,) or (4,). Got {arr.shape}."
				)

			# Convert 0..1 floats or uint8 into packed u32
			packed = converters._numpy_array_to_u32(arr.reshape(1, -1))[0]
			return int(packed)

		# Sequence: MUST be length 3 or 4
		if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
			arr = np.asarray(list(data))
			if arr.ndim != 1 or arr.shape[0] not in (3, 4):
				raise ValueError(
					f"expected sequence of length 3 or 4, received {arr.shape}"
				)
			packed = converters._numpy_array_to_u32(arr.reshape(1, -1))[0]
			return int(packed)

		raise TypeError(f"Unsupported type for Rgba32: {type(data)}")


	def to_numpy(
		self,
		dtype: typing.DTypeLike = np.uint8,
		copy: Optional[bool] = None,
		num_channels: int = 3,
	) -> typing.NDArray[Any]:
		"""
		Return the color as a NumPy array [R, G, B, A] or [R, G, B].
		"""
		array = converters._rgba_u32_to_u8_array(self.rgba, num_channels=num_channels, dtype=np.dtype(dtype))

		# If it's logically a single color, return shape (4,) for RGBA or (3,) for RGB. Otherwise, shape is (1, 4) or (1, 3).
		if array.shape[0] == 1:
			array = array[0]

		if copy:
			array = array.copy()

		return array

	def __int__(self) -> int:
		return int(self.rgba)

	def __hash__(self) -> int:
		return hash(self.rgba)

Rgba32Like = Union["Rgba32", int, Sequence[Union[int, float]], typing.NDArray[Union[np.uint8, np.float32, np.float64]]]
Rgba32ArrayLike = Union["Rgba32", Sequence[Rgba32Like], int, typing.ArrayLike]

# Pinhole for intrinsics
class Pinhole:

	telekinesis_datatype = "datatypes.datatypes.Pinhole"	

	image_from_camera: np.ndarray
	resolution: np.ndarray
	camera_xyz: np.ndarray
	image_plane_distance: float

	def __init__(
		self: Any,
		*,
		image_from_camera: Optional[np.ndarray] = None,
		resolution: Optional[np.ndarray] = None,
		camera_xyz: Optional[np.ndarray] = None,
		width: Optional[Union[int, float]] = None,
		height: Optional[Union[int, float]] = None,
		focal_length: Optional[Union[float, np.ndarray]] = None,
		principal_point: Optional[np.ndarray] = None,
		fov_y: Optional[float] = None,
		aspect_ratio: Optional[float] = None,
		image_plane_distance: Optional[float] = None
	):
		# Type checks
		if image_from_camera is not None and not isinstance(image_from_camera, np.ndarray):
			raise TypeError("image_from_camera must be a numpy ndarray or None")
		if resolution is not None and not isinstance(resolution, np.ndarray):
			raise TypeError("resolution must be a numpy ndarray or None")
		if camera_xyz is not None and not isinstance(camera_xyz, np.ndarray):
			raise TypeError("camera_xyz must be a numpy ndarray or None")
		if width is not None and not isinstance(width, (int, float)):
			raise TypeError("width must be an int, float, or None")
		if height is not None and not isinstance(height, (int, float)):
			raise TypeError("height must be an int, float, or None")
		if focal_length is not None and not isinstance(focal_length, (float, np.ndarray)):
			raise TypeError("focal_length must be a float, numpy ndarray, or None")
		if principal_point is not None and not isinstance(principal_point, np.ndarray):
			raise TypeError("principal_point must be a numpy ndarray or None")
		if fov_y is not None and not isinstance(fov_y, float):
			raise TypeError("fov_y must be a float or None.")
		if aspect_ratio is not None and not isinstance(aspect_ratio, float):
			raise TypeError("aspect_ratio must be a float or None")
		if image_plane_distance is not None and not isinstance(image_plane_distance, float):
			raise TypeError(f"image_plane_distance must be a float or None. But received: {type(image_plane_distance)}")

		#TODO: Shape checks

		if resolution is None and width is not None and height is not None:
			resolution = [width, height]
		elif resolution is not None and (width is not None or height is not None):
			logger.warning("Can't set both resolution and width/height", 1)

			if image_from_camera is None:
				if fov_y is not None and aspect_ratio is not None:
					EPSILON = 1.19209e-07
					focal_length = focal_length = 0.5 / math.tan(max(fov_y * 0.5, EPSILON))
					resolution = [aspect_ratio, 1.0]

				if resolution is not None:
					res_vec = np.array(resolution, dtype=float)
					width = cast("float", res_vec[0])
					height = cast("float", res_vec[1])
				else:
					width = None
					height = None

				if focal_length is None:
					if height is None or width is None:
						raise ValueError("Either image_from_camera or focal_length must be set")
					else:
						logger.warning("Either image_from_camera or focal_length must be set", 1)
						focal_length = (width * height) ** 0.5  # a reasonable best-effort default

				if principal_point is None:
					if height is not None and width is not None:
						principal_point = [width / 2, height / 2]
					else:
						raise ValueError("Must provide one of principal_point, resolution, or width/height")

				if type(focal_length) in (int, float):
					fl_x = focal_length
					fl_y = focal_length
				else:
					try:
						# TODO(emilk): check that it is 2 elements long
						fl_x = focal_length[0]  # type: ignore[index]
						fl_y = focal_length[1]  # type: ignore[index]
					except Exception:
						raise ValueError("Expected focal_length to be one or two floats") from None

				try:
					u_cen = principal_point[0]  # type: ignore[index]
					v_cen = principal_point[1]  # type: ignore[index]
				except Exception:
					raise ValueError("Expected principal_point to be one or two floats") from None

				image_from_camera = [[fl_x, 0, u_cen], [0, fl_y, v_cen], [0, 0, 1]]  # type: ignore[assignment]
			else:
				if focal_length is not None:
					logger.warning("Both image_from_camera and focal_length set", 1)
				if principal_point is not None:
					logger.warning("Both image_from_camera and principal_point set", 1)
				if fov_y is not None or aspect_ratio is not None:
					logger.warning("Both image_from_camera and fov_y or aspect_ratio set", 1)

			self.__attrs_init__(
				image_from_camera=image_from_camera,
				resolution=resolution,
				camera_xyz=camera_xyz,
				image_plane_distance=image_plane_distance,
			)

		# Members
		self.image_from_camera = image_from_camera
		self.resolution = resolution
		self.camera_xyz = camera_xyz
		self.image_plane_distance = image_plane_distance
		self.focal_length = focal_length
		self.width = width
		self.height = height
		self.principal_point = principal_point
		self.fov_y = fov_y
		self.aspect_ratio = aspect_ratio

		# field names for serialization
		self._field_names = [
			"image_from_camera",
			"resolution",
			"camera_xyz",
			"image_plane_distance",
		]

		# Mapping of field names to their PyArrow types
		self.field_to_pyarrow_type_map = {
			"image_from_camera": pa.list_(pa.list_(pa.float32(), 3), 3),  # 3x3 matrix
			"resolution": pa.list_(pa.float32(), 2),
			"camera_xyz": pa.list_(pa.float32(), 3),
			"image_plane_distance": pa.float32(),
		}

	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Pinhole instance to a dict of PyArrow arrays.

		Returns a single-row array for the matrix.
		"""
		array_dict: dict[str, pa.Array] = {}
		
		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Mat4X4")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")
			
			arr = np.asarray(field_value)
			if field_name == "image_from_camera":
				if arr.shape != (3, 3):
					raise ValueError(f"image_from_camera must be shape (3, 3), got {arr.shape}")
				
			# Wrap value into a single-row array
			try:
				if field_name == "image_plane_distance":
					array_dict[field_name] = pa.array([field_value], type=pa_type)
				else:
					array_dict[field_name] = pa.array([field_value.tolist()], type=pa_type)
			except Exception:
				raise ValueError(f"Field '{field_name}' value is not convertible to list. Field type is {type(field_value)}")
			
			
		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Pinhole":
		"""
		Reconstruct Pinhole from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected shape:
			image_from_camera: length-1 array containing a 3x3 matrix
			resolution: length-1 array containing a 2D vector
			camera_xyz: length-1 array containing a 3D vector
			image_plane_distance: length-1 array containing a float
		"""
		if "image_from_camera" not in columns:
			raise KeyError("Missing required column 'image_from_camera'")

		# 1. image_from_camera (required)
		pa_image_from_camera = columns["image_from_camera"]
		if len(pa_image_from_camera) != 1:
			raise ValueError(f"'image_from_camera' must have exactly 1 row, got {len(pa_image_from_camera)}")
		image_from_camera_list = pa_image_from_camera[0].as_py()  # [[row0], [row1], [row2], [row3]]
		image_from_camera = np.array(image_from_camera_list, dtype=np.float32)  # shape (3,3)

		# 2. resolution (optional)
		pa_resolution = columns.get("resolution")
		if pa_resolution is not None and len(pa_resolution) != 1:
			raise ValueError(f"'resolution' must have exactly 1 row, got {len(pa_resolution)}")
		if pa_resolution is not None:
			resolution_list = pa_resolution[0].as_py()
			resolution = np.array(resolution_list, dtype=np.float32)

		
		# 3. camera_xyz (optional)
		pa_camera_xyz = columns.get("camera_xyz")
		if pa_camera_xyz is not None and len(pa_camera_xyz) != 1:
			raise ValueError(f"'camera_xyz' must have exactly 1 row, got {len(pa_camera_xyz)}")
		if pa_camera_xyz is not None:
			camera_xyz_list = pa_camera_xyz[0].as_py()
			camera_xyz = np.array(camera_xyz_list, dtype=np.float32)


		# 4. image_plane_distance (optional)
		pa_image_plane_distance = columns.get("image_plane_distance")
		if pa_image_plane_distance is not None and len(pa_image_plane_distance) != 1:
			raise ValueError(f"'image_plane_distance' must have exactly 1 row, got {len(pa_image_plane_distance)}")
		if pa_image_plane_distance is not None:
			image_plane_distance = pa_image_plane_distance[0].as_py()
			image_plane_distance = float(image_plane_distance)

		return cls(image_from_camera=image_from_camera, 
			 resolution=resolution, 
			 camera_xyz=camera_xyz, 
			 image_plane_distance=image_plane_distance)


# ------------------ List related datatypes ------------------
class ListOfPoints3D:
	telekinesis_datatype = "datatypes.datatypes.ListOfPoints3D"
	"""
	List of 3D points of type Points3D.
	"""
	def __init__(self, point3d_list: list["Points3D"]):
		# Type checks
		if not isinstance(point3d_list, list):
			raise TypeError("point3d_list must be a list")
		
		for point in point3d_list:
			if not isinstance(point, Points3D):
				raise TypeError("point3d_list must be a list of Points3D instances")
		
		# Members
		self.point3d_list = point3d_list

		# Field names for serialization
		self._field_names = []
		for i in range(len(point3d_list)):
			self._field_names.append(f"point3d_{i}")


	def to_pyarrow(self) -> dict[str, dict]:
		"""
		Convert this ListOfPoints3D instance to a flat dict of format:
			{
				"point3d_0:position": pa.Array,
				"point3d_0:color":    pa.Array,
				"point3d_1:position": pa.Array,
				"point3d_1:color":    pa.Array,
				...
			}
		Returns a single-row array for each field.
		"""
		array_dict: dict[str, dict] = {}

		for idx, field_name in enumerate(self._field_names):
			if not hasattr(self, "point3d_list"):
				raise ValueError(f"Missing field 'point3d_list' on ListOfPoints3D")

			point3d = self.point3d_list[idx]
			points3d_pyarrow_dict = point3d.to_pyarrow()
			
			# Flatten the dict into a single dict for this point3d list
			for key, value in points3d_pyarrow_dict.items():
				array_dict[f"{field_name}:{key}"] = value
			

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, Any]) -> "ListOfPoints3D":
		"""
		columns: flat dict of the form:
			{
				"point3d_0:position": pa.Array,
				"point3d_0:color":    pa.Array,
				"point3d_1:position": pa.Array,
				"point3d_1:color":    pa.Array,
				...
			}
		"""
		
		# 1. Group by point3d key (point3d_0, point3d_1, ...)
		grouped: dict[str, dict[str, Any]] = defaultdict(dict)

		for key, value in columns.items():
			# column key format: "point3d_{i}:{position|color|normal|intensity|rgba32}"
			try:
				point3d_key, inner_key = key.split(":", 1)
			except ValueError:
				raise ValueError(f"Invalid column key format: {key!r}")

			# Optionally enforce prefix if you want:
			if not point3d_key.startswith("point3d_"):
				logger.warning(f"Skipping non-point3d column: {key}")
				continue

			# Group the inner fields according to their point3d key
			grouped[point3d_key][inner_key] = value

		
		# 2. Reconstruct Points3D objects in a stable order
		point3d_list: list[Points3D] = []

		def _sort_key(k: str) -> int:
			# expects "point3d_0", "point3d_1", ...
			parts = k.split("_")
			if parts and parts[-1].isdigit():
				return int(parts[-1])
			return 0

		for point3d_key in sorted(grouped.keys(), key=_sort_key):
			point3d_dict = grouped[point3d_key]
			
			point3d = Points3D.from_pyarrow(point3d_dict)
			point3d_list.append(point3d)

		return cls(point3d_list=point3d_list)
	
	def to_list(self) -> list["Points3D"]:
		"""Return the list of Points3D."""
		return self.point3d_list
	
	def __len__(self) -> int:
		return len(self.point3d_list)
	
# ------------------ Load from File ------------------
class Asset3D:
	"""
	Generic 3D asset (e.g. .ply, .obj, .glb, .stl, images, etc.)
	Serialized as:
	  - contents: raw bytes
	  - media_type: MIME type string (optional)
	"""
	telekinesis_datatype = "datatypes.datatypes.Asset3D"

	def __init__(
		self,
		path: Optional[Union[str, pathlib.Path, String]] = None,
		contents: Optional[bytes] = None,
		media_type: Optional[str] = None,
	) -> None:
		# --- Type checks ---
		if path is not None and not isinstance(path, (String, str, pathlib.Path)):
			raise TypeError("path must be a string or pathlib.Path")
		if contents is not None and not isinstance(contents, bytes):
			raise TypeError("contents must be bytes")
		if media_type is not None and not isinstance(media_type, str):
			raise TypeError("media_type must be a string")

		# --- Value checks: exactly one of path or contents ---
		if path is None and contents is None:
			raise ValueError("Must provide at least one of 'path' or 'contents'")
		if path is not None and contents is not None:
			raise ValueError("Provide exactly one of 'path' or 'contents', not both")

		# Normalize path to str
		if isinstance(path, String):
			path = path.value
		if isinstance(path, pathlib.Path):
			path = str(path)

		# --- Normalize to bytes ---
		if contents is None:
			# We got a path → read bytes from disk
			new_path = pathlib.Path(path)  # type: ignore[arg-type]
			if not new_path.is_file():
				raise FileNotFoundError(f"Asset3D path does not exist or is not a file: {new_path}")
			contents = new_path.read_bytes()
			if media_type is None:
				media_type = self._guess_media_type_from_path(str(new_path))

		# Members: we always keep bytes, path is optional / informational
		self.path: Optional[str] = path
		self.contents: bytes = contents
		self.media_type: Optional[str] = media_type

		# Field names for serialization
		self._field_names = ["contents", "media_type"]

		# PyArrow types
		self.field_to_pyarrow_type_map: Dict[str, pa.DataType] = {
			"contents": pa.binary(),
			"media_type": pa.string(),
		}

	# ------------------------------------------------------------------
	# Helpers
	# ------------------------------------------------------------------
	def _guess_media_type_from_path(self, path: str) -> Optional[str]:
		ext = pathlib.Path(path).suffix.lower()

		# Images
		if ext in {".jpg", ".jpeg"}:
			return "image/jpeg"
		if ext == ".png":
			return "image/png"

		# 3D models
		if ext == ".glb":
			return "model/gltf-binary"
		if ext == ".gltf":
			return "model/gltf+json"
		if ext == ".obj":
			return "model/obj"
		if ext == ".stl":
			return "model/stl"
		if ext == ".dae":
			return "model/vnd.collada+xml"
		
		# Point clouds
		if ext == ".ply":
			return "point_cloud/ply"

		# Video
		if ext == ".mp4":
			return "video/mp4"

		return None

	# ------------------------------------------------------------------
	# Arrow serialization
	# ------------------------------------------------------------------
	def to_pyarrow(self) -> dict[str, pa.Array]:
		"""
		Convert this Asset3D instance to a dict of PyArrow arrays.
		One row per asset:
		  - contents: binary
		  - media_type: string or null
		"""
		array_dict: dict[str, pa.Array] = {}

		for field_name in self._field_names:
			if not hasattr(self, field_name):
				raise ValueError(f"Missing field '{field_name}' on Asset3D")

			field_value = getattr(self, field_name)
			pa_type = self.field_to_pyarrow_type_map.get(field_name)
			if pa_type is None:
				raise ValueError(f"Unknown field '{field_name}'")

			# Single-row column: [value]
			array_dict[field_name] = pa.array([field_value], type=pa_type)

		return array_dict

	@classmethod
	def from_pyarrow(cls, columns: dict[str, pa.Array]) -> "Asset3D":
		"""
		Reconstruct Asset3D from a dict of PyArrow arrays produced by `to_pyarrow`.

		Expected:
		  contents : binary[1]
		  media_type : string[1] or null
		"""
		# contents (required)
		if "contents" not in columns:
			raise KeyError("Missing required column 'contents'")

		pa_contents = columns["contents"]
		if len(pa_contents) != 1:
			raise ValueError(f"'contents' must have exactly 1 row, got {len(pa_contents)}")

		contents = pa_contents[0].as_py()  # bytes

		# media_type (optional)
		media_type = None
		if "media_type" in columns:
			pa_media_type = columns["media_type"]
			if len(pa_media_type) != 1:
				raise ValueError(f"'media_type' must have exactly 1 row, got {len(pa_media_type)}")
			media_type = pa_media_type[0].as_py()  # str or None

		# Path is intentionally not reconstructed from IPC
		return cls(
			path=None,
			contents=contents,
			media_type=media_type,
		)

# ------------------ Helper datatypes and extensions ------------------
class ChannelDatatypeExt:
	"""
	Extension for [channel_datatype.ChannelDatatype]
	"""

	@staticmethod
	def from_np_dtype(dtype: Any) -> "ChannelDatatype":

		channel_datatype_from_np_dtype = {
			np.uint8: ChannelDatatype.U8,
			np.uint16: ChannelDatatype.U16,
			np.uint32: ChannelDatatype.U32,
			np.uint64: ChannelDatatype.U64,
			np.int8: ChannelDatatype.I8,
			np.int16: ChannelDatatype.I16,
			np.int32: ChannelDatatype.I32,
			np.int64: ChannelDatatype.I64,
			np.float16: ChannelDatatype.F16,
			np.float32: ChannelDatatype.F32,
			np.float64: ChannelDatatype.F64,
		}
		return channel_datatype_from_np_dtype[dtype.type]

	def to_np_dtype(self: Any) -> type:

		channel_datatype_to_np_dtype = {
			ChannelDatatype.U8: np.uint8,
			ChannelDatatype.U16: np.uint16,
			ChannelDatatype.U32: np.uint32,
			ChannelDatatype.U64: np.uint64,
			ChannelDatatype.I8: np.int8,
			ChannelDatatype.I16: np.int16,
			ChannelDatatype.I32: np.int32,
			ChannelDatatype.I64: np.int64,
			ChannelDatatype.F16: np.float16,
			ChannelDatatype.F32: np.float32,
			ChannelDatatype.F64: np.float64,
		}
		return channel_datatype_to_np_dtype[self]

class ChannelDatatype(ChannelDatatypeExt, enum.Enum):
	"""
	The innermost datatype of an image.

	How individual color channel datatypes are encoded.
	"""

	U8 = 6
	"""8-bit unsigned integer."""

	I8 = 7
	"""8-bit signed integer."""

	U16 = 8
	"""16-bit unsigned integer."""

	I16 = 9
	"""16-bit signed integer."""

	U32 = 10
	"""32-bit unsigned integer."""

	I32 = 11
	"""32-bit signed integer."""

	U64 = 12
	"""64-bit unsigned integer."""

	I64 = 13
	"""64-bit signed integer."""

	F16 = 33
	"""16-bit IEEE-754 floating point, also known as `half`."""

	F32 = 34
	"""32-bit IEEE-754 floating point, also known as `float` or `single`."""

	F64 = 35
	"""64-bit IEEE-754 floating point, also known as `double`."""

	@classmethod
	def auto(cls, val: Union[str, int, "ChannelDatatype"]) -> "ChannelDatatype":
		"""Best-effort converter, including a case-insensitive string matcher."""
		if isinstance(val, ChannelDatatype):
			return val
		if isinstance(val, int):
			return cls(val)
		try:
			return cls[val]
		except KeyError:
			val_lower = val.lower()
			for variant in cls:
				if variant.name.lower() == val_lower:
					return variant
		raise ValueError(f"Cannot convert {val} to {cls.__name__}")

	def __str__(self) -> str:
		"""Returns the variant name."""
		return self.name

class ColorModelExt:
	"""
	Extension for [ColorModel].
	"""

	def num_channels(self) -> int:

		"""Returns the number of channels for this color model."""
		if self == ColorModel.L:
			return 1
		elif self in (ColorModel.RGB, ColorModel.BGR):
			return 3
		elif self in (ColorModel.RGBA, ColorModel.BGRA):
			return 4
		else:
			raise ValueError(f"Unknown color model: {self}")

class ColorModel(ColorModelExt, enum.Enum):
	"""
	Specified what color datatypes are present in an [`Image`]

	This combined with [`ChannelDatatype`] determines the pixel format of an image.
	"""

	L = 1
	"""Grayscale luminance intencity/brightness/value, sometimes called `Y`"""

	RGB = 2
	"""Red, Green, Blue"""

	RGBA = 3
	"""Red, Green, Blue, Alpha"""

	BGR = 4
	"""Blue, Green, Red"""

	BGRA = 5
	"""Blue, Green, Red, Alpha"""

	def __str__(self) -> str:
		"""Returns the variant name."""
		return self.name

ColorModelLike = Union[ColorModel, Literal["BGR", "BGRA", "L", "RGB", "RGBA", "bgr", "bgra", "l", "rgb", "rgba"], int]
"""A type alias for any ColorModel-like object."""

ColorModelArrayLike = (
	Union[
	ColorModel,	
	 Literal["BGR", "BGRA", "L", "RGB", "RGBA", "bgr", "bgra", "l", "rgb", "rgba"],
	int,
	Sequence[ColorModelLike]
]
)







