from loguru import logger
import numpy as np
from typing import Optional
import requests
import os

from datatypes import datatypes, serializer
_VITREOUS_API_BASE_URL = "https://api.telekinesis.ai/vitreous/v1/"

def _load_api_key() -> str:
    """
    Load the Telekinesis API key from the environment variable.

    Returns:
        The API key
    """

    api_key = os.getenv("TELEKINESIS_API_KEY")
    if not api_key:
        raise RuntimeError("Telekinesis API key not found.\n\n"
            "Set the TELEKINESIS_API_KEY environment variable.")
    
    return api_key

def _send_request(endpoint: str, input_data: dict) -> dict:
    
    # Serialize using PyArrow IPC
    serialized_bytes = serializer.serialize_to_pyarrow_ipc(input_data)
    
    # Load API Key
    API_KEY = _load_api_key()

    # API Call
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/vnd.apache.arrow.stream",
    }
    
    try:
        response = requests.post(f"{_VITREOUS_API_BASE_URL}{endpoint}",
                                 data=serialized_bytes,
                                 headers=headers,
                                 timeout=130) 
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

    # Deserialize
    status = response.status_code

    if not response.ok:
        # Try to extract a textual error if available
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            error = response.json()
        else:
            error = response.text

        raise RuntimeError(
            f"Request failed [{status}]: {error}"
        )

    # Only deserialize on success
    response_data = serializer.deserialize_from_pyarrow_ipc(response.content)

    return response_data

# Function to demonstrate all datatypes transfer in vitreous module
def _send_all_datatypes(
        param_1: datatypes.Bool | bool,
        param_2: datatypes.Int | int,
        param_3: datatypes.Float | float | int,
        param_4: datatypes.String | str,
        param_5: datatypes.Vector3D | np.ndarray | list[float] = None,
        param_6: datatypes.Vector4D | np.ndarray | list[float] = None,
        param_7: datatypes.Mat4X4 | np.ndarray | list[list[float]] = None,
        param_8: datatypes.Rgba32 | np.ndarray | list[int] = None,
        param_9: datatypes.Image | np.ndarray = None,
        param_10: datatypes.Boxes3D = None,
        param_11: datatypes.Mesh3D = None,
        param_12: datatypes.Points2D = None,
        param_13: datatypes.ListOfPoints3D | list[datatypes.Points3D] = None
):
    '''
    Sends all datatypes to demonstrate datatype transfer in the vitreous module.

    Args:
        param_1: A Bool datatype to test the transfer.
        param_2: An Int datatype to test the transfer.
        param_3: A Float datatype to test the transfer.
        param_4: A String datatype to test the transfer.
        param_5: A Vector3D datatype to test the transfer.
        param_6: A Vector4D datatype to test the transfer.
        param_7: A Mat4X4 datatype to test the transfer.
        param_8: An Rgba32 datatype to test the transfer.
        param_9: An Image datatype to test the transfer.
        param_10: A Boxes3D datatype to test the transfer.
        param_11: A Mesh3D datatype to test the transfer.
        param_12: A Points2D datatype to test the transfer.
        param_13: A ListOfPoints3D datatype to test the transfer.
    '''
    if not isinstance(param_1, (datatypes.Bool, bool)):
        raise TypeError(f"param_1 must be a Bool object, class received: {type(param_1).__name__}")
    
    if not isinstance(param_2, (datatypes.Int, int)):
        raise TypeError(f"param_2 must be an Int object, class received: {type(param_2).__name__}")
    
    if not isinstance(param_3, (datatypes.Float, float, int)):
        raise TypeError(f"param_3 must be a Float, float, or int, class received: {type(param_3).__name__}")
    
    if not isinstance(param_4, (datatypes.String, str)):
        raise TypeError(f"param_4 must be a String object, class received: {type(param_4).__name__}")
    
    if not isinstance(param_5, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(f"param_5 must be a Vector3D, np.ndarray, or list, class received: {type(param_5).__name__}")
    if isinstance(param_5, np.ndarray):
        if param_5.size != 3:
            raise ValueError(f"param_5 numpy array must have exactly 3 elements, got shape {param_5.shape} with {param_5.size} elements")
    elif isinstance(param_5, list):
        if len(param_5) != 3:
            raise ValueError(f"param_5 list must have exactly 3 elements, got {len(param_5)}")
        if not all(isinstance(x, (float, int)) for x in param_5):
            raise ValueError("param_5 list must contain only float or int elements")

    if not isinstance(param_6, (datatypes.Vector4D, np.ndarray, list)):
        raise TypeError(f"param_6 must be a Vector4D, np.ndarray, or list, class received: {type(param_6).__name__}")
    if isinstance(param_6, np.ndarray):
        if param_6.size != 4:
            raise ValueError(f"param_6 numpy array must have exactly 4 elements, got shape {param_6.shape} with {param_6.size} elements")
    elif isinstance(param_6, list):
        if len(param_6) != 4:
            raise ValueError(f"param_6 list must have exactly 4 elements, got {len(param_6)}")
        if not all(isinstance(x, (float, int)) for x in param_6):
            raise ValueError("param_6 list must contain only float or int elements")
    
    if not isinstance(param_7, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(f"param_7 must be a Mat4X4, np.ndarray, or list, class received: {type(param_7).__name__}")
    if isinstance(param_7, np.ndarray):
        if param_7.shape != (4, 4):
            raise ValueError(f"param_7 numpy array must have exactly 4x4 elements, got shape {param_7.shape}")
    elif isinstance(param_7, list):
        if len(param_7) != 4 or not all(len(x) == 4 for x in param_7):
            raise ValueError(f"param_7 list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(param_7)} rows")
        if not all(isinstance(x, (float, int)) for row in param_7 for x in row):
            raise ValueError("param_7 list must contain only float or int elements in all rows")
    
    if not isinstance(param_8, (datatypes.Rgba32, np.ndarray, list)):
        raise TypeError(f"param_8 must be a Rgba32, np.ndarray, or list, class received: {type(param_8).__name__}")
    if isinstance(param_8, np.ndarray):
        if param_8.size != 4 and param_8.size != 3:
            raise ValueError(f"param_8 numpy array must have 3 or 4 elements, got shape {param_8.shape} with {param_8.size} elements")
    elif isinstance(param_8, list):
        if len(param_8) != 3 and len(param_8) != 4:
            raise ValueError(f"param_8 list must have 3 or 4 elements, got {len(param_8)}")
        if not all(isinstance(x, (int,)) for x in param_8):
            raise ValueError("param_8 list must contain only int elements")

    if not isinstance(param_9, (datatypes.Image, np.ndarray, list)):
        raise TypeError(f"param_9 must be an Image, np.ndarray, or list, class received: {type(param_9).__name__}")
    if isinstance(param_9, np.ndarray):
        if len(param_9.shape) < 2 or len(param_9.shape) > 3:
            raise ValueError(f"param_9 numpy array must be 2D (height, width) or 3D (height, width, channels), got shape {param_9.shape}")
        if len(param_9.shape) == 3 and param_9.shape[2] not in (1, 3, 4):
            raise ValueError(f"param_9 numpy array with 3D shape must have 1, 3, or 4 channels, got {param_9.shape[2]} channels")
   
    if not isinstance(param_10, datatypes.Boxes3D):
        raise TypeError(f"param_10 must be a Boxes3D object, class received: {type(param_10).__name__}")
    
    if not isinstance(param_11, datatypes.Mesh3D):
        raise TypeError(f"param_11 must be a Mesh3D object, class received: {type(param_11).__name__}")
    
    if not isinstance(param_12, datatypes.Points2D):
        raise TypeError(f"param_12 must be a Points2D object, class received: {type(param_12).__name__}")
    
    if not isinstance(param_13, (datatypes.ListOfPoints3D, list)):
        raise TypeError(f"param_13 must be a ListOfPoints3D or list, class received: {type(param_13).__name__}")
    if isinstance(param_13, list):
        if not all(isinstance(x, datatypes.Points3D) for x in param_13):
            raise ValueError("param_13 list must contain only Points3D objects")

    if isinstance(param_1, bool):
        param_1 = datatypes.Bool(param_1)
    if isinstance(param_2, int):
        param_2 = datatypes.Int(param_2)
    if isinstance(param_3, (float, int)):
        param_3 = datatypes.Float(param_3)
    if isinstance(param_4, str):
        param_4 = datatypes.String(param_4)
    if isinstance(param_5, np.ndarray):
        param_5 = datatypes.Vector3D(xyz=param_5)
    elif isinstance(param_5, list):
        param_5 = datatypes.Vector3D(xyz=np.array(param_5, dtype=np.float32))
    if isinstance(param_6, np.ndarray):
        param_6 = datatypes.Vector4D(xyzw=param_6)
    elif isinstance(param_6, list):
        param_6 = datatypes.Vector4D(xyzw=np.array(param_6, dtype=np.float32))
    if isinstance(param_7, np.ndarray):
        param_7 = datatypes.Mat4X4(matrix=param_7)
    elif isinstance(param_7, list):
        param_7 = datatypes.Mat4X4(matrix=np.array(param_7, dtype=np.float32))
    if isinstance(param_8, np.ndarray):
        param_8 = datatypes.Rgba32(rgba=param_8)
    elif isinstance(param_8, list):
        param_8 = datatypes.Rgba32(rgba=np.array(param_8, dtype=np.uint8))
    if isinstance(param_9, np.ndarray):
        param_9 = datatypes.Image(image=param_9)
    elif isinstance(param_9, list):
        param_9 = datatypes.Image(image=np.array(param_9, dtype=np.uint8))
    if isinstance(param_13, list):
        param_13 = datatypes.ListOfPoints3D(point3d_list=param_13)
    # Serialize using PyArrow IPC
    input_data = {
        "param_1": param_1,
        "param_2": param_2,
        "param_3": param_3,
        "param_4": param_4,
        "param_5": param_5,
        "param_6": param_6,
        "param_7": param_7,
        "param_8": param_8,
        "param_9": param_9,
        "param_10": param_10,
        "param_11": param_11,
        "param_12": param_12,
        "param_13": param_13
    }

    response_data = _send_request(endpoint="get_all_datatypes", 
                                 input_data=input_data)
    return response_data

# Calculation

def calculate_axis_aligned_bounding_box(
    point_cloud: datatypes.Points3D,
) -> datatypes.Boxes3D:
    """
    Calculate the axis-aligned bounding box (AABB) of a point cloud.

    Args:
        point_cloud: The point cloud to calculate the AABB of.

    Returns:
        A new Boxes3D object containing the AABB of the point cloud.
    """
    # Type checks
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    
    # Prepare input
    input_data = {
        "point_cloud": point_cloud
    }
    
    # Call the API
    end_point = "calculate_axis_aligned_bounding_box"
    response_data = _send_request(endpoint=end_point,
                                   input_data=input_data)

    bounding_box = response_data["bounding_box"]
    return bounding_box


def calculate_oriented_bounding_box(
    point_cloud: datatypes.Points3D,
    minimize_bbox_volume: datatypes.Bool | bool = True,
    use_robust_fitting: datatypes.Bool | bool = True,
) -> datatypes.Boxes3D:
    """
    Calculate the oriented bounding box (OBB) of a point cloud.

    Args:
        point_cloud: The point cloud to calculate the OBB of.
        minimize_bbox_volume: Whether to minimize the volume of the bounding box. When True, the algorithm
            finds the OBB with the smallest possible volume that contains all points, which provides the
            tightest fit. When False, uses a faster but less optimal method. Set to True for accurate
            measurements, False for faster computation. Default: True.
        use_robust_fitting: Whether to use robust fitting that is less sensitive to outliers. When True,
            outliers have less influence on the OBB calculation, resulting in a more stable box that
            better represents the main structure. When False, all points have equal weight, which may
            cause the box to be skewed by outliers. Set to True when the point cloud contains noise or
            outliers, False for clean data. Default: True.

    Returns:
        A new Boxes3D object containing the OBB of the point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(minimize_bbox_volume, (datatypes.Bool, bool)):
        raise TypeError(
            f"minimize_bbox_volume must be a Bool or bool, class received: {type(minimize_bbox_volume).__name__}"
        )
    if not isinstance(use_robust_fitting, (datatypes.Bool, bool)):
        raise TypeError(
            f"use_robust_fitting must be a Bool or bool, class received: {type(use_robust_fitting).__name__}"
        )
    
    if isinstance(minimize_bbox_volume, bool):
        minimize_bbox_volume = datatypes.Bool(minimize_bbox_volume)
    if isinstance(use_robust_fitting, bool):
        use_robust_fitting = datatypes.Bool(use_robust_fitting)

    # Prepare data
    input_data = {
        "point_cloud": point_cloud,
        "minimize_bbox_volume": minimize_bbox_volume,
        "use_robust_fitting": use_robust_fitting
    }

    # Call the API
    end_point = "calculate_oriented_bounding_box"
    response_data = _send_request(endpoint=end_point,
                                   input_data=input_data)

    bounding_box = response_data["bounding_box"]
    return bounding_box


def calculate_plane_normal(
    plane_coefficients: datatypes.Vector4D | np.ndarray | list[float],
) -> np.ndarray:
    """
    Calculate the normal vector of a plane.

    Args:
        plane_coefficients: The plane coefficients to calculate the normal vector of.

    Returns:
        A new Vector3D object containing the normal vector.
    """
    # Type check
    if not isinstance(plane_coefficients, (datatypes.Vector4D, np.ndarray, list)):
        raise TypeError(
            f"plane_coefficients must be a Vector4D, np.ndarray, or list, class received: {type(plane_coefficients).__name__}"
        )
    if isinstance(plane_coefficients, np.ndarray):
        if plane_coefficients.size != 4:
            raise ValueError(f"plane_coefficients numpy array must have exactly 4 elements, got shape {plane_coefficients.shape} with {plane_coefficients.size} elements")
    elif isinstance(plane_coefficients, list):
        if len(plane_coefficients) != 4:
            raise ValueError(f"plane_coefficients list must have exactly 4 elements, got {len(plane_coefficients)}")
        if not all(isinstance(x, (float, int)) for x in plane_coefficients):
            raise ValueError("plane_coefficients list must contain only float or int elements")
    
    if isinstance(plane_coefficients, np.ndarray):
        plane_coefficients = datatypes.Vector4D(xyzw=plane_coefficients)
    elif isinstance(plane_coefficients, list):
        plane_coefficients = datatypes.Vector4D(xyzw=np.array(plane_coefficients, dtype=np.float32))
    
    # Prepare input data
    input_data = {
        "plane_coefficients": plane_coefficients
    }

    # Call the API
    end_point = "calculate_plane_normal"
    response_data = _send_request(endpoint=end_point,
                                   input_data=input_data)

    normal_vector = response_data["plane_normal"]
    return normal_vector.to_numpy()


def calculate_point_cloud_centroid(
    point_cloud: datatypes.Points3D,
) -> np.ndarray:
    """
    Calculate the centroid of a point cloud.

    Args:
        point_cloud: The point cloud to calculate the centroid of.

    Returns:
        A new Position3D object containing the centroid.
    """
    # Type check
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    
    # Prepare input
    input_data = {
        "point_cloud": point_cloud
    }

    # Call the API
    end_point = "calculate_point_cloud_centroid"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)    
    
    centroid = response_data["centroid"]

    return centroid.to_numpy()


def calculate_points_in_point_cloud(
    point_cloud: datatypes.Points3D,
) -> int:
    """
    Calculate the number of points in a point cloud.

    Args:
        point_cloud: The point cloud to calculate the number of points in.

    Returns:
        A new Int object containing the number of points in the point cloud.
    """
    # Type check
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud
    }

    # Call the API
    end_point = "calculate_points_in_point_cloud"
    response_data = _send_request(endpoint=end_point,
                                   input_data=input_data)

    num_points = response_data["num_points"]
    return num_points

# Clustering

def cluster_point_cloud_using_dbscan(
    point_cloud: datatypes.Points3D,
    max_distance: datatypes.Float | float | int = 0.5,
    min_points: datatypes.Int | int = 10,
) -> list[datatypes.Points3D]:
    """
    Cluster a point cloud using the DBSCAN density-based clustering algorithm.

    Args:
        point_cloud: The point cloud to cluster using DBSCAN.
        max_distance: The maximum distance (epsilon) between two points to be considered neighbors, in meters.
            Increasing this value merges more distant points into clusters, creating fewer but larger clusters.
            Decreasing creates more, smaller clusters and may leave more points as noise. Should be set based
            on the typical spacing between points in your point cloud. Typical range: 0.01-1.0 meters.
            For dense point clouds (e.g., from structured light), use 0.01-0.1. For sparse clouds, use 0.1-1.0.
            Default: 0.5.
        min_points: The minimum number of points required to form a dense region (core point requirement).
            Increasing this value requires more points to form a cluster, resulting in fewer clusters and
            more points classified as noise. Decreasing allows smaller groups to form clusters but may
            create clusters from noise. Typical range: 3-50. For small objects, use 3-10. For large
            scenes, use 10-50. Default: 10.

    Returns:
        A list of Points3D objects containing the clustered point clouds.
    """
    # Type checks
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(max_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_distance must be a Float, float, or int, class received: {type(max_distance).__name__}"
        )
    if not isinstance(min_points, (datatypes.Int, int)):
        raise TypeError(
            f"min_points must be an Int or int, class received: {type(min_points).__name__}"
        )
    
    if isinstance(max_distance, (float, int)):
        max_distance = datatypes.Float(max_distance)
    if isinstance(min_points, int):
        min_points = datatypes.Int(min_points)

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "max_distance": max_distance,
        "min_points": min_points
    }

    # Call the API
    end_point = "cluster_point_cloud_using_dbscan"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)
    
    clustered_point_clouds = response_data["clustered_point_clouds"]
    return clustered_point_clouds


def cluster_point_cloud_based_on_density_jump(
    point_cloud: datatypes.Points3D,
    projection_axis: datatypes.Vector3D | np.ndarray | list[float],
    num_nearest_neighbors: datatypes.Int | int = 12,
    neighborhood_radius: datatypes.Float | float | int = 0.001,
    is_point_cloud_linear: datatypes.Bool | bool = False,
) -> list[datatypes.Points3D]:
    """
    Clusters a point cloud into 2 regions based on density discontinuities. Often where volumes change rapidly.


    Args:
        point_cloud: The point cloud to cluster based on density jump.
        projection_axis: The axis to project the point cloud onto. Defines the direction along which
            density changes are analyzed. Set to the principal axis of the point cloud for best results.
            Typical values: [0,0,1] for vertical, [1,0,0] for horizontal along x-axis.
        num_nearest_neighbors: The number of nearest neighbors to use for density estimation at each point.
            Increasing this value makes the density calculation more stable but slower, and may smooth out
            small density changes. Decreasing makes it more sensitive to local variations but may be
            affected by noise. Typical range: 6-30. Default: 12.
        neighborhood_radius: The radius of the spherical neighborhood used for density calculation, in meters.
            Increasing this value considers points from a larger area, making density estimates more
            robust but less sensitive to local changes. Decreasing makes it more sensitive to local
            density variations but may be affected by noise. Should be set based on the scale of your
            point cloud (typically 0.0001 to 0.01 for small objects, 0.01 to 0.1 for larger scenes).
            Default: 0.001.
        is_point_cloud_linear: Whether the point cloud represents a linear structure (e.g., a rod or wire).
            Set to True if the point cloud is approximately one-dimensional, False for 2D or 3D structures.
            When True, the algorithm uses a different density calculation method optimized for linear
            structures. Default: False.

    Returns:
        A list of Points3D objects containing the clustered point clouds.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(projection_axis, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"projection_axis must be a Vector3D, np.ndarray, or list, class received: {type(projection_axis).__name__}"
        )
    if isinstance(projection_axis, np.ndarray):
        if projection_axis.size != 3:
            raise ValueError(f"projection_axis numpy array must have exactly 3 elements, got shape {projection_axis.shape} with {projection_axis.size} elements")
    elif isinstance(projection_axis, list):
        if len(projection_axis) != 3:
            raise ValueError(f"projection_axis list must have exactly 3 elements, got {len(projection_axis)}")
        if not all(isinstance(x, (float, int)) for x in projection_axis):
            raise ValueError("projection_axis list must contain only float or int elements")
    if not isinstance(num_nearest_neighbors, (datatypes.Int, int)):
        raise TypeError(
            f"num_nearest_neighbors must be an Int or int, class received: {type(num_nearest_neighbors).__name__}"
        )
    if not isinstance(neighborhood_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"neighborhood_radius must be a Float, float, or int, class received: {type(neighborhood_radius).__name__}"
        )
    if not isinstance(is_point_cloud_linear, (datatypes.Bool, bool)):
        raise TypeError(
            f"is_point_cloud_linear must be a Bool or bool, class received: {type(is_point_cloud_linear).__name__}"
        )
    
    if isinstance(projection_axis, np.ndarray):
        projection_axis = datatypes.Vector3D(xyz=projection_axis)
    elif isinstance(projection_axis, list):
        projection_axis = datatypes.Vector3D(xyz=np.array(projection_axis, dtype=np.float32))
    if isinstance(num_nearest_neighbors, int):
        num_nearest_neighbors = datatypes.Int(num_nearest_neighbors)
    if isinstance(neighborhood_radius, (float, int)):
        neighborhood_radius = datatypes.Float(neighborhood_radius)
    if isinstance(is_point_cloud_linear, bool):
        is_point_cloud_linear = datatypes.Bool(is_point_cloud_linear)

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "projection_axis": projection_axis,
        "num_nearest_neighbors": num_nearest_neighbors,
        "neighborhood_radius": neighborhood_radius,
        "is_point_cloud_linear": is_point_cloud_linear
    }

    # Call the API
    end_point = "cluster_point_cloud_based_on_density_jump"
    response_data = _send_request(endpoint=end_point,
                                  input_data=input_data)

    clustered_point_clouds = response_data["clustered_point_clouds"]
    return clustered_point_clouds

# Conversion

def convert_mesh_to_point_cloud(
        mesh: datatypes.Mesh3D,
        num_points: datatypes.Int | int = 1000,
        sampling_method: datatypes.String | str = "uniform",
        initial_sampling_factor: datatypes.Int | int = 1,
        initial_point_cloud: datatypes.Points3D = None,
        use_triangle_normal: datatypes.Bool | bool = False,
) -> datatypes.Points3D:

    # Type checks
    if not isinstance(mesh, datatypes.Mesh3D):
        raise TypeError(
            f"mesh must be a Mesh3D object, class received: {type(mesh).__name__}"
        )
    if not isinstance(num_points, (datatypes.Int, int)):
        raise TypeError(
            f"num_points must be an Int or int, class received: {type(num_points).__name__}"
        )
    if not isinstance(sampling_method, (datatypes.String, str)):
        raise TypeError(
            f"sampling_method must be a String or str, class received: {type(sampling_method).__name__}"
        )
    if not isinstance(initial_sampling_factor, (datatypes.Int, int)):
        raise TypeError(
            f"initial_sampling_factor must be an Int or int, class received: {type(initial_sampling_factor).__name__}"
        )
    if initial_point_cloud is not None and not isinstance(initial_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"initial_point_cloud must be a Points3D object, class received: {type(initial_point_cloud).__name__}"
        )
    if not isinstance(use_triangle_normal, (datatypes.Bool, bool)):
        raise TypeError(
            f"use_triangle_normal must be a Bool or bool, class received: {type(use_triangle_normal).__name__}"
        )
    
    if isinstance(num_points, int):
        num_points = datatypes.Int(num_points)
    if isinstance(sampling_method, str):
        sampling_method = datatypes.String(sampling_method)
    if isinstance(initial_sampling_factor, int):
        initial_sampling_factor = datatypes.Int(initial_sampling_factor)
    if isinstance(use_triangle_normal, bool):
        use_triangle_normal = datatypes.Bool(use_triangle_normal)

    # Prepare input data
    input_data = {
        "mesh": mesh,
        "num_points": num_points,
        "sampling_method": sampling_method,
        "initial_sampling_factor": initial_sampling_factor,
        "initial_point_cloud": initial_point_cloud,
        "use_triangle_normal": use_triangle_normal
    }

    # Call the API
    end_point = "convert_mesh_to_point_cloud"
    response_data = _send_request(endpoint=end_point,
                                   input_data=input_data)

    # Get point cloud from response
    point_cloud = response_data["point_cloud"]

    return point_cloud

# Mesh Creation

def create_cylinder_mesh(
    radius: datatypes.Float | float | int = 0.01,
    height: datatypes.Float | float | int = 0.02,
    radial_resolution: datatypes.Int | int = 20,
    height_resolution: datatypes.Int | int = 4,
    retain_base: datatypes.Bool | bool = False,
    vertex_tolerance: datatypes.Float | float | int = 1e-6,
    transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    compute_vertex_normals: datatypes.Bool | bool = True,
) -> datatypes.Mesh3D:
    """
    Creates a parametric cylinder mesh.

    Args:
        radius: The radius of the cylinder in meters. Increasing creates a wider cylinder.
            Typical range: 0.001-1.0 meters. Default: 0.01.

        height: The height of the cylinder along its axis in meters. Increasing creates a taller cylinder.
            Typical range: 0.001-10.0 meters. Default: 0.02.

        radial_resolution: The number of vertices around the circumference (angular resolution).
            Increasing creates a smoother circular cross-section but with more triangles. Decreasing
            creates a more faceted appearance but fewer triangles. Typical range: 8-64. Use 8-16 for
            low-poly, 20-32 for smooth, 32-64 for very smooth. Default: 20.

        height_resolution: The number of vertices along the height (vertical segments).
            Increasing creates more vertical subdivisions, useful for curved or deformed cylinders.
            Decreasing creates fewer segments. Typical range: 2-20. Use 2-4 for simple cylinders,
            4-10 for detailed shapes. Default: 4.

        retain_base: Whether to include the circular base (bottom cap) of the cylinder. When True,
            the cylinder has a closed bottom. When False, the bottom is open. Set to True for solid
            cylinders, False for hollow/open cylinders. Default: False.

        vertex_tolerance: The minimum distance between vertices to avoid duplicate vertices, in meters.
            Increasing allows vertices to be closer together. Decreasing merges vertices that are
            very close. Typical range: 1e-8 to 1e-4. Use smaller values (1e-6 to 1e-8) for high
            precision, larger (1e-4 to 1e-3) for automatic cleanup. Default: 1e-6.

        transformation_matrix: The 4x4 transformation matrix to position and orient the cylinder.
            The cylinder's axis is along the Z-axis by default. Use this to translate, rotate, and scale.

    Returns:
        A new Mesh3D object containing the cylinder mesh.
    """
    if not isinstance(radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"radius must be a Float, float, or int, class received: {type(radius).__name__}"
        )
    if not isinstance(height, (datatypes.Float, float, int)):
        raise TypeError(
            f"height must be a Float, float, or int, class received: {type(height).__name__}"
        )
    if not isinstance(radial_resolution, (datatypes.Int, int)):
        raise TypeError(
            f"radial_resolution must be an Int or int, class received: {type(radial_resolution).__name__}"
        )
    if not isinstance(height_resolution, (datatypes.Int, int)):
        raise TypeError(
            f"height_resolution must be an Int or int, class received: {type(height_resolution).__name__}"
        )
    if not isinstance(retain_base, (datatypes.Bool, bool)):
        raise TypeError(
            f"retain_base must be a Bool or bool, class received: {type(retain_base).__name__}"
        )
    if not isinstance(vertex_tolerance, (datatypes.Float, float, int)):
        raise TypeError(
            f"vertex_tolerance must be a Float, float, or int, class received: {type(vertex_tolerance).__name__}"
        )
    if not isinstance(transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(transformation_matrix).__name__}"
        )
    if isinstance(transformation_matrix, np.ndarray):
        if transformation_matrix.shape != (4, 4):
            raise ValueError(f"transformation_matrix numpy array must have exactly 4x4 elements, got shape {transformation_matrix.shape}")
    elif isinstance(transformation_matrix, list):
        if len(transformation_matrix) != 4 or not all(len(x) == 4 for x in transformation_matrix):
            raise ValueError(f"transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in transformation_matrix for x in row):
            raise ValueError("transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(compute_vertex_normals, (datatypes.Bool, bool)):
        raise TypeError(
            f"compute_vertex_normals must be a Bool or bool, class received: {type(compute_vertex_normals).__name__}"
        )
    
    if isinstance(radius, (float, int)):
        radius = datatypes.Float(radius)
    if isinstance(height, (float, int)):
        height = datatypes.Float(height)
    if isinstance(radial_resolution, int):
        radial_resolution = datatypes.Int(radial_resolution)
    if isinstance(height_resolution, int):
        height_resolution = datatypes.Int(height_resolution)
    if isinstance(retain_base, bool):
        retain_base = datatypes.Bool(retain_base)
    if isinstance(vertex_tolerance, (float, int)):
        vertex_tolerance = datatypes.Float(vertex_tolerance)
    if isinstance(transformation_matrix, np.ndarray):
        transformation_matrix = datatypes.Mat4X4(matrix=transformation_matrix)
    elif isinstance(transformation_matrix, list):
        transformation_matrix = datatypes.Mat4X4(matrix=np.array(transformation_matrix, dtype=np.float32))
    if isinstance(compute_vertex_normals, bool):
        compute_vertex_normals = datatypes.Bool(compute_vertex_normals)
    
    # Prepare input data
    input_data = {
        "radius": radius,
        "height": height,
        "radial_resolution": radial_resolution,
        "height_resolution": height_resolution,
        "retain_base": retain_base,
        "vertex_tolerance": vertex_tolerance,
        "transformation_matrix": transformation_matrix,
        "compute_vertex_normals": compute_vertex_normals
    }

    # Call the API
    end_point = "create_cylinder_mesh"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)    
    
    cylinder_mesh = response_data["cylinder_mesh"]
    return cylinder_mesh


def create_plane_mesh(
    transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    x_dimension: datatypes.Float | float | int = 1.0,
    y_dimension: datatypes.Float | float | int = 1.0,
    z_dimension: datatypes.Float | float | int = 0.01,
    compute_vertex_normals: datatypes.Bool | bool = True
) -> datatypes.Mesh3D:
    """
    Creates a rectangular plane mesh (thin box).

    Args:
        transformation_matrix: The 4x4 transformation matrix to position and orient the plane.
            The plane lies in the XY plane by default, with normal along Z-axis.
        x_dimension: The length of the plane along the X-axis in meters. Increasing creates a wider plane.
            Typical range: 0.001-100.0 meters. Default: 1.0.
        y_dimension: The length of the plane along the Y-axis in meters. Increasing creates a longer plane.
            Typical range: 0.001-100.0 meters. Default: 1.0.
        z_dimension: The thickness of the plane along the Z-axis in meters. Increasing creates a thicker
            plane (more like a box). Decreasing creates a thinner plane. For a true plane, use very small
            values (0.001-0.01). Typical range: 0.001-1.0 meters. Default: 0.01.
        compute_vertex_normals: Whether to compute vertex normals for the plane mesh. When True, vertex normals
            are calculated, which is useful for lighting and rendering. When False, normals are

    Returns:
        A new Mesh3D object containing the plane mesh.
    """
    if not isinstance(transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(transformation_matrix).__name__}"
        )
    if isinstance(transformation_matrix, np.ndarray):
        if transformation_matrix.shape != (4, 4):
            raise ValueError(f"transformation_matrix numpy array must have exactly 4x4 elements, got shape {transformation_matrix.shape}")
    elif isinstance(transformation_matrix, list):
        if len(transformation_matrix) != 4 or not all(len(x) == 4 for x in transformation_matrix):
            raise ValueError(f"transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in transformation_matrix for x in row):
            raise ValueError("transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(x_dimension, (datatypes.Float, float, int)):
        raise TypeError(
            f"x_dimension must be a Float, float, or int, class received: {type(x_dimension).__name__}"
        )
    if not isinstance(y_dimension, (datatypes.Float, float, int)):
        raise TypeError(
            f"y_dimension must be a Float, float, or int, class received: {type(y_dimension).__name__}"
        )
    if not isinstance(z_dimension, (datatypes.Float, float, int)):
        raise TypeError(
            f"z_dimension must be a Float, float, or int, class received: {type(z_dimension).__name__}"
        )
    if not isinstance(compute_vertex_normals, (datatypes.Bool, bool)):
        raise TypeError(
            f"compute_vertex_normals must be a Bool or bool, class received: {type(compute_vertex_normals).__name__}"
        )
    
    if isinstance(transformation_matrix, np.ndarray):
        transformation_matrix = datatypes.Mat4X4(matrix=transformation_matrix)
    elif isinstance(transformation_matrix, list):
        transformation_matrix = datatypes.Mat4X4(matrix=np.array(transformation_matrix, dtype=np.float32))
    if isinstance(x_dimension, (float, int)):
        x_dimension = datatypes.Float(x_dimension)
    if isinstance(y_dimension, (float, int)):
        y_dimension = datatypes.Float(y_dimension)
    if isinstance(z_dimension, (float, int)):
        z_dimension = datatypes.Float(z_dimension)
    if isinstance(compute_vertex_normals, bool):
        compute_vertex_normals = datatypes.Bool(compute_vertex_normals)
    # Prepare input data
    input_data = {
        "transformation_matrix": transformation_matrix,
        "x_dimension": x_dimension,
        "y_dimension": y_dimension,
        "z_dimension": z_dimension,
        "compute_vertex_normals": compute_vertex_normals
    }

    # Call the API
    end_point = "create_plane_mesh"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    plane_mesh = response_data["plane_mesh"]
    return plane_mesh


def create_sphere_mesh(
    transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    radius: datatypes.Float | float | int = 0.01,
    resolution: datatypes.Int | int = 20,
    compute_vertex_normals: datatypes.Bool | bool = True,
) -> datatypes.Mesh3D:
    """
    Create a sphere mesh.

    Args:
        transformation_matrix: The 4x4 transformation matrix to position the sphere. The sphere
            is centered at the translation component of the matrix.
        radius: The radius of the sphere in meters. Increasing creates a larger sphere.
            Typical range: 0.001-100.0 meters. Use 0.001-0.1 for small markers, 0.1-1.0 for
            medium spheres, 1.0-10.0 for large spheres. Default: 0.01.
        resolution: The number of vertices around the sphere (angular resolution). Increasing creates
            a smoother sphere with more triangles. Decreasing creates a more faceted sphere with
            fewer triangles. Typical range: 8-64. Use 8-16 for low-poly spheres, 20-32 for smooth,
            32-64 for very smooth. Default: 20.
        compute_vertex_normals: Whether to compute vertex normals for the sphere mesh. When True,
            vertex normals are calculated, which is useful for lighting and rendering. When False, normals are
            not computed, which may be acceptable for non-rendering uses. Default: True

    Returns:
        A new Mesh3D object containing the sphere mesh.
    """
    # Type checks
    if not isinstance(transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(transformation_matrix).__name__}"
        )
    if isinstance(transformation_matrix, np.ndarray):
        if transformation_matrix.shape != (4, 4):
            raise ValueError(f"transformation_matrix numpy array must have exactly 4x4 elements, got shape {transformation_matrix.shape}")
    elif isinstance(transformation_matrix, list):
        if len(transformation_matrix) != 4 or not all(len(x) == 4 for x in transformation_matrix):
            raise ValueError(f"transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in transformation_matrix for x in row):
            raise ValueError("transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"radius must be a Float, float, or int, class received: {type(radius).__name__}"
        )
    if not isinstance(resolution, (datatypes.Int, int)):
        raise TypeError(
            f"resolution must be an Int or int, class received: {type(resolution).__name__}"
        )
    if not isinstance(compute_vertex_normals, (datatypes.Bool, bool)):
        raise TypeError(
            f"compute_vertex_normals must be a Bool or bool, class received: {type(compute_vertex_normals).__name__}"
        )
    
    if isinstance(transformation_matrix, np.ndarray):
        transformation_matrix = datatypes.Mat4X4(matrix=transformation_matrix)
    elif isinstance(transformation_matrix, list):
        transformation_matrix = datatypes.Mat4X4(matrix=np.array(transformation_matrix, dtype=np.float32))
    if isinstance(radius, (float, int)):
        radius = datatypes.Float(radius)
    if isinstance(resolution, int):
        resolution = datatypes.Int(resolution)
    if isinstance(compute_vertex_normals, bool):
        compute_vertex_normals = datatypes.Bool(compute_vertex_normals)
    # Prepare input data
    input_data = {
        "transformation_matrix": transformation_matrix,
        "radius": radius,
        "resolution": resolution,
        "compute_vertex_normals": compute_vertex_normals
    }

    # Call the API
    end_point = "create_sphere_mesh"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    sphere_mesh = response_data["sphere_mesh"]
    return sphere_mesh


def create_torus_mesh(
    transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    torus_radius: datatypes.Float | float | int = 0.01,
    tube_radius: datatypes.Float | float | int = 0.005,
    radial_resolution: datatypes.Int | int = 20,
    tubular_resolution: datatypes.Int | int = 10,
    compute_vertex_normals: datatypes.Bool | bool = True
) -> datatypes.Mesh3D:
    """
    Create a torus mesh.

    Args:
        transformation_matrix: The 4x4 transformation matrix to position and orient the torus.
            The torus lies in the XY plane by default, with the hole along the Z-axis.
        torus_radius: The major radius (distance from center to tube center) in meters.
            Increasing creates a larger torus. Must be greater than tube_radius. Typical range:
            0.001-1.0 meters. Default: 0.01.
        tube_radius: The minor radius (radius of the circular cross-section of the tube) in meters.
            Increasing creates a thicker tube. Must be less than torus_radius. Typical range:
            0.0005-0.5 meters. Default: 0.005.
        radial_resolution: The number of vertices around the major circle (torus circumference).
            Increasing creates a smoother torus but with more triangles. Decreasing creates a
            more faceted appearance. Typical range: 8-64. Use 8-16 for low-poly, 20-32 for smooth,
            32-64 for very smooth. Default: 20.
        tubular_resolution: The number of vertices around the minor circle (tube cross-section).
            Increasing creates a smoother tube but with more triangles. Decreasing creates a more
            faceted tube. Typical range: 6-32. Use 6-10 for low-poly, 10-20 for smooth,
            20-32 for very smooth. Default: 10.
        compute_vertex_normals: Whether to compute vertex normals for the torus mesh. When True,
            vertex normals are calculated, which is useful for lighting and rendering. When False, normals are
            not computed, which may be acceptable for non-rendering uses. Default: True

    Returns:
        A new Mesh3D object containing the torus mesh.
    """
    # Type checks
    if not isinstance(transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(transformation_matrix).__name__}"
        )
    if isinstance(transformation_matrix, np.ndarray):
        if transformation_matrix.shape != (4, 4):
            raise ValueError(f"transformation_matrix numpy array must have exactly 4x4 elements, got shape {transformation_matrix.shape}")
    elif isinstance(transformation_matrix, list):
        if len(transformation_matrix) != 4 or not all(len(x) == 4 for x in transformation_matrix):
            raise ValueError(f"transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in transformation_matrix for x in row):
            raise ValueError("transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(torus_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"torus_radius must be a Float, float, or int, class received: {type(torus_radius).__name__}"
        )
    if not isinstance(tube_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"tube_radius must be a Float, float, or int, class received: {type(tube_radius).__name__}"
        )
    if not isinstance(radial_resolution, (datatypes.Int, int)):
        raise TypeError(
            f"radial_resolution must be an Int or int, class received: {type(radial_resolution).__name__}"
        )
    if not isinstance(tubular_resolution, (datatypes.Int, int)):
        raise TypeError(
            f"tubular_resolution must be an Int or int, class received: {type(tubular_resolution).__name__}"
        )
    if not isinstance(compute_vertex_normals, (datatypes.Bool, bool)):
        raise TypeError(
            f"compute_vertex_normals must be a Bool or bool, class received: {type(compute_vertex_normals).__name__}"
        )
    
    if isinstance(transformation_matrix, np.ndarray):
        transformation_matrix = datatypes.Mat4X4(matrix=transformation_matrix)
    elif isinstance(transformation_matrix, list):
        transformation_matrix = datatypes.Mat4X4(matrix=np.array(transformation_matrix, dtype=np.float32))
    if isinstance(torus_radius, (float, int)):
        torus_radius = datatypes.Float(torus_radius)
    if isinstance(tube_radius, (float, int)):
        tube_radius = datatypes.Float(tube_radius)
    if isinstance(radial_resolution, int):
        radial_resolution = datatypes.Int(radial_resolution)
    if isinstance(tubular_resolution, int):
        tubular_resolution = datatypes.Int(tubular_resolution)
    if isinstance(compute_vertex_normals, bool):
        compute_vertex_normals = datatypes.Bool(compute_vertex_normals)
    # Prepare input data
    input_data = {
        "transformation_matrix": transformation_matrix,
        "torus_radius": torus_radius,
        "tube_radius": tube_radius,
        "radial_resolution": radial_resolution,
        "tubular_resolution": tubular_resolution,
        "compute_vertex_normals": compute_vertex_normals,
    }

    # Call the API
    end_point = "create_torus_mesh"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    torus_mesh = response_data["torus_mesh"]
    return torus_mesh

# Estimation examples

def estimate_principal_axis_within_radius(
    point_cloud: datatypes.Points3D,
    neighborhood_radius: datatypes.Float | float | int = 1,
    reference_point: datatypes.Vector3D | np.ndarray | list[float] = np.array([0.0, 0.0, 0.0]),
) -> np.ndarray:
    """
    Estimate the principal axis within a radius of a point cloud.

    Computes the dominant direction (principal axis) of points within a spherical neighborhood
    around a reference point. Useful for analyzing local orientation in a point cloud.

    Args:
        point_cloud: The point cloud to estimate the principal axis of. Should contain points
            with a dominant direction near the reference_point.
        neighborhood_radius: The radius of the spherical neighborhood in meters. Increasing
            considers more points, providing a more global principal axis but may include
            points from different regions. Decreasing uses fewer points, giving a more local
            principal axis. Should be set based on the scale of features you want to analyze.
            Typical range: 0.1-10.0 meters. Use 0.1-1.0 for local features, 1.0-5.0 for
            regional, 5.0-10.0 for global. Default: 1.0.
        reference_point: The 3D center point in meters around which to analyze the neighborhood.
            Only points within neighborhood_radius of this point are used for principal axis
            estimation. Typically set to a point of interest or the center of a region to analyze.
            Default: [0.0, 0.0, 0.0] (origin).

    Returns:
        A new Vector3D object containing the normalized principal axis direction vector.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(neighborhood_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"neighborhood_radius must be a Float, float, or int, class received: {type(neighborhood_radius).__name__}"
        )
    if not isinstance(reference_point, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"reference_point must be a Vector3D, np.ndarray, or list, class received: {type(reference_point).__name__}"
        )
    if isinstance(reference_point, np.ndarray):
        if reference_point.size != 3:
            raise ValueError(f"reference_point numpy array must have exactly 3 elements, got shape {reference_point.shape} with {reference_point.size} elements")
    elif isinstance(reference_point, list):
        if len(reference_point) != 3:
            raise ValueError(f"reference_point list must have exactly 3 elements, got {len(reference_point)}")
        if not all(isinstance(x, (float, int)) for x in reference_point):
            raise ValueError("reference_point list must contain only float or int elements")
    
    if isinstance(neighborhood_radius, (float, int)):
        neighborhood_radius = datatypes.Float(neighborhood_radius)
    if isinstance(reference_point, np.ndarray):
        reference_point = datatypes.Vector3D(xyz=reference_point)
    elif isinstance(reference_point, list):
        reference_point = datatypes.Vector3D(xyz=np.array(reference_point, dtype=np.float32))
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "neighborhood_radius": neighborhood_radius,
        "reference_point": reference_point
    }

    # Call the API
    end_point = "estimate_principal_axis_within_radius"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    principal_axis = response_data["principal_axis"]
    return principal_axis.to_numpy()


def estimate_principal_axes(
    point_cloud: datatypes.Points3D, method: datatypes.String | str = "obb"
) -> np.ndarray:
    """
    Estimate the principal axes of a point cloud.

    Computes the three principal axes (directions of maximum variance) of the entire point cloud.
    These axes represent the dominant orientations of the point cloud.

    Args:
        point_cloud: The point cloud to estimate the principal axes of. The algorithm analyzes
            all points in the cloud to find the dominant directions.
        method: The method to use for principal axis estimation. Options: "obb" (oriented bounding
            box) or "pca" (principal component analysis). "obb" uses the oriented bounding box
            axes, which may be more robust to outliers. "pca" uses principal component analysis,
            which is faster but more sensitive to outliers. Use "obb" for robust results with
            noisy data, "pca" for fast computation with clean data. Default: "obb".

    Returns:
        A new Vector3D object containing the principal axes (typically the first principal axis,
        though the exact return format may vary by implementation).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(method, (datatypes.String, str)):
        raise TypeError(
            f"method must be a String or str, class received: {type(method).__name__}"
        )
    
    if isinstance(method, str):
        method = datatypes.String(method)
    if method.value not in ["obb", "pca"]:
        raise ValueError(
            f"method must be either 'obb' or 'pca', received: {method.value}"
        )
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "method": method
    }

    # Call the API
    end_point = "estimate_principal_axes"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)

    principal_axes = response_data["principal_axes"]
    return principal_axes.to_numpy()

# Filtering examples

def filter_point_cloud_using_pass_through_filter(
    point_cloud: datatypes.Points3D,
    x_min: datatypes.Float | float | int = -100.0,
    x_max: datatypes.Float | float | int = 100.0,
    y_min: datatypes.Float | float | int = -100.0,
    y_max: datatypes.Float | float | int = 100.0,
    z_min: datatypes.Float | float | int = -100.0,
    z_max: datatypes.Float | float | int = 100.0,
) -> datatypes.Points3D:
    """
    Filters points within axis-aligned min/max ranges using a pass-through filter.

    Keeps only points where each coordinate (x, y, z) falls within specified
    min/max bounds. Creates a rectangular box filter aligned with the coordinate axes.

    Args:
        point_cloud: The point cloud to filter.
        x_min: Minimum x coordinate in meters. Points with x < x_min are removed. Increasing
            includes more points (expands the box in negative x direction). Should be less than
            x_max. Typical range: -100.0 to 100.0 meters depending on scene scale. Default: -100.0.
        x_max: Maximum x coordinate in meters. Points with x > x_max are removed. Increasing
            includes more points (expands the box in positive x direction). Should be greater
            than x_min. Typical range: -100.0 to 100.0 meters. Default: 100.0.
        y_min: Minimum y coordinate in meters. Points with y < y_min are removed. Increasing
            includes more points. Should be less than y_max. Typical range: -100.0 to 100.0 meters.
            Default: -100.0.
        y_max: Maximum y coordinate in meters. Points with y > y_max are removed. Increasing
            includes more points. Should be greater than y_min. Typical range: -100.0 to 100.0 meters.
            Default: 100.0.
        z_min: Minimum z coordinate in meters. Points with z < z_min are removed. Increasing
            includes more points. Should be less than z_max. Typical range: -100.0 to 100.0 meters.
            Default: -100.0.
        z_max: Maximum z coordinate in meters. Points with z > z_max are removed. Increasing
            includes more points. Should be greater than z_min. Typical range: -100.0 to 100.0 meters.
            Default: 100.0.

    Returns:
        A new Points3D object containing the filtered point cloud (points within the box).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(x_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"x_min must be a Float, float, or int, class received: {type(x_min).__name__}"
        )
    if not isinstance(x_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"x_max must be a Float, float, or int, class received: {type(x_max).__name__}"
        )
    if not isinstance(y_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"y_min must be a Float, float, or int, class received: {type(y_min).__name__}"
        )
    if not isinstance(y_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"y_max must be a Float, float, or int, class received: {type(y_max).__name__}"
        )
    if not isinstance(z_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"z_min must be a Float, float, or int, class received: {type(z_min).__name__}"
        )
    if not isinstance(z_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"z_max must be a Float, float, or int, class received: {type(z_max).__name__}"
        )

    if isinstance(x_min, (float, int)):
        x_min = datatypes.Float(x_min)
    if isinstance(x_max, (float, int)):
        x_max = datatypes.Float(x_max)
    if isinstance(y_min, (float, int)):
        y_min = datatypes.Float(y_min)
    if isinstance(y_max, (float, int)):
        y_max = datatypes.Float(y_max)
    if isinstance(z_min, (float, int)):
        z_min = datatypes.Float(z_min)
    if isinstance(z_max, (float, int)):
        z_max = datatypes.Float(z_max)

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max
    }

    # Call the API
    end_point = "filter_point_cloud_using_pass_through_filter"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)  
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_bounding_box(
    point_cloud: datatypes.Points3D, bbox: datatypes.Boxes3D
) -> datatypes.Points3D:
    """
    Filter a point cloud using a bounding box. Keeps only points that fall within the specified 3D box.

    Args:
        point_cloud: The point cloud to filter.
        bbox: The bounding box to use for the filtering.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(bbox, datatypes.Boxes3D):
        raise TypeError(
            f"oriented_bbox must be a Boxes3D object, class received: {type(bbox).__name__}"
        )
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "bbox": bbox,
    }

    # Call the API
    end_point = "filter_point_cloud_using_bounding_box"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)

    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_cylinder_base_removal(
    mesh: datatypes.Mesh3D,
    distance_threshold: datatypes.Float | float | int = 0.01,
    compute_vertex_normals: datatypes.Bool | bool = True
) -> datatypes.Mesh3D:
    """
    Filter a mesh by removing cylinder base regions.

    Removes mesh vertices and faces that are near the base of a cylindrical object,
    effectively cutting off the bottom of a cylinder.

    Args:
        mesh: The mesh to filter. Should represent a cylindrical object (e.g., a rod or pipe).
        distance_threshold: The maximum distance from the detected base to remove vertices,
            in meters. Increasing removes more of the base region (thicker cut). Decreasing
            removes less (thinner cut). Should be set based on the cylinder's size and desired
            cut depth. Typical range: 0.001-0.1 meters. Use 0.001-0.01 for precise removal,
            0.01-0.05 for moderate, 0.05-0.1 for aggressive. Default: 0.01.

    Returns:
        A new Mesh3D object containing the filtered mesh with base regions removed.
    """
    if not isinstance(mesh, datatypes.Mesh3D):
        raise TypeError(
            f"mesh must be a Mesh3D object, class received: {type(mesh).__name__}"
        )
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    if not isinstance(compute_vertex_normals, (datatypes.Bool, bool)):
        raise TypeError(
            f"compute_vertex_normals must be a Bool or bool, class received: {type(compute_vertex_normals).__name__}"
        )

    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    if isinstance(compute_vertex_normals, bool):
        compute_vertex_normals = datatypes.Bool(compute_vertex_normals)
    # Prepare input data
    input_data = {
        "mesh": mesh,
        "distance_threshold": distance_threshold,
        "compute_vertex_normals": compute_vertex_normals
    }

    # Call the API
    end_point = "filter_point_cloud_using_cylinder_base_removal"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    filtered_mesh = response_data["filtered_mesh"]
    return filtered_mesh


def filter_point_cloud_using_mask(
    point_cloud: datatypes.Points3D,
    mask: datatypes.Image | np.ndarray | list,
) -> datatypes.Points3D:
    """
    Filters a structured point cloud using a 2D binary mask.

    Applies a 2D image mask to an organized point cloud, keeping only points
    where the corresponding pixel is True.

    Args:
        point_cloud: The point cloud to filter.
        mask: The 2D binary mask array.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(mask, (datatypes.Image, np.ndarray, list)):
        raise TypeError(
            f"mask must be an Image, np.ndarray, or list, class received: {type(mask).__name__}"
        )
    
    if isinstance(mask, np.ndarray):
        mask = datatypes.Image(image=mask)
    elif isinstance(mask, list):
        mask = datatypes.Image(image=np.array(mask))
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "mask": mask,
    }

    # Call the API
    end_point = "filter_point_cloud_using_mask"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_oriented_bounding_box(
    point_cloud: datatypes.Points3D, oriented_bbox: datatypes.Boxes3D
) -> datatypes.Points3D:
    """
    Filter a point cloud using an oriented bounding box.
    Keeps only points that fall within the specified 3D box that can be rotated to any orientation.
    Args:
        point_cloud: The point cloud to filter.
        oriented_bbox: The oriented bounding box to use for the filtering.
    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(oriented_bbox, datatypes.Boxes3D):
        raise TypeError(
            f"oriented_bbox must be a Boxes3D object, class received: {type(oriented_bbox).__name__}"
        )
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "oriented_bbox": oriented_bbox,
    }

    # Call the API
    end_point = "filter_point_cloud_using_oriented_bounding_box"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_plane_defined_by_point_normal_proximity(
    point_cloud: datatypes.Points3D,
    plane_point: datatypes.Vector3D | np.ndarray | list[float],
    plane_normal: datatypes.Vector3D | np.ndarray | list[float],
    distance_threshold: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Filters points near a plane defined by a point and normal vector.

    Keeps points within a distance threshold of a plane specified by a point
    on the plane and its normal vector.

    Args:
        point_cloud: The point cloud to filter.
        plane_point: A 3D point that lies on the plane, in meters. Defines the plane's position in space.
            Any point on the plane can be used. Typically set to a point you know lies on the plane
            (e.g., from plane fitting or manual selection).
        plane_normal: The normal vector of the plane (perpendicular to the plane surface). Should be
            normalized (unit vector). Defines the plane's orientation. For horizontal planes, use [0,0,1]
            or [0,0,-1]. For vertical planes, use [1,0,0], [0,1,0], etc. The direction (positive/negative)
            determines which side of the plane is considered "positive".
        distance_threshold: The maximum perpendicular distance from the plane to keep a point, in meters.
            Increasing this value keeps points farther from the plane, including points on nearby parallel
            surfaces. Decreasing keeps only points very close to the plane. Typical range: 0.001-0.1 meters.
            For precise plane extraction, use 0.001-0.01. For filtering near a plane, use 0.01-0.1.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(plane_point, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"plane_point must be a Vector3D, np.ndarray, or list, class received: {type(plane_point).__name__}"
        )
    if isinstance(plane_point, np.ndarray):
        if plane_point.size != 3:
            raise ValueError(f"plane_point numpy array must have exactly 3 elements, got shape {plane_point.shape} with {plane_point.size} elements")
    elif isinstance(plane_point, list):
        if len(plane_point) != 3:
            raise ValueError(f"plane_point list must have exactly 3 elements, got {len(plane_point)}")
        if not all(isinstance(x, (float, int)) for x in plane_point):
            raise ValueError("plane_point list must contain only float or int elements")
    if not isinstance(plane_normal, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"plane_normal must be a Vector3D, np.ndarray, or list, class received: {type(plane_normal).__name__}"
        )
    if isinstance(plane_normal, np.ndarray):
        if plane_normal.size != 3:
            raise ValueError(f"plane_normal numpy array must have exactly 3 elements, got shape {plane_normal.shape} with {plane_normal.size} elements")
    elif isinstance(plane_normal, list):
        if len(plane_normal) != 3:
            raise ValueError(f"plane_normal list must have exactly 3 elements, got {len(plane_normal)}")
        if not all(isinstance(x, (float, int)) for x in plane_normal):
            raise ValueError("plane_normal list must contain only float or int elements")
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    
    if isinstance(plane_point, np.ndarray):
        plane_point = datatypes.Vector3D(xyz=plane_point)
    elif isinstance(plane_point, list):
        plane_point = datatypes.Vector3D(xyz=np.array(plane_point, dtype=np.float32))
    if isinstance(plane_normal, np.ndarray):
        plane_normal = datatypes.Vector3D(xyz=plane_normal)
    elif isinstance(plane_normal, list):
        plane_normal = datatypes.Vector3D(xyz=np.array(plane_normal, dtype=np.float32))
    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "plane_point": plane_point,
        "plane_normal": plane_normal,
        "distance_threshold": distance_threshold
    }

    # Call the API
    end_point = "filter_point_cloud_using_plane_defined_by_point_normal_proximity"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_plane_proximity(
    point_cloud: datatypes.Points3D,
    plane_coefficients: datatypes.Vector4D | np.ndarray | list[float],
    distance_threshold: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Filters points near a plane defined by coefficients.

    Keeps points within a distance threshold of a plane specified by its
    equation coefficients (ax + by + cz + d = 0).

    Args:
        point_cloud: The point cloud to filter.
        plane_coefficients: The plane equation coefficients as [a, b, c, d] where ax + by + cz + d = 0.
            The vector [a, b, c] is the plane normal (should be normalized), and d is the distance from
            origin. Can be obtained from plane fitting algorithms. For a horizontal plane at z=0.5,
            use [0, 0, 1, -0.5]. For a plane through origin with normal [1,0,0], use [1, 0, 0, 0].
        distance_threshold: The maximum perpendicular distance from the plane to keep a point, in meters.
            Increasing this value keeps points farther from the plane, including points on nearby parallel
            surfaces. Decreasing keeps only points very close to the plane. Typical range: 0.001-0.1 meters.
            For precise plane extraction, use 0.001-0.01. For filtering near a plane, use 0.01-0.1.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(plane_coefficients, (datatypes.Vector4D, np.ndarray, list)):
        raise TypeError(
            f"plane_coefficients must be a Vector4D, np.ndarray, or list, class received: {type(plane_coefficients).__name__}"
        )
    if isinstance(plane_coefficients, np.ndarray):
        if plane_coefficients.size != 4:
            raise ValueError(f"plane_coefficients numpy array must have exactly 4 elements, got shape {plane_coefficients.shape} with {plane_coefficients.size} elements")
    elif isinstance(plane_coefficients, list):
        if len(plane_coefficients) != 4:
            raise ValueError(f"plane_coefficients list must have exactly 4 elements, got {len(plane_coefficients)}")
        if not all(isinstance(x, (float, int)) for x in plane_coefficients):
            raise ValueError("plane_coefficients list must contain only float or int elements")
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    
    if isinstance(plane_coefficients, np.ndarray):
        plane_coefficients = datatypes.Vector4D(xyzw=plane_coefficients)
    elif isinstance(plane_coefficients, list):
        plane_coefficients = datatypes.Vector4D(xyzw=np.array(plane_coefficients, dtype=np.float32))
    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "plane_coefficients": plane_coefficients,
        "distance_threshold": distance_threshold
    }

    # Call the API
    end_point = "filter_point_cloud_using_plane_proximity"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_plane_splitting(
    point_cloud: datatypes.Points3D,
    plane_coefficients: datatypes.Vector4D | np.ndarray | list[float],
    keep_positive_side: datatypes.Bool | bool,
) -> datatypes.Points3D:
    """
    Splits a point cloud by a plane, keeping one side.

    Divides a point cloud using a plane and keeps points on either the positive
    or negative side. Useful for cutting a point cloud in half along a plane.

    Args:
        point_cloud: The point cloud to filter.
        plane_coefficients: The plane equation coefficients as [a, b, c, d] where ax + by + cz + d = 0.
            The vector [a, b, c] is the plane normal (should be normalized), and d is the distance
            from origin. The sign of (ax + by + cz + d) determines which side a point is on.
            Can be obtained from plane fitting algorithms.
        keep_positive_side: Whether to keep points on the positive side of the plane. When True,
            keeps points where (ax + by + cz + d) > 0. When False, keeps points where
            (ax + by + cz + d) < 0. Set to True to keep points in the direction of the normal
            vector, False to keep points opposite to the normal. The choice depends on which
            half-space you want to retain.

    Returns:
        A new Points3D object containing the filtered point cloud (points on the selected side).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(plane_coefficients, (datatypes.Vector4D, np.ndarray, list)):
        raise TypeError(
            f"plane_coefficients must be a Vector4D, np.ndarray, or list, class received: {type(plane_coefficients).__name__}"
        )
    if isinstance(plane_coefficients, np.ndarray):
        if plane_coefficients.size != 4:
            raise ValueError(f"plane_coefficients numpy array must have exactly 4 elements, got shape {plane_coefficients.shape} with {plane_coefficients.size} elements")
    elif isinstance(plane_coefficients, list):
        if len(plane_coefficients) != 4:
            raise ValueError(f"plane_coefficients list must have exactly 4 elements, got {len(plane_coefficients)}")
        if not all(isinstance(x, (float, int)) for x in plane_coefficients):
            raise ValueError("plane_coefficients list must contain only float or int elements")
    if not isinstance(keep_positive_side, (datatypes.Bool, bool)):
        raise TypeError(
            f"keep_positive_side must be a Bool or bool, class received: {type(keep_positive_side).__name__}"
        )
    
    if isinstance(plane_coefficients, np.ndarray):
        plane_coefficients = datatypes.Vector4D(xyzw=plane_coefficients)
    elif isinstance(plane_coefficients, list):
        plane_coefficients = datatypes.Vector4D(xyzw=np.array(plane_coefficients, dtype=np.float32))
    if isinstance(keep_positive_side, bool):
        keep_positive_side = datatypes.Bool(keep_positive_side)

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "plane_coefficients": plane_coefficients,
        "keep_positive_side": keep_positive_side
    }

    # Call the API
    end_point = "filter_point_cloud_using_plane_splitting"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)  
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_radius_outlier_removal(
    point_cloud: datatypes.Points3D,
    num_points: datatypes.Int | int,
    neighborhood_radius: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Removes points with too few neighbors within a radius.

    Removes points that have fewer than a specified number of neighbors within
    a given radius.

    Args:
        point_cloud: The point cloud to filter.
        num_points: The minimum number of neighbors required within the radius for a point to be kept.
            Increasing this value removes more points (stricter filtering), keeping only points in dense
            regions. Decreasing keeps more points but may retain some outliers. Typical range: 3-20.
            For dense point clouds, use 5-10. For sparse clouds, use 3-5. Set based on expected
            local point density.
        neighborhood_radius: The search radius in meters for finding neighbors around each point.
            Increasing this value considers a larger area, making the filter less sensitive to local
            density variations but may remove valid points in sparse regions. Decreasing makes it more
            sensitive to local density but may miss outliers in sparse areas. Should be set to 2-3x
            the typical point spacing in your cloud. Typical range: 0.01-0.1 meters for small objects,
            0.1-1.0 for larger scenes.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(num_points, (datatypes.Int, int)):
        raise TypeError(
            f"num_points must be an Int or int, class received: {type(num_points).__name__}"
        )
    if not isinstance(neighborhood_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"neighborhood_radius must be a Float, float, or int, class received: {type(neighborhood_radius).__name__}"
        )
    
    if isinstance(num_points, int):
        num_points = datatypes.Int(num_points)
    if isinstance(neighborhood_radius, (float, int)):
        neighborhood_radius = datatypes.Float(neighborhood_radius)
    
    input_data = {
        "point_cloud": point_cloud,
        "num_points": num_points,
        "neighborhood_radius": neighborhood_radius
    }
    end_point = "filter_point_cloud_using_radius_outlier_removal"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_statistical_outlier_removal(
    point_cloud: datatypes.Points3D,
    num_neighbors: datatypes.Int | int,
    standard_deviation_ratio: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Removes statistical outliers based on distance distribution.

    Removes points that are farther than a threshold from their neighbors,
    where the threshold is computed from mean distance and standard deviation.

    Args:
        point_cloud: The point cloud to filter.
        num_neighbors: The number of nearest neighbors used to compute mean distance for each point.
            Increasing this value provides more stable distance statistics but is slower and may smooth
            out local variations. Decreasing is faster but may be more sensitive to noise. Typical
            range: 10-50. For dense clouds, use 20-50. For sparse clouds, use 10-20. Default: 20.
        standard_deviation_ratio: The multiplier for standard deviation to determine the outlier threshold.
            Points with mean distance > (mean + ratio * std_dev) are removed. Increasing this value
            removes fewer points (more lenient), keeping points that are moderately far from neighbors.
            Decreasing removes more points (stricter), keeping only points very close to their neighbors.
            Typical range: 0.5-3.0. Use 1.0-2.0 for moderate filtering, 2.0-3.0 for light filtering,
            0.5-1.0 for aggressive filtering. Default: 2.0.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(num_neighbors, (datatypes.Int, int)):
        raise TypeError(
            f"num_neighbors must be an Int or int, class received: {type(num_neighbors).__name__}"
        )
    if not isinstance(standard_deviation_ratio, (datatypes.Float, float, int)):
        raise TypeError(
            f"standard_deviation_ratio must be a Float, float, or int, class received: {type(standard_deviation_ratio).__name__}"
        )
    
    if isinstance(num_neighbors, int):
        num_neighbors = datatypes.Int(num_neighbors)
    if isinstance(standard_deviation_ratio, (float, int)):
        standard_deviation_ratio = datatypes.Float(standard_deviation_ratio)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "num_neighbors": num_neighbors,
        "standard_deviation_ratio": standard_deviation_ratio
    }

    # Call the API
    end_point = "filter_point_cloud_using_statistical_outlier_removal"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_uniform_downsampling(
    point_cloud: datatypes.Points3D,
    step_size: datatypes.Int | int,
) -> datatypes.Points3D:
    """
    Downsamples a point cloud by selecting every Nth point.

    Uniformly samples points by selecting every step_size-th point from the
    original cloud.

    Args:
        point_cloud: The point cloud to downsample.
        step_size: The interval for selecting points (selects every Nth point). Increasing this value
            reduces the number of points more aggressively, creating a sparser point cloud. Decreasing
            keeps more points, preserving more detail. The output will have approximately
            (original_count / step_size) points. Typical range: 2-100. Use 2-5 for light downsampling,
            5-20 for moderate, 20-100 for aggressive. Must be >= 1. Default: 10.

    Returns:
        A new Points3D object containing the downsampled point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(step_size, (datatypes.Int, int)):
        raise TypeError(
            f"step_size must be an Int or int, class received: {type(step_size).__name__}"
        )
    
    if isinstance(step_size, int):
        step_size = datatypes.Int(step_size)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "step_size": step_size
    }

    # Call the API
    end_point = "filter_point_cloud_using_uniform_downsampling"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_viewpoint_visibility(
    point_cloud: datatypes.Points3D,
    viewpoint: datatypes.Vector3D | np.ndarray | list[float],
    visibility_radius: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Filters points based on visibility from a camera viewpoint.

    Removes points that are occluded or outside the visibility range from
    a specified camera position.

    Args:
        point_cloud: The point cloud to filter.
        viewpoint: The 3D position of the camera/viewpoint in world coordinates, in meters.
            Points are tested for visibility from this location. Set to the camera's position
            when the point cloud was captured.
        visibility_radius: The maximum distance from the viewpoint to consider points visible, in meters.
            Increasing this value keeps points that are farther away, expanding the visible region.
            Decreasing restricts visibility to a smaller region around the viewpoint. Points beyond
            this radius are removed. Typical range: 0.1-100 meters depending on scene scale.
            For close-range scanning, use 0.1-1.0. For room-scale, use 1.0-10.0. For large scenes,
            use 10.0-100.0.

    Returns:
        A new Points3D object containing the filtered point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(viewpoint, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"viewpoint must be a Vector3D, np.ndarray, or list, class received: {type(viewpoint).__name__}"
        )
    if isinstance(viewpoint, np.ndarray):
        if viewpoint.size != 3:
            raise ValueError(f"viewpoint numpy array must have exactly 3 elements, got shape {viewpoint.shape} with {viewpoint.size} elements")
    elif isinstance(viewpoint, list):
        if len(viewpoint) != 3:
            raise ValueError(f"viewpoint list must have exactly 3 elements, got {len(viewpoint)}")
        if not all(isinstance(x, (float, int)) for x in viewpoint):
            raise ValueError("viewpoint list must contain only float or int elements")
    if not isinstance(visibility_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"visibility_radius must be a Float, float, or int, class received: {type(visibility_radius).__name__}"
        )
    
    if isinstance(viewpoint, np.ndarray):
        viewpoint = datatypes.Vector3D(xyz=viewpoint)
    elif isinstance(viewpoint, list):
        viewpoint = datatypes.Vector3D(xyz=np.array(viewpoint, dtype=np.float32))
    if isinstance(visibility_radius, (float, int)):
        visibility_radius = datatypes.Float(visibility_radius)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "viewpoint": viewpoint,
        "visibility_radius": visibility_radius
    }

    # Call the API
    end_point = "filter_point_cloud_using_viewpoint_visibility"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud


def filter_point_cloud_using_voxel_downsampling(
    point_cloud: datatypes.Points3D,
    voxel_size: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Downsamples a point cloud using voxel grid averaging.

    Divides 3D space into voxels and replaces all points within each voxel
    with their centroid.

    Args:
        point_cloud: The point cloud to downsample.
        voxel_size: The edge length of each cubic voxel in meters. Increasing this value creates larger
            voxels, resulting in more aggressive downsampling and fewer output points. Decreasing creates
            smaller voxels, preserving more detail but with more points. All points within a voxel are
            replaced by their centroid. Should be set to 2-5x the typical point spacing for balanced
            downsampling. Typical range: 0.001-0.1 meters for small objects, 0.01-0.5 for medium scenes,
            0.1-1.0 for large scenes. Use smaller values (0.001-0.01) to preserve fine details, larger
            values (0.05-0.1) for aggressive reduction.

    Returns:
        A new Points3D object containing the downsampled point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(voxel_size, (datatypes.Float, float, int)):
        raise TypeError(
            f"voxel_size must be a Float, float, or int, class received: {type(voxel_size).__name__}"
        )
    
    if isinstance(voxel_size, (float, int)):
        voxel_size = datatypes.Float(voxel_size)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "voxel_size": voxel_size
    }

    # Call the API
    end_point = "filter_point_cloud_using_voxel_downsampling"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    filtered_point_cloud = response_data["filtered_point_cloud"]
    return filtered_point_cloud

# Operations

def add_point_clouds(
    point_cloud1: datatypes.Points3D, point_cloud2: datatypes.Points3D
) -> datatypes.Points3D:
    """
    Combines all points from two point clouds into one unified point cloud.

    Args:
        point_cloud1: The first point cloud to add.
        point_cloud2: The second point cloud to add.

    Returns:
        A new Points3D object containing the combined points from both input point clouds.
    """
    if not isinstance(point_cloud1, datatypes.Points3D):
        raise TypeError(
            f"point_cloud1 must be a Points3D object, class received: {type(point_cloud1).__name__}"
        )
    if not isinstance(point_cloud2, datatypes.Points3D):
        raise TypeError(
            f"point_cloud2 must be a Points3D object, class received: {type(point_cloud2).__name__}"
        )
    
    # Prepare input data
    input_data = {
        "point_cloud1": point_cloud1,
        "point_cloud2": point_cloud2
    }

    # Call the API
    end_point = "add_point_clouds"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)
    result_point_cloud = response_data["result_point_cloud"]
    return result_point_cloud


def subtract_point_clouds(
    point_cloud1: datatypes.Points3D,
    point_cloud2: datatypes.Points3D,
    distance_threshold: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Removes points from one cloud that are near points in another cloud.

    Subtracts point_cloud2 from point_cloud1 by removing any point in cloud1
    that is within distance_threshold of any point in cloud2. Useful for removing
    overlapping regions or subtracting one object from another.

    Args:
        point_cloud1: The point cloud to subtract from (the source cloud). Points from this
            cloud will be removed if they are near points in point_cloud2.
        point_cloud2: The point cloud to subtract (the reference cloud). Points in point_cloud1
            that are near any point in this cloud will be removed.
        distance_threshold: The maximum distance in meters to consider points as "near" each other.
            Any point in point_cloud1 within this distance of any point in point_cloud2 will be
            removed. Increasing removes more points (more aggressive subtraction). Decreasing
            removes fewer points (more precise, only very close points). Should be set based on
            point cloud density and desired precision. Typical range: 0.001-0.1 meters. Use
            0.001-0.01 for precise subtraction, 0.01-0.05 for moderate, 0.05-0.1 for aggressive.

    Returns:
        A new Points3D object containing the subtracted point cloud (point_cloud1 with points
        near point_cloud2 removed).
    """
    if not isinstance(point_cloud1, datatypes.Points3D):
        raise TypeError(
            f"point_cloud1 must be a Points3D object, class received: {type(point_cloud1).__name__}"
        )
    if not isinstance(point_cloud2, datatypes.Points3D):
        raise TypeError(
            f"point_cloud2 must be a Points3D object, class received: {type(point_cloud2).__name__}"
        )
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    
    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    
    # Prepare input point clouds
    input_data = {
        "point_cloud1": point_cloud1,
        "point_cloud2": point_cloud2,
        "distance_threshold": distance_threshold,
    }

    # Call the API
    end_point = "subtract_point_clouds"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)
    result_point_cloud = response_data["result_point_cloud"]

    return result_point_cloud


def scale_point_cloud(
    point_cloud: datatypes.Points3D,
    scale_factor: datatypes.Float | float | int,
    center_point: datatypes.Vector3D | np.ndarray | list[float],
    modify_inplace: datatypes.Bool | bool = False,
) -> datatypes.Points3D:
    """
    Scales a point cloud uniformly about a center point.

    Multiplies all point coordinates by a scale factor relative to a center.

    Args:
        point_cloud: The point cloud to scale.
        scale_factor: The uniform scale factor to apply. Values > 1.0 enlarge the point cloud,
            values < 1.0 shrink it, and 1.0 leaves it unchanged. Increasing makes the cloud larger,
            decreasing makes it smaller. Typical range: 0.01-100.0. Use 0.1-0.5 to shrink,
            0.5-2.0 for moderate scaling, 2.0-10.0 to enlarge significantly.
        center_point: The 3D point (in meters) about which scaling is performed. All points are
            scaled relative to this center. Typically set to the centroid or a known reference point.
            Points at this location remain unchanged.
        modify_inplace: Whether to modify the input point cloud in place (True) or create a new
            one (False). When True, the original point cloud is modified. When False, a new point
            cloud is returned. Set to True to save memory, False to preserve the original.
            Default: False.

    Returns:
        A new Points3D object containing the scaled point cloud (or the modified original if
        modify_inplace is True).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(scale_factor, (datatypes.Float, float, int)):
        raise TypeError(
            f"scale_factor must be a Float, float, or int, class received: {type(scale_factor).__name__}"
        )
    if not isinstance(center_point, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"center_point must be a Vector3D, np.ndarray, or list, class received: {type(center_point).__name__}"
        )
    if isinstance(center_point, np.ndarray):
        if center_point.size != 3:
            raise ValueError(f"center_point numpy array must have exactly 3 elements, got shape {center_point.shape} with {center_point.size} elements")
    elif isinstance(center_point, list):
        if len(center_point) != 3:
            raise ValueError(f"center_point list must have exactly 3 elements, got {len(center_point)}")
        if not all(isinstance(x, (float, int)) for x in center_point):
            raise ValueError("center_point list must contain only float or int elements")
    if not isinstance(modify_inplace, (datatypes.Bool, bool)):
        raise TypeError(
            f"modify_inplace must be a Bool or bool, class received: {type(modify_inplace).__name__}"
        )
    
    if isinstance(scale_factor, (float, int)):
        scale_factor = datatypes.Float(scale_factor)
    if isinstance(center_point, np.ndarray):
        center_point = datatypes.Vector3D(xyz=center_point)
    elif isinstance(center_point, list):
        center_point = datatypes.Vector3D(xyz=np.array(center_point, dtype=np.float32))
    if isinstance(modify_inplace, bool):
        modify_inplace = datatypes.Bool(modify_inplace)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "scale_factor": scale_factor,
        "center_point": center_point,
        "modify_inplace": modify_inplace,
    }

    # Call the API
    end_point = "scale_point_cloud"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)
    result_point_cloud = response_data["result_point_cloud"]

    return result_point_cloud


def apply_transform_to_point_cloud(
    point_cloud: datatypes.Points3D, 
    transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]], 
    modify_inplace: Optional[datatypes.Bool | bool] = False
) -> datatypes.Points3D:
    """
    Apply a rigid body transform to a point cloud.

    Args:
        point_cloud: The point cloud to apply the transform to.
        transformation_matrix: The transformation matrix to apply to the point cloud.

    Returns:
        A new Points3D object containing the transformed point cloud.
    """
    # RigidBodyTransformer()
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(transformation_matrix).__name__}"
        )
    if isinstance(transformation_matrix, np.ndarray):
        if transformation_matrix.shape != (4, 4):
            raise ValueError(f"transformation_matrix numpy array must have exactly 4x4 elements, got shape {transformation_matrix.shape}")
    elif isinstance(transformation_matrix, list):
        if len(transformation_matrix) != 4 or not all(len(x) == 4 for x in transformation_matrix):
            raise ValueError(f"transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in transformation_matrix for x in row):
            raise ValueError("transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(modify_inplace, (datatypes.Bool, bool)):
        raise TypeError(
            f"modify_inplace must be a Bool or bool, class received: {type(modify_inplace).__name__}"
        )
    
    if isinstance(transformation_matrix, np.ndarray):
        transformation_matrix = datatypes.Mat4X4(matrix=transformation_matrix)
    elif isinstance(transformation_matrix, list):
        transformation_matrix = datatypes.Mat4X4(matrix=np.array(transformation_matrix, dtype=np.float32))
    if isinstance(modify_inplace, bool):
        modify_inplace = datatypes.Bool(modify_inplace)

    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "transformation_matrix": transformation_matrix,
        "modify_inplace": modify_inplace
    }

    # Call the API
    end_point = "apply_transform_to_point_cloud"
    response_data = _send_request(endpoint=end_point,
                                      input_data=input_data)
    
    result_point_cloud = response_data["result_point_cloud"]

    return result_point_cloud

#Projection

def project_point_cloud_to_plane(
    point_cloud: datatypes.Points3D,
    plane_coefficients: datatypes.Vector4D | np.ndarray | list[float],
    add_white_noise: datatypes.Bool | bool = datatypes.Bool(False),
    white_noise_standard_deviation: datatypes.Float | float | int = 0.0,
) -> datatypes.Points3D:
    """
    Projects a point cloud onto a plane.

    Projects all points in the cloud onto a plane defined by its coefficients.

    Args:
        point_cloud: The point cloud to project.
        plane_coefficients: The plane equation coefficients as [a, b, c, d] where ax + by + cz + d = 0.
            The vector [a, b, c] is the plane normal (should be normalized), and d is the distance from
            origin. Can be obtained from plane fitting algorithms.
        add_white_noise: Whether to add random noise to the projected points. When True, adds Gaussian
            noise to simulate measurement uncertainty or add variation. When False, projects points
            exactly onto the plane. Set to True for simulation/testing, False for exact projection.
            Default: False.
        white_noise_standard_deviation: The standard deviation of the Gaussian noise in meters, when
            add_white_noise is True. Increasing this value adds more variation to the projected points.
            Decreasing adds less noise. Typical range: 0.0-0.01 meters. Use 0.0 for no noise,
            0.001-0.005 for small variations, 0.005-0.01 for larger variations. Ignored if
            add_white_noise is False. Default: 0.0.

    Returns:
        A new Points3D object containing the projected point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(plane_coefficients, (datatypes.Vector4D, np.ndarray, list)):
        raise TypeError(
            f"plane_coefficients must be a Vector4D, np.ndarray, or list, class received: {type(plane_coefficients).__name__}"
        )
    if isinstance(plane_coefficients, np.ndarray):
        if plane_coefficients.size != 4:
            raise ValueError(f"plane_coefficients numpy array must have exactly 4 elements, got shape {plane_coefficients.shape} with {plane_coefficients.size} elements")
    elif isinstance(plane_coefficients, list):
        if len(plane_coefficients) != 4:
            raise ValueError(f"plane_coefficients list must have exactly 4 elements, got {len(plane_coefficients)}")
        if not all(isinstance(x, (float, int)) for x in plane_coefficients):
            raise ValueError("plane_coefficients list must contain only float or int elements")
    if not isinstance(add_white_noise, (datatypes.Bool, bool)):
        raise TypeError(
            f"add_white_noise must be a Bool or bool, class received: {type(add_white_noise).__name__}"
        )
    if not isinstance(white_noise_standard_deviation, (datatypes.Float, float, int)):
        raise TypeError(
            f"white_noise_standard_deviation must be a Float, float, or int, class received: {type(white_noise_standard_deviation).__name__}"
        )
    
    if isinstance(plane_coefficients, np.ndarray):
        plane_coefficients = datatypes.Vector4D(xyzw=plane_coefficients)
    elif isinstance(plane_coefficients, list):
        plane_coefficients = datatypes.Vector4D(xyzw=np.array(plane_coefficients, dtype=np.float32))
    if isinstance(add_white_noise, bool):
        add_white_noise = datatypes.Bool(add_white_noise)
    if isinstance(white_noise_standard_deviation, (float, int)):
        white_noise_standard_deviation = datatypes.Float(white_noise_standard_deviation)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "plane_coefficients": plane_coefficients,
        "add_white_noise": add_white_noise,
        "white_noise_standard_deviation": white_noise_standard_deviation
    }

    # Call the API
    end_point = "project_point_cloud_to_plane"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    projected_point_cloud = response_data["projected_point_cloud"]
    return projected_point_cloud


def project_point_cloud_to_plane_defined_by_point_normal(
    point_cloud: datatypes.Points3D,
    point: datatypes.Vector3D | np.ndarray | list[float],
    plane_normal: datatypes.Vector3D | np.ndarray | list[float],
    add_white_noise: datatypes.Bool | bool = False,
    white_noise_standard_deviation: datatypes.Float | float | int = 0.0,
) -> datatypes.Points3D:
    """
    Projects a point cloud onto a plane defined by a point and normal vector.

    Projects all points in the cloud onto a plane specified by a point on the
    plane and its normal vector.

    Args:
        point_cloud: The point cloud to project.
        point: A 3D point that lies on the plane, in meters. Defines the plane's position in space.
            Any point on the plane can be used.
        plane_normal: The normal vector of the plane (perpendicular to the plane surface). Should be
            normalized (unit vector). Defines the plane's orientation.
        add_white_noise: Whether to add random noise to the projected points. When True, adds Gaussian
            noise to simulate measurement uncertainty. When False, projects points exactly onto the plane.
            Set to True for simulation/testing, False for exact projection. Default: False.
        white_noise_standard_deviation: The standard deviation of the Gaussian noise in meters, when
            add_white_noise is True. Increasing this value adds more variation to the projected points.
            Decreasing adds less noise. Typical range: 0.0-0.01 meters. Use 0.0 for no noise,
            0.001-0.005 for small variations, 0.005-0.01 for larger variations. Ignored if
            add_white_noise is False. Default: 0.0.

    Returns:
        A new Points3D object containing the projected point cloud.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(point, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"point must be a Vector3D, np.ndarray, or list, class received: {type(point).__name__}"
        )
    if isinstance(point, np.ndarray):
        if point.size != 3:
            raise ValueError(f"point numpy array must have exactly 3 elements, got shape {point.shape} with {point.size} elements")
    elif isinstance(point, list):
        if len(point) != 3:
            raise ValueError(f"point list must have exactly 3 elements, got {len(point)}")
        if not all(isinstance(x, (float, int)) for x in point):
            raise ValueError("point list must contain only float or int elements")
    if not isinstance(plane_normal, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"plane_normal must be a Vector3D, np.ndarray, or list, class received: {type(plane_normal).__name__}"
        )
    if isinstance(plane_normal, np.ndarray):
        if plane_normal.size != 3:
            raise ValueError(f"plane_normal numpy array must have exactly 3 elements, got shape {plane_normal.shape} with {plane_normal.size} elements")
    elif isinstance(plane_normal, list):
        if len(plane_normal) != 3:
            raise ValueError(f"plane_normal list must have exactly 3 elements, got {len(plane_normal)}")
        if not all(isinstance(x, (float, int)) for x in plane_normal):
            raise ValueError("plane_normal list must contain only float or int elements")
    if not isinstance(add_white_noise, (datatypes.Bool, bool)):
        raise TypeError(
            f"add_white_noise must be a Bool or bool, class received: {type(add_white_noise).__name__}"
        )
    if not isinstance(white_noise_standard_deviation, (datatypes.Float, float, int)):
        raise TypeError(
            f"white_noise_standard_deviation must be a Float, float, or int, class received: {type(white_noise_standard_deviation).__name__}"
        )
    
    if isinstance(point, np.ndarray):
        point = datatypes.Vector3D(xyz=point)
    elif isinstance(point, list):
        point = datatypes.Vector3D(xyz=np.array(point, dtype=np.float32))
    if isinstance(plane_normal, np.ndarray):
        plane_normal = datatypes.Vector3D(xyz=plane_normal)
    elif isinstance(plane_normal, list):
        plane_normal = datatypes.Vector3D(xyz=np.array(plane_normal, dtype=np.float32))
    if isinstance(add_white_noise, bool):
        add_white_noise = datatypes.Bool(add_white_noise)
    if isinstance(white_noise_standard_deviation, (float, int)):
        white_noise_standard_deviation = datatypes.Float(white_noise_standard_deviation)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "point": point,
        "plane_normal": plane_normal,
        "add_white_noise": add_white_noise,
        "white_noise_standard_deviation": white_noise_standard_deviation
    }

    # Call the API
    end_point = "project_point_cloud_to_plane_defined_by_point_normal"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    projected_point_cloud = response_data["projected_point_cloud"]
    return projected_point_cloud

# Reconstruction

def reconstruct_mesh_using_convex_hull(
    point_cloud: datatypes.Points3D,
    joggle_inputs: datatypes.Bool | bool = False,
) -> datatypes.Mesh3D:
    """
    Reconstructs a mesh using convex hull algorithm.

    Creates a mesh that wraps all points in the point cloud using the convex hull.

    Args:
        point_cloud: The point cloud to reconstruct from. The convex hull will wrap all points,
            creating a convex shape that may not match concave features of the original shape.
        joggle_inputs: Whether to add small random perturbations to input points to avoid degenerate
            cases (e.g., coplanar points, duplicate points). When True, helps handle edge cases but
            slightly modifies the input. When False, may fail on degenerate inputs. Set to True for
            robust operation, False for exact computation. Default: False.

    Returns:
        A new Mesh3D object containing the reconstructed mesh.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(joggle_inputs, (datatypes.Bool, bool)):
        raise TypeError(
            f"joggle_inputs must be a Bool or bool, class received: {type(joggle_inputs).__name__}"
        )
    
    if isinstance(joggle_inputs, bool):
        joggle_inputs = datatypes.Bool(joggle_inputs)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "joggle_inputs": joggle_inputs
    }

    # Call the API
    end_point = "reconstruct_mesh_using_convex_hull"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    reconstructed_mesh = response_data["reconstructed_mesh"]
    return reconstructed_mesh


def reconstruct_mesh_using_poisson(
    point_cloud: datatypes.Points3D,
    octree_depth: datatypes.Int | int = 8,
    octree_width: datatypes.Int | int = 0,
    scale_factor: datatypes.Float | float | int = 1.05,
) -> datatypes.Mesh3D:
    """
    Reconstructs a watertight mesh from an oriented point cloud using Poisson surface reconstruction.

    Solves a Poisson equation to fit a smooth surface through points with normals.
    Produces closed, manifold meshes. Requires point cloud normals.

    Args:
        point_cloud: The point cloud to reconstruct from. Must have normals for best results.
        octree_depth: The depth of the octree used for spatial subdivision. Increasing creates finer
            detail but uses more memory and computation time. Decreasing creates coarser meshes but
            is faster. Each level doubles the resolution. Typical range: 6-12. Use 6-8 for coarse
            meshes, 8-10 for balanced quality/speed, 10-12 for high detail. Default: 8.
        octree_width: The width of the octree in voxels (0 = auto). When 0, automatically computed
            from point cloud bounds. When set manually, defines the spatial extent. Increasing expands
            the reconstruction volume. Typical range: 0 (auto) or 100-10000. Use 0 for automatic,
            or set manually if you need a specific volume size. Default: 0.
        scale_factor: The scale factor for the reconstruction. Increasing expands the surface
            slightly beyond the points, helping close small holes. Decreasing contracts the surface
            closer to points. Typical range: 1.0-1.2. Use 1.0-1.05 for tight fit, 1.05-1.1 for
            balanced, 1.1-1.2 for more expansion. Default: 1.05.

    Returns:
        A new Mesh3D object containing the reconstructed mesh.
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(octree_depth, (datatypes.Int, int)):
        raise TypeError(
            f"octree_depth must be an Int or int, class received: {type(octree_depth).__name__}"
        )
    if not isinstance(octree_width, (datatypes.Int, int)):
        raise TypeError(
            f"octree_width must be an Int or int, class received: {type(octree_width).__name__}"
        )
    if not isinstance(scale_factor, (datatypes.Float, float, int)):
        raise TypeError(
            f"scale_factor must be a Float, float, or int, class received: {type(scale_factor).__name__}"
        )
    
    if isinstance(octree_depth, int):
        octree_depth = datatypes.Int(octree_depth)
    if isinstance(octree_width, int):
        octree_width = datatypes.Int(octree_width)
    if isinstance(scale_factor, (float, int)):
        scale_factor = datatypes.Float(scale_factor)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "octree_depth": octree_depth,
        "octree_width": octree_width,
        "scale_factor": scale_factor
    }

    # Call the API
    end_point = "reconstruct_mesh_using_poisson"
    response_data = _send_request(endpoint=end_point,
                                  input_data=input_data)
    reconstructed_mesh = response_data["reconstructed_mesh"]
    return reconstructed_mesh

# Registration

def register_point_clouds_using_centroid_translation(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
) -> datatypes.Points3D:
    """
    Aligns point clouds by matching their centroids (coarse alignment).

    Computes a translation that moves the source cloud's center to the target cloud's
    center. Fast initial alignment step before fine registration.

    Args:
        source_point_cloud: The source point cloud to align.
        target_point_cloud: The target point cloud to align to.
        initial_transformation_matrix: The initial transformation matrix.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix
    }

    # Call the API
    end_point = "register_point_clouds_using_centroid_translation"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)

    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


def register_point_clouds_using_cuboid_translation_sampler_icp(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    step_size: datatypes.Float | float | int = 0.001,
    x_min: datatypes.Float | float | int = -0.01,
    x_max: datatypes.Float | float | int = 0.01,
    y_min: datatypes.Float | float | int = -0.01,
    y_max: datatypes.Float | float | int = 0.01,
    z_min: datatypes.Float | float | int = -0.01,
    z_max: datatypes.Float | float | int = 0.01,
    early_stop_fitness_score: datatypes.Float | float | int = 0.5,
    min_fitness_score: datatypes.Float | float | int = 0.9,
    max_iterations: datatypes.Int | int = 50,
    max_correspondence_distance: datatypes.Float | float | int = 0.02,
    estimate_scaling: datatypes.Bool | bool = False,
) -> datatypes.Points3D:
    """
    Finds best alignment by sampling translations in a 3D grid (cuboid) with ICP.

    Tries translations on a regular 3D grid within specified x/y/z ranges, runs ICP
    for each, and keeps best result.

    Args:
        source_point_cloud: The source point cloud to align.
        target_point_cloud: The target point cloud to align to.
        initial_transformation_matrix: The initial 4x4 transformation matrix. The translation
            search is performed relative to this initial alignment.
        step_size: The step size between sampled translations in meters. Increasing creates
            a coarser search grid (fewer samples, faster) but may miss the optimal alignment.
            Decreasing creates a finer grid (more samples, slower) for more thorough search.
            Should be set to 0.5-2x the expected alignment accuracy. Typical range: 0.0005-0.01 meters.
            Use 0.0005-0.001 for precise search, 0.001-0.005 for balanced, 0.005-0.01 for coarse.
            Default: 0.001.
        x_min: Minimum x translation in meters. Defines the lower bound of the search cuboid
            along the x-axis. Should be negative if translation can go in negative x direction.
            Typical range: -0.1 to 0.1 meters. Default: -0.01.
        x_max: Maximum x translation in meters. Defines the upper bound of the search cuboid
            along the x-axis. Should be positive and greater than x_min. Typical range: -0.1 to 0.1 meters.
            Default: 0.01.
        y_min: Minimum y translation in meters. Defines the lower bound along the y-axis.
            Typical range: -0.1 to 0.1 meters. Default: -0.01.
        y_max: Maximum y translation in meters. Defines the upper bound along the y-axis.
            Typical range: -0.1 to 0.1 meters. Default: 0.01.
        z_min: Minimum z translation in meters. Defines the lower bound along the z-axis.
            Typical range: -0.1 to 0.1 meters. Default: -0.01.
        z_max: Maximum z translation in meters. Defines the upper bound along the z-axis.
            Typical range: -0.1 to 0.1 meters. Default: 0.01.
        early_stop_fitness_score: Fitness score threshold (0-1) for early stopping during search.
            If a translation achieves this score or higher, search stops early. Increasing stops
            earlier (faster) but may accept suboptimal alignments. Decreasing requires better
            alignments before stopping. Typical range: 0.3-0.7. Use 0.3-0.5 for fast search,
            0.5-0.7 for quality. Default: 0.5.
        min_fitness_score: Minimum fitness score (0-1) required to accept the final result.
            Results below this are rejected. Increasing requires better alignment quality.
            Decreasing accepts lower quality alignments. Typical range: 0.7-0.99. Use 0.7-0.85
            for lenient, 0.85-0.95 for balanced, 0.95-0.99 for strict. Default: 0.9.
        max_iterations: The maximum number of ICP iterations per translation sample. Increasing
            allows more refinement but is slower. Typical range: 10-200. Use 10-30 for fast,
            30-50 for balanced, 50-200 for high precision. Default: 50.
        max_correspondence_distance: The maximum distance to consider points as correspondences
            in meters. Increasing allows matching more distant points but may include incorrect
            matches. Decreasing requires closer matches. Should be 2-5x point spacing. Typical
            range: 0.01-0.1 meters. Default: 0.02.
        estimate_scaling: Whether to estimate and apply uniform scaling between point clouds.
            When True, allows the algorithm to find scale differences. When False, assumes same scale.
            Set to True if point clouds may have different scales, False for same-scale alignment.
            Default: False.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(step_size, (datatypes.Float, float, int)):
        raise TypeError(
            f"step_size must be a Float, float, or int, class received: {type(step_size).__name__}"
        )
    if not isinstance(x_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"x_min must be a Float, float, or int, class received: {type(x_min).__name__}"
        )
    if not isinstance(x_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"x_max must be a Float, float, or int, class received: {type(x_max).__name__}"
        )
    if not isinstance(y_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"y_min must be a Float, float, or int, class received: {type(y_min).__name__}"
        )
    if not isinstance(y_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"y_max must be a Float, float, or int, class received: {type(y_max).__name__}"
        )
    if not isinstance(z_min, (datatypes.Float, float, int)):
        raise TypeError(
            f"z_min must be a Float, float, or int, class received: {type(z_min).__name__}"
        )
    if not isinstance(z_max, (datatypes.Float, float, int)):
        raise TypeError(
            f"z_max must be a Float, float, or int, class received: {type(z_max).__name__}"
        )
    if not isinstance(early_stop_fitness_score, (datatypes.Float, float, int)):
        raise TypeError(
            f"early_stop_fitness_score must be a Float, float, or int, class received: {type(early_stop_fitness_score).__name__}"
        )
    if not isinstance(min_fitness_score, (datatypes.Float, float, int)):
        raise TypeError(
            f"min_fitness_score must be a Float, float, or int, class received: {type(min_fitness_score).__name__}"
        )
    if not isinstance(max_iterations, (datatypes.Int, int)):
        raise TypeError(
            f"max_iterations must be an Int or int, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(max_correspondence_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_correspondence_distance must be a Float, float, or int, class received: {type(max_correspondence_distance).__name__}"
        )
    if not isinstance(estimate_scaling, (datatypes.Bool, bool)):
        raise TypeError(
            f"estimate_scaling must be a Bool or bool, class received: {type(estimate_scaling).__name__}"
        )
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    if isinstance(step_size, (float, int)):
        step_size = datatypes.Float(step_size)
    if isinstance(x_min, (float, int)):
        x_min = datatypes.Float(x_min)
    if isinstance(x_max, (float, int)):
        x_max = datatypes.Float(x_max)
    if isinstance(y_min, (float, int)):
        y_min = datatypes.Float(y_min)
    if isinstance(y_max, (float, int)):
        y_max = datatypes.Float(y_max)
    if isinstance(z_min, (float, int)):
        z_min = datatypes.Float(z_min)
    if isinstance(z_max, (float, int)):
        z_max = datatypes.Float(z_max)
    if isinstance(early_stop_fitness_score, (float, int)):
        early_stop_fitness_score = datatypes.Float(early_stop_fitness_score)
    if isinstance(min_fitness_score, (float, int)):
        min_fitness_score = datatypes.Float(min_fitness_score)
    if isinstance(max_iterations, int):
        max_iterations = datatypes.Int(max_iterations)
    if isinstance(max_correspondence_distance, (float, int)):
        max_correspondence_distance = datatypes.Float(max_correspondence_distance)
    if isinstance(estimate_scaling, bool):
        estimate_scaling = datatypes.Bool(estimate_scaling)
    
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix,
        "step_size": step_size,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max,
        "early_stop_fitness_score": early_stop_fitness_score,
        "min_fitness_score": min_fitness_score,
        "max_iterations": max_iterations,
        "max_correspondence_distance": max_correspondence_distance,
        "estimate_scaling": estimate_scaling,
    }

    # Call the API
    end_point = "register_point_clouds_using_cuboid_translation_sampler_icp"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


def register_point_clouds_using_fast_global_registration(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    normal_radius: datatypes.Float | float | int = 0.02,
    normal_max_neighbors: datatypes.Int | int = 20,
    feature_radius: datatypes.Float | float | int = 0.05,
    feature_max_neighbors: datatypes.Int | int = 30,
    max_correspondence_distance: datatypes.Float | float | int = 0.015,
) -> datatypes.Points3D:
    """
    Aligns point clouds using Fast Global Registration (FGR).

    Feature-based registration that's faster than RANSAC. Uses graduated
    non-convexity optimization.

    Args:
        source_point_cloud: The source point cloud to align. Should have normals or they will be estimated.
        target_point_cloud: The target point cloud to align to. Should have normals or they will be estimated.
        initial_transformation_matrix: The initial 4x4 transformation matrix. FGR can handle larger
            initial misalignments than ICP, but a rough initial alignment helps.
        normal_radius: The search radius for normal estimation in meters. Increasing considers more
            neighbors for smoother normals but is slower. Decreasing uses fewer neighbors, faster but
            more sensitive to noise. Should be 2-5x point spacing. Typical range: 0.01-0.1 meters.
            Use 0.01-0.02 for dense clouds, 0.02-0.05 for medium, 0.05-0.1 for sparse. Default: 0.02.
        normal_max_neighbors: Maximum number of neighbors to use for normal estimation. Increasing
            provides more stable normals but is slower. Decreasing is faster but may be noisy.
            Typical range: 10-50. Use 10-20 for fast, 20-30 for balanced, 30-50 for quality.
            Default: 20.
        feature_radius: The radius for computing FPFH features in meters. Increasing captures larger
            scale features but is slower. Decreasing captures finer features. Should be 5-10x point
            spacing. Typical range: 0.02-0.2 meters. Use 0.02-0.05 for fine features, 0.05-0.1 for
            balanced, 0.1-0.2 for coarse. Default: 0.05.
        feature_max_neighbors: Maximum neighbors for FPFH feature computation. Increasing captures more
            context but is slower. Typical range: 20-100. Use 20-30 for fast, 30-50 for balanced,
            50-100 for detailed. Default: 30.
        max_correspondence_distance: The maximum distance for feature matching in meters. Increasing
            allows matching more distant features but may include incorrect matches. Decreasing requires
            closer matches. Should be 2-5x feature_radius. Typical range: 0.01-0.1 meters.
            Default: 0.015.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(normal_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"normal_radius must be a Float, float, or int, class received: {type(normal_radius).__name__}"
        )
    if not isinstance(normal_max_neighbors, (datatypes.Int, int)):
        raise TypeError(
            f"normal_max_neighbors must be an Int or int, class received: {type(normal_max_neighbors).__name__}"
        )
    if not isinstance(feature_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"feature_radius must be a Float, float, or int, class received: {type(feature_radius).__name__}"
        )
    if not isinstance(feature_max_neighbors, (datatypes.Int, int)):
        raise TypeError(
            f"feature_max_neighbors must be an Int or int, class received: {type(feature_max_neighbors).__name__}"
        )
    if not isinstance(max_correspondence_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_correspondence_distance must be a Float, float, or int, class received: {type(max_correspondence_distance).__name__}"
        )
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    if isinstance(normal_radius, (float, int)):
        normal_radius = datatypes.Float(normal_radius)
    if isinstance(normal_max_neighbors, int):
        normal_max_neighbors = datatypes.Int(normal_max_neighbors)
    if isinstance(feature_radius, (float, int)):
        feature_radius = datatypes.Float(feature_radius)
    if isinstance(feature_max_neighbors, int):
        feature_max_neighbors = datatypes.Int(feature_max_neighbors)
    if isinstance(max_correspondence_distance, (float, int)):
        max_correspondence_distance = datatypes.Float(max_correspondence_distance)
    
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix,
        "normal_radius": normal_radius,
        "normal_max_neighbors": normal_max_neighbors,
        "feature_radius": feature_radius,
        "feature_max_neighbors": feature_max_neighbors,
        "max_correspondence_distance": max_correspondence_distance,
    }

    # Call the API
    end_point = "register_point_clouds_using_fast_global_registration"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


def register_point_clouds_using_point_to_plane_icp(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    max_iterations: datatypes.Int | int = 50,
    max_correspondence_distance: datatypes.Float | float | int = 0.05,
    normal_max_neighbors: datatypes.Int | int = 30,
    normal_search_radius: datatypes.Float | float | int = 0.05,
    use_robust_kernel: datatypes.Bool | bool = False,
    loss_type: datatypes.String | str = "L2",
    noise_standard_deviation: datatypes.Float | float | int = 0.0,
) -> datatypes.Points3D:
    """
    Aligns point clouds using point-to-plane ICP.

    Uses point-to-plane distance metric for more accurate registration when
    normals are available.

    Args:
        source_point_cloud: The source point cloud to align. Should have normals for best results.
        target_point_cloud: The target point cloud to align to. Should have normals for best results.
        initial_transformation_matrix: The initial 4x4 transformation matrix. Should bring source
            close to target (within max_correspondence_distance).
        max_iterations: The maximum number of ICP iterations. Increasing allows more refinement.
            Typical range: 10-200. Use 10-30 for fast, 30-50 for balanced, 50-200 for precision.
            Default: 50.
        max_correspondence_distance: The maximum distance to consider points as correspondences
            in meters. Increasing allows matching more distant points. Should be 2-5x point spacing.
            Typical range: 0.01-0.1 meters. Default: 0.05.
        normal_max_neighbors: Maximum number of neighbors for normal estimation. Increasing provides
            smoother normals but is slower. Typical range: 10-50. Default: 30.
        normal_search_radius: Search radius for normal estimation in meters. Increasing considers
            more neighbors. Should be 2-5x point spacing. Typical range: 0.01-0.1 meters. Default: 0.05.
        use_robust_kernel: Whether to use robust kernel (e.g., Huber) to reduce outlier influence.
            When True, outliers have less impact on alignment. When False, uses standard L2 loss.
            Set to True when point clouds contain outliers or noise. Default: False.
        loss_type: The loss function type. Options: "L2" (standard), "L1" (robust), "Huber" (balanced).
            "L2" is standard, "L1" is more robust to outliers, "Huber" balances both. Default: "L2".
        noise_standard_deviation: Expected standard deviation of point noise in meters. Used for
            uncertainty weighting. Increasing gives less weight to noisy points. Typical range: 0.0-0.01.
            Use 0.0 to ignore, 0.001-0.005 for typical noise. Default: 0.0.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(max_iterations, (datatypes.Int, int)):
        raise TypeError(
            f"max_iterations must be an Int or int, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(max_correspondence_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_correspondence_distance must be a Float, float, or int, class received: {type(max_correspondence_distance).__name__}"
        )
    if not isinstance(normal_max_neighbors, (datatypes.Int, int)):
        raise TypeError(
            f"normal_max_neighbors must be an Int or int, class received: {type(normal_max_neighbors).__name__}"
        )
    if not isinstance(normal_search_radius, (datatypes.Float, float, int)):
        raise TypeError(
            f"normal_search_radius must be a Float, float, or int, class received: {type(normal_search_radius).__name__}"
        )
    if not isinstance(use_robust_kernel, (datatypes.Bool, bool)):
        raise TypeError(
            f"use_robust_kernel must be a Bool or bool, class received: {type(use_robust_kernel).__name__}"
        )
    if not isinstance(loss_type, (datatypes.String, str)):
        raise TypeError(
            f"loss_type must be a String or str, class received: {type(loss_type).__name__}"
        )
    if not isinstance(noise_standard_deviation, (datatypes.Float, float, int)):
        raise TypeError(
            f"noise_standard_deviation must be a Float, float, or int, class received: {type(noise_standard_deviation).__name__}"
        )
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    if isinstance(max_iterations, int):
        max_iterations = datatypes.Int(max_iterations)
    if isinstance(max_correspondence_distance, (float, int)):
        max_correspondence_distance = datatypes.Float(max_correspondence_distance)
    if isinstance(normal_max_neighbors, int):
        normal_max_neighbors = datatypes.Int(normal_max_neighbors)
    if isinstance(normal_search_radius, (float, int)):
        normal_search_radius = datatypes.Float(normal_search_radius)
    if isinstance(use_robust_kernel, bool):
        use_robust_kernel = datatypes.Bool(use_robust_kernel)
    if isinstance(loss_type, str):
        loss_type = datatypes.String(loss_type)
    if isinstance(noise_standard_deviation, (float, int)):
        noise_standard_deviation = datatypes.Float(noise_standard_deviation)
    
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix,
        "max_iterations": max_iterations,
        "max_correspondence_distance": max_correspondence_distance,
        "normal_max_neighbors": normal_max_neighbors,
        "normal_search_radius": normal_search_radius,
        "use_robust_kernel": use_robust_kernel,
        "loss_type": loss_type,
        "noise_standard_deviation": noise_standard_deviation,
    }

    # Call the API
    end_point = "register_point_clouds_using_point_to_plane_icp"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


def register_point_clouds_using_point_to_point_icp(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    max_iterations: datatypes.Int | int = 50,
    max_correspondence_distance: datatypes.Float | float | int = 0.05,
    estimate_scaling: datatypes.Bool | bool = False,
    min_fitness_score: datatypes.Float | float | int = 0.9,
) -> datatypes.Points3D:
    """
    Aligns point clouds using point-to-point ICP.

    Iteratively finds correspondences and computes transformation to minimize
    point-to-point distances.

    Args:
        source_point_cloud: The source point cloud to align.
        target_point_cloud: The target point cloud to align to.
        initial_transformation_matrix: The initial 4x4 transformation matrix. Should bring source
            close to target (within max_correspondence_distance). Use identity if roughly aligned.
        max_iterations: The maximum number of ICP iterations. Increasing allows more refinement but
            takes longer. Typical range: 10-200. Use 10-30 for fast, 30-50 for balanced,
            50-200 for high precision. Default: 50.
        max_correspondence_distance: The maximum distance to consider points as correspondences
            in meters. Increasing allows matching more distant points but may include incorrect
            matches. Decreasing requires closer matches. Should be 2-5x the typical point spacing.
            Typical range: 0.01-0.1 meters. Use 0.01-0.02 for dense clouds, 0.02-0.05 for medium,
            0.05-0.1 for sparse. Default: 0.05.
        estimate_scaling: Whether to estimate and apply uniform scaling between point clouds.
            When True, allows the algorithm to find scale differences. When False, assumes same scale.
            Set to True if point clouds may have different scales, False for same-scale alignment.
            Default: False.
        min_fitness_score: Minimum fitness score (0-1) required to accept the final result.
            Results below this are rejected. Typical range: 0.7-0.99. Default: 0.9.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(max_iterations, (datatypes.Int, int)):
        raise TypeError(
            f"max_iterations must be an Int or int, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(max_correspondence_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_correspondence_distance must be a Float, float, or int, class received: {type(max_correspondence_distance).__name__}"
        )
    if not isinstance(estimate_scaling, (datatypes.Bool, bool)):
        raise TypeError(
            f"estimate_scaling must be a Bool or bool, class received: {type(estimate_scaling).__name__}"
        )
    if not isinstance(min_fitness_score, (datatypes.Float, float, int)):
        raise TypeError(
            f"min_fitness_score must be a Float, float, or int, class received: {type(min_fitness_score).__name__}"
        )
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    if isinstance(max_iterations, int):
        max_iterations = datatypes.Int(max_iterations)
    if isinstance(max_correspondence_distance, (float, int)):
        max_correspondence_distance = datatypes.Float(max_correspondence_distance)
    if isinstance(estimate_scaling, bool):
        estimate_scaling = datatypes.Bool(estimate_scaling)
    if isinstance(min_fitness_score, (float, int)):
        min_fitness_score = datatypes.Float(min_fitness_score)
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix,
        "max_iterations": max_iterations,
        "max_correspondence_distance": max_correspondence_distance,
        "estimate_scaling": estimate_scaling,
        "min_fitness_score": min_fitness_score,
    }

    # Call the API
    end_point = "register_point_clouds_using_point_to_point_icp"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


def register_point_clouds_using_rotation_sampler_icp(
    source_point_cloud: datatypes.Points3D,
    target_point_cloud: datatypes.Points3D,
    initial_transformation_matrix: datatypes.Mat4X4 | np.ndarray | list[list[float]] = np.eye(4),
    x_step_size_deg: datatypes.Int | int = 20,
    y_step_size_deg: datatypes.Int | int = 20,
    z_step_size_deg: datatypes.Int | int = 20,
    x_min_deg: datatypes.Int | int = 0,
    x_max_deg: datatypes.Int | int = 180,
    y_min_deg: datatypes.Int | int = 0,
    y_max_deg: datatypes.Int | int = 180,
    z_min_deg: datatypes.Int | int = 0,
    z_max_deg: datatypes.Int | int = 180,
    early_stop_fitness_score: datatypes.Float | float | int = 0.5,
    min_fitness_score: datatypes.Float | float | int = 0.9,
    max_iterations: datatypes.Int | int = 50,
    max_correspondence_distance: datatypes.Float | float | int = 0.02,
    estimate_scaling: datatypes.Bool | bool = False,
) -> datatypes.Points3D:
    """
    Finds best alignment by trying multiple rotations with ICP refinement.

    Samples rotations in Euler angle space, runs ICP for each, and keeps the best.

    Args:
        source_point_cloud: The source point cloud to align.
        target_point_cloud: The target point cloud to align to.
        initial_transformation_matrix: The initial 4x4 transformation matrix. The rotation search
            is performed relative to this initial alignment.
        x_step_size_deg: Step size for x-axis rotation sampling in degrees. Increasing creates
            a coarser search (fewer samples, faster) but may miss optimal rotation. Decreasing
            creates finer search (more samples, slower). Typical range: 5-45 degrees. Use 5-10
            for fine search, 10-20 for balanced, 20-45 for coarse. Default: 20.0.
        y_step_size_deg: Step size for y-axis rotation sampling in degrees. Same as x_step_size_deg.
            Default: 20.0.
        z_step_size_deg: Step size for z-axis rotation sampling in degrees. Same as x_step_size_deg.
            Default: 20.0.
        x_min_deg: Minimum x-axis rotation angle in degrees. Defines the lower bound of rotation
            search around x-axis. Typical range: 0-360. Use 0-180 for half-sphere, 0-360 for full.
            Default: 0.0.
        x_max_deg: Maximum x-axis rotation angle in degrees. Should be greater than x_min_deg.
            Typical range: 0-360. Default: 180.0.
        y_min_deg: Minimum y-axis rotation angle in degrees. Default: 0 .
        y_max_deg: Maximum y-axis rotation angle in degrees. Default: 180.
        z_min_deg: Minimum z-axis rotation angle in degrees. Default: 0.
        z_max_deg: Maximum z-axis rotation angle in degrees. Default: 180.
        early_stop_fitness_score: Fitness score threshold (0-1) for early stopping during search.
            If a rotation achieves this score or higher, search stops early. Increasing stops
            earlier (faster) but may accept suboptimal alignments. Typical range: 0.3-0.7.
            Default: 0.5.
        min_fitness_score: Minimum fitness score (0-1) required to accept the final result.
            Results below this are rejected. Typical range: 0.7-0.99. Default: 0.9.
        max_iterations: The maximum number of ICP iterations per rotation sample. Typical range:
            10-200. Default: 50.
        max_correspondence_distance: The maximum distance to consider points as correspondences
            in meters. Should be 2-5x point spacing. Typical range: 0.01-0.1 meters. Default: 0.02.
        estimate_scaling: Whether to estimate and apply uniform scaling between point clouds.
            When True, allows the algorithm to find scale differences. Default: False.

    Returns:
        A new Points3D object containing the registered point cloud.
    """
    if not isinstance(source_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"source_point_cloud must be a Points3D object, class received: {type(source_point_cloud).__name__}"
        )
    if not isinstance(target_point_cloud, datatypes.Points3D):
        raise TypeError(
            f"target_point_cloud must be a Points3D object, class received: {type(target_point_cloud).__name__}"
        )
    if not isinstance(initial_transformation_matrix, (datatypes.Mat4X4, np.ndarray, list)):
        raise TypeError(
            f"initial_transformation_matrix must be a Mat4X4, np.ndarray, or list, class received: {type(initial_transformation_matrix).__name__}"
        )
    if isinstance(initial_transformation_matrix, np.ndarray):
        if initial_transformation_matrix.shape != (4, 4):
            raise ValueError(f"initial_transformation_matrix numpy array must have exactly 4x4 elements, got shape {initial_transformation_matrix.shape}")
    elif isinstance(initial_transformation_matrix, list):
        if len(initial_transformation_matrix) != 4 or not all(len(x) == 4 for x in initial_transformation_matrix):
            raise ValueError(f"initial_transformation_matrix list must be a 4x4 matrix (4 rows, each with 4 elements), got {len(initial_transformation_matrix)} rows")
        if not all(isinstance(x, (float, int)) for row in initial_transformation_matrix for x in row):
            raise ValueError("initial_transformation_matrix list must contain only float or int elements in all rows")
    if not isinstance(x_step_size_deg, (datatypes.Int, int)):
        raise TypeError(
            f"x_step_size_deg must be an Int or int, class received: {type(x_step_size_deg).__name__}"
        )
    if not isinstance(y_step_size_deg, (datatypes.Int, int)):
        raise TypeError(
            f"y_step_size_deg must be an Int or int, class received: {type(y_step_size_deg).__name__}"
        )
    if not isinstance(z_step_size_deg, (datatypes.Int, int)):
        raise TypeError(
            f"z_step_size_deg must be an Int or int, class received: {type(z_step_size_deg).__name__}"
        )
    if not isinstance(x_min_deg, (datatypes.Int, int)):
        raise TypeError(
            f"x_min_deg must be an Int or int, class received: {type(x_min_deg).__name__}"
        )
    if not isinstance(x_max_deg, (datatypes.Int, int)):
        raise TypeError(
            f"x_max_deg must be an Int or int, class received: {type(x_max_deg).__name__}"
        )
    if not isinstance(y_min_deg, (datatypes.Int, int)):
        raise TypeError(
            f"y_min_deg must be an Int or int, class received: {type(y_min_deg).__name__}"
        )
    if not isinstance(y_max_deg, (datatypes.Int, int)):
        raise TypeError(
            f"y_max_deg must be an Int or int, class received: {type(y_max_deg).__name__}"
        )
    if not isinstance(z_min_deg, (datatypes.Int, int)):
        raise TypeError(
            f"z_min_deg must be an Int or int, class received: {type(z_min_deg).__name__}"
        )
    if not isinstance(z_max_deg, (datatypes.Int, int)):
        raise TypeError(
            f"z_max_deg must be an Int or int, class received: {type(z_max_deg).__name__}"
        )
    if not isinstance(early_stop_fitness_score, (datatypes.Float, float, int)):
        raise TypeError(
            f"early_stop_fitness_score must be a Float, float, or int, class received: {type(early_stop_fitness_score).__name__}"
        )
    if not isinstance(min_fitness_score, (datatypes.Float, float, int)):
        raise TypeError(
            f"min_fitness_score must be a Float, float, or int, class received: {type(min_fitness_score).__name__}"
        )
    if not isinstance(max_iterations, (datatypes.Int, int)):
        raise TypeError(
            f"max_iterations must be an Int or int, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(max_correspondence_distance, (datatypes.Float, float, int)):
        raise TypeError(
            f"max_correspondence_distance must be a Float, float, or int, class received: {type(max_correspondence_distance).__name__}"
        )
    if not isinstance(estimate_scaling, (datatypes.Bool, bool)):
        raise TypeError(
            f"estimate_scaling must be a Bool or bool, class received: {type(estimate_scaling).__name__}"
        )
    
    if isinstance(initial_transformation_matrix, np.ndarray):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=initial_transformation_matrix)
    elif isinstance(initial_transformation_matrix, list):
        initial_transformation_matrix = datatypes.Mat4X4(matrix=np.array(initial_transformation_matrix, dtype=np.float32))
    if isinstance(x_step_size_deg, int):
        x_step_size_deg = datatypes.Int(x_step_size_deg)
    if isinstance(y_step_size_deg, int):
        y_step_size_deg = datatypes.Int(y_step_size_deg)
    if isinstance(z_step_size_deg, int):
        z_step_size_deg = datatypes.Int(z_step_size_deg)
    if isinstance(x_min_deg, int):
        x_min_deg = datatypes.Int(x_min_deg)
    if isinstance(x_max_deg, int):
        x_max_deg = datatypes.Int(x_max_deg)
    if isinstance(y_min_deg, int):
        y_min_deg = datatypes.Int(y_min_deg)
    if isinstance(y_max_deg, int):
        y_max_deg = datatypes.Int(y_max_deg)
    if isinstance(z_min_deg, int):
        z_min_deg = datatypes.Int(z_min_deg)
    if isinstance(z_max_deg, int):
        z_max_deg = datatypes.Int(z_max_deg)
    if isinstance(early_stop_fitness_score, (float, int)):
        early_stop_fitness_score = datatypes.Float(early_stop_fitness_score)
    if isinstance(min_fitness_score, (float, int)):
        min_fitness_score = datatypes.Float(min_fitness_score)
    if isinstance(max_iterations, int):
        max_iterations = datatypes.Int(max_iterations)
    if isinstance(max_correspondence_distance, (float, int)):
        max_correspondence_distance = datatypes.Float(max_correspondence_distance)
    if isinstance(estimate_scaling, bool):
        estimate_scaling = datatypes.Bool(estimate_scaling)
    
    # Prepare input data
    input_data = {
        "source_point_cloud": source_point_cloud,
        "target_point_cloud": target_point_cloud,
        "initial_transformation_matrix": initial_transformation_matrix,
        "x_step_size_deg": x_step_size_deg,
        "y_step_size_deg": y_step_size_deg,
        "z_step_size_deg": z_step_size_deg,
        "x_min_deg": x_min_deg,
        "x_max_deg": x_max_deg,
        "y_min_deg": y_min_deg,
        "y_max_deg": y_max_deg,
        "z_min_deg": z_min_deg,
        "z_max_deg": z_max_deg,
        "early_stop_fitness_score": early_stop_fitness_score,
        "min_fitness_score": min_fitness_score,
        "max_iterations": max_iterations,
        "max_correspondence_distance": max_correspondence_distance,
        "estimate_scaling": estimate_scaling,
    }

    # Call the API
    end_point = "register_point_clouds_using_rotation_sampler_icp"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)  
    
    transformation_matrix = response_data["transformation_matrix"]
    return transformation_matrix


# Segmentation

def segment_point_cloud_using_color(
    point_cloud: datatypes.Points3D,
    target_color: datatypes.Rgba32 | np.ndarray | list[int],
    color_distance_threshold: datatypes.Float | float | int,
) -> datatypes.Points3D:
    """
    Segments a point cloud based on color similarity.

    Keeps points whose color is within a distance threshold of a target color.

    Args:
        point_cloud: The point cloud to segment. Must have colors for this function to work.
        target_color: The target color to match as a numpy array [R, G, B] with values in range
            [0.0, 1.0] for normalized colors or [0, 255] for 8-bit colors. The color space should
            match the point cloud's color space. Example: [1.0, 0.0, 0.0] for red in normalized,
            or [255, 0, 0] for red in 8-bit.
        color_distance_threshold: The maximum color distance (in color space) to consider a point
            as matching the target color. Increasing keeps points with more color variation,
            including points that are less similar to the target. Decreasing keeps only points
            very close to the target color. Typical range: 0.01-0.5 for normalized colors [0-1],
            or 5-100 for 8-bit colors [0-255]. Use 0.01-0.1 for strict matching, 0.1-0.3 for
            moderate, 0.3-0.5 for lenient.

    Returns:
        A new Points3D object containing the segmented point cloud (points matching the target color).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(target_color, (datatypes.Rgba32, np.ndarray, list)):
        raise TypeError(
            f"target_color must be a Rgba32, np.ndarray, or list, class received: {type(target_color).__name__}"
        )
    if isinstance(target_color, np.ndarray):
        if target_color.size in (3, 4):
            raise ValueError(f"target_color numpy array must have exactly 4 elements, got shape {target_color.shape} with {target_color.size} elements")
    elif isinstance(target_color, list):
        if len(target_color) not in (3, 4):
            raise ValueError(f"target_color list must have exactly 4 elements, got {len(target_color)}")
        if not all(isinstance(x, (int, float)) for x in target_color):
            raise ValueError("target_color list must contain only int or float elements")
    if not isinstance(color_distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"color_distance_threshold must be a Float, float, or int, class received: {type(color_distance_threshold).__name__}"
        )
    
    if isinstance(target_color, np.ndarray):
        target_color = datatypes.Rgba32(rgba=target_color)
    elif isinstance(target_color, list):
        target_color = datatypes.Rgba32(rgba=np.array(target_color, dtype=np.uint8))
    if isinstance(color_distance_threshold, (float, int)):
        color_distance_threshold = datatypes.Float(color_distance_threshold)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "target_color": target_color,
        "color_distance_threshold": color_distance_threshold,
    }

    # Call the API
    end_point = "segment_point_cloud_using_color"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    segmented_point_cloud = response_data["segmented_point_cloud"]
    return segmented_point_cloud


def segment_point_cloud_using_plane(
    point_cloud: datatypes.Points3D,
    distance_threshold: datatypes.Float | float | int,
    num_initial_points: datatypes.Int | int = 3,
    max_iterations: datatypes.Int | int = 100,
    keep_outliers: datatypes.Bool | bool = False,
) -> datatypes.Points3D:
    """
    Segments a point cloud by fitting a plane using RANSAC.

    Finds the largest plane in the point cloud and segments points belonging to it.

    Args:
        point_cloud: The point cloud to segment. Should contain at least one dominant plane.
        distance_threshold: The maximum perpendicular distance from the plane to include a point,
            in meters. Increasing includes points farther from the plane, capturing a thicker
            plane region. Decreasing keeps only points very close to the plane. Should be set based
            on point cloud density and noise level. Typical range: 0.001-0.1 meters. Use 0.001-0.01
            for precise plane extraction, 0.01-0.05 for moderate, 0.05-0.1 for thick planes.
        num_initial_points: The number of points used to initialize each RANSAC plane hypothesis.
            For a plane, 3 points are needed (minimum). Increasing uses more points per hypothesis,
            which may be more stable but is slower. Typical range: 3-10. Use 3 for standard RANSAC,
            4-6 for more stable fits, 7-10 for very robust (slower). Default: 3.
        max_iterations: The maximum number of RANSAC iterations. Increasing tries more random
            samples, improving the chance of finding the best plane but taking longer. Decreasing
            is faster but may miss the optimal plane. Typical range: 100-10000. Use 100-500 for
            fast, 500-2000 for balanced, 2000-10000 for high robustness. Default: 100.
        keep_outliers: Whether to return points that are NOT on the plane (outliers) instead of
            points ON the plane (inliers). When True, returns points that don't belong to the plane.
            When False, returns points that belong to the plane. Set to True to remove the plane,
            False to extract the plane. Default: False.

    Returns:
        A new Points3D object containing the segmented point cloud (plane points or outliers
        depending on keep_outliers).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    if not isinstance(num_initial_points, (datatypes.Int, int)):
        raise TypeError(
            f"num_initial_points must be an Int or int, class received: {type(num_initial_points).__name__}"
        )
    if not isinstance(max_iterations, (datatypes.Int, int)):
        raise TypeError(
            f"max_iterations must be an Int or int, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(keep_outliers, (datatypes.Bool, bool)):
        raise TypeError(
            f"keep_outliers must be a Bool or bool, class received: {type(keep_outliers).__name__}"
        )
    
    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    if isinstance(num_initial_points, int):
        num_initial_points = datatypes.Int(num_initial_points)
    if isinstance(max_iterations, int):
        max_iterations = datatypes.Int(max_iterations)
    if isinstance(keep_outliers, bool):
        keep_outliers = datatypes.Bool(keep_outliers)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "distance_threshold": distance_threshold,
        "num_initial_points": num_initial_points,
        "max_iterations": max_iterations,
        "keep_outliers": keep_outliers,
    }

    # Call the API
    end_point = "segment_point_cloud_using_plane"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    segmented_point_cloud = response_data["segmented_point_cloud"]
    plane_model = response_data["plane_model"]

    return segmented_point_cloud, plane_model


def segment_point_cloud_using_vector_proximity(
    point_cloud: datatypes.Points3D,
    reference_point: datatypes.Vector3D | np.ndarray | list[float],
    reference_vector: datatypes.Vector3D | np.ndarray | list[float],
    distance_threshold: datatypes.Float | float | int,
    keep_outliers: datatypes.Bool | bool = False,
) -> datatypes.Points3D:
    """
    Segments a point cloud based on proximity to a vector.

    Keeps points that are within a distance threshold of a reference vector
    starting from a reference point. Useful for extracting points along a line or direction.

    Args:
        point_cloud: The point cloud to segment.
        reference_point: The 3D starting point of the reference vector, in meters. Defines where
            the vector begins in space.
        reference_vector: The direction vector (should be normalized) defining the line/direction
            to segment along. Points are tested for proximity to the infinite line defined by
            reference_point + t * reference_vector. Typical values: [1,0,0] for x-axis,
            [0,1,0] for y-axis, [0,0,1] for z-axis, or any normalized direction vector.
        distance_threshold: The maximum perpendicular distance from the vector line to include
            a point, in meters. Increasing includes points farther from the line, creating a
            thicker "tube" around the vector. Decreasing keeps only points very close to the line.
            Should be set based on point cloud density. Typical range: 0.001-0.1 meters. Use
            0.001-0.01 for precise line extraction, 0.01-0.05 for moderate, 0.05-0.1 for thick.
        keep_outliers: Whether to return points that are NOT near the vector (outliers) instead
            of points near the vector (inliers). When True, returns points far from the vector.
            When False, returns points near the vector. Set to True to remove points along the
            vector, False to extract points along the vector. Default: False.

    Returns:
        A new Points3D object containing the segmented point cloud (points near the vector or
        outliers depending on keep_outliers).
    """
    if not isinstance(point_cloud, datatypes.Points3D):
        raise TypeError(
            f"point_cloud must be a Points3D object, class received: {type(point_cloud).__name__}"
        )
    if not isinstance(reference_point, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"reference_point must be a Vector3D, np.ndarray, or list, class received: {type(reference_point).__name__}"
        )
    if isinstance(reference_point, np.ndarray):
        if reference_point.size != 3:
            raise ValueError(f"reference_point numpy array must have exactly 3 elements, got shape {reference_point.shape} with {reference_point.size} elements")
    elif isinstance(reference_point, list):
        if len(reference_point) != 3:
            raise ValueError(f"reference_point list must have exactly 3 elements, got {len(reference_point)}")
        if not all(isinstance(x, (float, int)) for x in reference_point):
            raise ValueError("reference_point list must contain only float or int elements")
    if not isinstance(reference_vector, (datatypes.Vector3D, np.ndarray, list)):
        raise TypeError(
            f"reference_vector must be a Vector3D, np.ndarray, or list, class received: {type(reference_vector).__name__}"
        )
    if isinstance(reference_vector, np.ndarray):
        if reference_vector.size != 3:
            raise ValueError(f"reference_vector numpy array must have exactly 3 elements, got shape {reference_vector.shape} with {reference_vector.size} elements")
    elif isinstance(reference_vector, list):
        if len(reference_vector) != 3:
            raise ValueError(f"reference_vector list must have exactly 3 elements, got {len(reference_vector)}")
        if not all(isinstance(x, (float, int)) for x in reference_vector):
            raise ValueError("reference_vector list must contain only float or int elements")
    if not isinstance(distance_threshold, (datatypes.Float, float, int)):
        raise TypeError(
            f"distance_threshold must be a Float, float, or int, class received: {type(distance_threshold).__name__}"
        )
    if not isinstance(keep_outliers, (datatypes.Bool, bool)):
        raise TypeError(
            f"keep_outliers must be a Bool or bool, class received: {type(keep_outliers).__name__}"
        )
    
    if isinstance(reference_point, np.ndarray):
        reference_point = datatypes.Vector3D(xyz=reference_point)
    elif isinstance(reference_point, list):
        reference_point = datatypes.Vector3D(xyz=np.array(reference_point, dtype=np.float32))
    if isinstance(reference_vector, np.ndarray):
        reference_vector = datatypes.Vector3D(xyz=reference_vector)
    elif isinstance(reference_vector, list):
        reference_vector = datatypes.Vector3D(xyz=np.array(reference_vector, dtype=np.float32))
    if isinstance(distance_threshold, (float, int)):
        distance_threshold = datatypes.Float(distance_threshold)
    if isinstance(keep_outliers, bool):
        keep_outliers = datatypes.Bool(keep_outliers)
    
    # Prepare input data
    input_data = {
        "point_cloud": point_cloud,
        "reference_point": reference_point,
        "reference_vector": reference_vector,
        "distance_threshold": distance_threshold,
        "keep_outliers": keep_outliers,
    }

    # Call the API
    end_point = "segment_point_cloud_using_vector_proximity"
    response_data = _send_request(endpoint=end_point,
                                        input_data=input_data)
    
    segmented_point_cloud = response_data["segmented_point_cloud"]
    return segmented_point_cloud


