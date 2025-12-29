import pyarrow as pa
import numpy as np
from loguru import logger
from datatypes.datatypes import Points3D, ListOfPoints3D
# Maximum number of points allowed in a point cloud
MAX_POINT_CLOUD_POINTS = 1_000_000
MAX_POINT_CLOUD_BYTES = 16_100_000

def serialize_to_pyarrow_ipc(attribute_data: dict) -> bytes:
    """Serialize attribute data to PyArrow IPC bytes.

    Args:
        attribute_data (dict): A dictionary where keys are attribute names and values are tuples of (data, pyarrow_type).

    Returns:
        bytes: The serialized PyArrow IPC bytes.
    """
    fields = []
    arrays = []

    # Make fields and arrays
    for attribute_name, attribute in attribute_data.items():
        if attribute is None:
            logger.warning(f"Attribute '{attribute_name}' is None, skipping serialization.")
            continue
        
        # Check for point cloud size limits
        if isinstance(attribute, Points3D):
            logger.warning(f"Attribute '{attribute_name}' is a Points3D, checking size limit.")
            if len(attribute.positions) > MAX_POINT_CLOUD_POINTS:
                raise ValueError(
                    f"Point cloud '{attribute_name}' has {len(attribute.positions):,} points, "
                    f"which exceeds the maximum allowed limit of {MAX_POINT_CLOUD_POINTS:,} points."
                )
        elif isinstance(attribute, ListOfPoints3D):
            total_points = 0
            for point3d in attribute.point3d_list:
                total_points += len(point3d.positions)
            if total_points > MAX_POINT_CLOUD_POINTS:
                raise ValueError(
                    f"Point cloud '{attribute_name}' has {total_points:,} points, "
                    f"which exceeds the maximum allowed limit of {MAX_POINT_CLOUD_POINTS:,} points."
                )
        
        pyarrow_dict = attribute.to_pyarrow()

        for field_name, pyarrow_array in pyarrow_dict.items():
            # Make field with metadata and add to arrays
            try:
                fields.append(pa.field(attribute_name+":"+field_name, 
                                       pyarrow_array.type, 
                                       metadata={b'telekinesis_datatype': attribute.telekinesis_datatype.encode('utf8')}))
                arrays.append(pyarrow_array)
            except Exception as e:
                logger.error(f"Error serializing field '{field_name}' of attribute '{attribute_name}': {e}")

    # Build schema from fields
    schema = pa.schema(fields)
    record_batch = pa.RecordBatch.from_arrays(arrays, schema=schema)

    # Write to IPC bytes
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, schema) as writer:
        writer.write_batch(record_batch)

    return sink.getvalue().to_pybytes()

def deserialize_from_pyarrow_ipc(ipc_bytes: bytes) -> dict:
    """Deserialize PyArrow IPC bytes to attribute data.

    Args:
        ipc_bytes (bytes): The serialized PyArrow IPC bytes.

    Returns:
        dict: A dictionary where keys are attribute names and values are attribute instances.
    """
    # Check byte size limit before deserializing
    if len(ipc_bytes) > MAX_POINT_CLOUD_BYTES:
        raise ValueError(
            f"IPC data size ({len(ipc_bytes):,} bytes) exceeds the maximum allowed limit "
            f"of {MAX_POINT_CLOUD_BYTES:,} bytes (equivalent to ~{MAX_POINT_CLOUD_POINTS:,} points)."
        )
    
    buffer = pa.BufferReader(ipc_bytes)
    reader = pa.ipc.open_stream(buffer)
    record_batch = reader.read_next_batch()
    schema = record_batch.schema

    # Group fields by attribute name and telekinesis_datatype
    grouped_fields = {}
    
    for i, field in enumerate(schema):
        full_field_name = field.name
        metadata = field.metadata
        datatype_key = b'telekinesis_datatype'
        
        # Parse attribute_name:field_name
        if ":" in full_field_name:
            attribute_name, field_name = full_field_name.split(":", 1)
        else:
            attribute_name = full_field_name
            field_name = full_field_name

        if metadata and datatype_key in metadata:
            datatype_str = metadata[datatype_key].decode('utf8')
            
            
            # Group by attribute_name
            if attribute_name not in grouped_fields:
                grouped_fields[attribute_name] = {
                    'datatype': datatype_str,
                    'fields': {}
                }
            # Store the field array
            grouped_fields[attribute_name]['fields'][field_name] = record_batch.column(i)
        else:
            logger.warning(f"No datatype metadata found for field '{full_field_name}'")
    
    # Now deserialize each grouped attribute
    attribute_data = {}
    
    for attribute_name, group_info in grouped_fields.items():
        datatype_str = group_info['datatype']
        field_dict = group_info['fields']
        
        # Import the module and get the attribute class
        module_name, class_name = datatype_str.rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        attribute_class = getattr(module, class_name)
        
        # Check if the class has a from_pyarrow method (for complex types like Points3D)
        if hasattr(attribute_class, 'from_pyarrow'):
            # For Points3D, check the size of positions field before deserializing
            if datatype_str == "datatypes.datatypes.Points3D" and "positions" in field_dict:
                positions_array = field_dict["positions"]
                # positions is stored as a length-1 array containing a list of lists [[x,y,z], ...]
                if len(positions_array) > 0:
                    # Get the first (and only) element and convert to Python list
                    positions_list = positions_array[0].as_py()
                    if isinstance(positions_list, list) and len(positions_list) > MAX_POINT_CLOUD_POINTS:
                        raise ValueError(
                            f"Point cloud '{attribute_name}' has {len(positions_list):,} points, "
                            f"which exceeds the maximum allowed limit of {MAX_POINT_CLOUD_POINTS:,} points."
                        )
            
            # Call from_pyarrow with the dictionary of fields
            attribute_instance = attribute_class.from_pyarrow(field_dict)
        else:
            raise NotImplementedError(f"The class '{class_name}' does not implement 'from_pyarrow' method.")
        
        attribute_data[attribute_name] = attribute_instance
    
    return attribute_data