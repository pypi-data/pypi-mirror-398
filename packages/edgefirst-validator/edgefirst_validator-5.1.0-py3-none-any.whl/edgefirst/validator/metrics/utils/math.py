"""
Various mathematical utility functions for metric calculations.
"""

from typing import Union

import numpy as np


def mean_absolute_error(
    y_true: Union[list, np.ndarray],
    y_pred: Union[list, np.ndarray]
) -> float:
    """
    Calculates the mean absolute error defined in this source::
    https://datagy.io/mae-python/

    Parameters
    ----------
    y_true: Union[list, np.ndarray]
        The true values.
    y_pred: Union[list, np.ndarray]
        The predicted values.

    Returns
    -------
    float
        The mean absolute error of the values comparing y_pred to y_true.
    """
    return np.abs(np.subtract(y_true, y_pred)).mean()


def mean_squared_error(
    y_true: Union[list, np.ndarray],
    y_pred: Union[list, np.ndarray]
) -> float:
    """
    Calculates the mean squared error defined in this source:
    https://www.geeksforgeeks.org/python-mean-squared-error/

    Parameters
    ----------
    y_true: Union[list, np.ndarray]
        The true values.
    y_pred: Union[list, np.ndarray]
        The predicted values.

    Returns
    -------
    float
        The mean squared error of the values
        comparing y_pred to y_true.
    """
    return np.square(np.subtract(y_true, y_pred)).mean()


def batch_iou(box1: np.ndarray, box2: np.ndarray, eps: float = 1e-7):
    """
    The intersection-over-union (Jaccard index) of boxes.
    The YOLOv5 implementation taken from::
    https://github.com/ultralytics/yolov5/blob/master/utils/metrics.py#L266

    Both sets of boxes are expected to be in (xmin, ymin, xmax, ymax) format.

    Parameters
    ----------
    box1 : np.ndarray
        The first set of bounding boxes with the shape (n, 4)
        in the format [xmin, ymin, xmax, ymax].
    box2 : np.ndarray
        The second bounding boxes with the shape (n, 4)
        in the format [xmin, ymin, xmax, ymax].
    eps : float
        This is used to prevent division by 0.

    Returns
    -------
    np.ndarray
        An IoU 2D matrix which calculates
        the IoU between box1 (row) and
        box2 (column).
    """
    if len(box1) == 0 or len(box2) == 0:
        return np.zeros((len(box1), len(box2)), dtype=np.float32)

    # Expand dimensions for broadcasting
    a1 = box1[:, None, :2]  # (N,1,2)
    a2 = box1[:, None, 2:]  # (N,1,2)
    b1 = box2[None, :, :2]  # (1,M,2)
    b2 = box2[None, :, 2:]  # (1,M,2)

    # Intersection box
    inter_wh = np.minimum(a2, b2) - np.maximum(a1, b1)
    inter_wh = np.clip(inter_wh, a_min=0, a_max=None)
    inter_area = inter_wh[..., 0] * inter_wh[..., 1]

    # Areas of each box
    area1 = (a2[..., 0] - a1[..., 0]) * (a2[..., 1] - a1[..., 1])  # (N,1)
    area2 = (b2[..., 0] - b1[..., 0]) * (b2[..., 1] - b1[..., 1])  # (1,M)

    # IoU
    union = area1 + area2 - inter_area + eps
    iou = inter_area / union

    return iou.astype(np.float32)


def batch_distance_similarity(
    boxes1: np.ndarray,
    boxes2: np.ndarray,
    leniency_factor: int = 2
) -> np.ndarray:
    """
    IoU-like center-distance similarity in range [0,1].

    Parameters
    ----------
    boxes1: np.ndarray
        The first set of bounding boxes with the shape (n, 4)
        in the format [xmin, ymin, xmax, ymax].
    boxes2: np.ndarray
        The second bounding boxes with the shape (n, 4)
        in the format [xmin, ymin, xmax, ymax].
    leniency_factor: int
        A factor to control the leniency of the distance similarity.

    Returns
    -------
    np.ndarray
        A similarity matrix between boxes1 (row) and boxes2 (column).
    """
    # centers
    c1 = box_centers(boxes1)      # [N,2]
    c2 = box_centers(boxes2)      # [M,2]

    center_dist = minkowski_distance(c1, c2, p=2)  # [N,M]

    # diagonals (per box)
    d1 = box_diagonals(boxes1)  # [N]
    d2 = box_diagonals(boxes2)  # [M]

    # smaller per pair
    dmin = np.minimum(d1[:, None], d2[None, :])  # [N,M]

    # threshold distance
    max_dist = leniency_factor * dmin  # [N,M]

    # similarity
    sim = 1 - (center_dist / max_dist)
    sim = np.clip(sim, 0, 1)

    return sim.astype(np.float32)


def mask_iou(mask1: np.ndarray, mask2: np.ndarray,
             eps: float = 1e-7) -> np.ndarray:
    """
    The intersection-over-union (Jaccard index) of masks.
    The Ultralytics implementation taken from::
    https://github.com/ultralytics/ultralytics/blob/main/ultralytics/utils/metrics.py#L147

    Parameters
    ----------
    mask1 : np.ndarray
        Array of shape (N, n), N ground truth masks, flattened.
        This array must have floating point values for correct IoUs.
    mask2 : np.ndarray
        Array of shape (M, n), M predicted masks, flattened.
        This array must have floating point values for correct IoUs.
    eps : float, optional
        Small epsilon to prevent division by zero.

    Returns
    -------
    np.ndarray
        IoU matrix of shape (N, M) representing mask IoUs.
    """
    # Compute intersection
    intersection = np.clip(mask1 @ mask2.T, 0, None)  # shape: (N, M)

    # Compute union
    area1 = mask1.sum(axis=1, keepdims=True)  # shape: (N, 1)
    area2 = mask2.sum(axis=1, keepdims=True).T  # shape: (1, M)
    union = area1 + area2 - intersection

    # Compute IoU
    return intersection / (union + eps)


def iou_3d(
    corners1: Union[list, np.ndarray],
    corners2: Union[list, np.ndarray]
) -> float:
    """
    Computes the 3D IoU between ground truth and detection bounding boxes.
    Source:: https://github.com/varunagrawal/bbox/blob/master/bbox/metrics.py#L139

    Parameters
    ----------
    corners1: Union[list, np.ndarray]
        This is an (8, 3) array of 8 corners for a single 3D bounding box where
        rows represents one point and columns represents the [x,y,z] coordinates.
    corners2: Union[list, np.ndarray]
        This is an (8, 3) array of 8 corners for a single 3D bounding box where
        rows represents one point and columns represents the [x,y,z] coordinates.

    Returns
    -------
    float
        This is the 3D IoU between ground truth and prediction bounding boxes.
    """
    # Check if the two boxes don't overlap.
    if not polygon_collision(corners1[0:4, [0, 2]], corners2[0:4, [0, 2]]):
        return 0.0

    # Intersection of the x,z plane.
    intersection_points = polygon_intersection(
        corners1[0:4, [0, 2]], corners2[0:4, [0, 2]])
    # If intersection_points is empty, means the boxes don't intersect
    if len(intersection_points) == 0:
        return 0.0
    inter_area = polygon_area(intersection_points)

    ymax = np.minimum(corners1[4, 1], corners2[4, 1])
    ymin = np.maximum(corners1[0, 1], corners2[0, 1])
    inter_vol = inter_area * np.maximum(0, ymax - ymin)

    vol1 = box3d_vol(corners1)
    vol2 = box3d_vol(corners2)
    union_vol = vol1 + vol2 - inter_vol

    iou = inter_vol / union_vol
    # set nan and +/- inf to 0
    if np.isinf(iou) or np.isnan(iou):
        iou = 0
    return iou


def cosine_similarity(
    center1: Union[list, np.ndarray],
    center2: Union[list, np.ndarray],
    normalize: bool = False
) -> float:
    """
    The cosine similarity between two vectors is the dot product
    of the vectors over the product of the magnitudes of the vectors.
    https://en.wikipedia.org/wiki/Cosine_similarity

    Parameters
    ----------
    center1: list or np.ndarray
        The 2D [x,y] or 3D [x,y,z] coordinates
        for the first point.
    center2: list or np.ndarray
        The 2D [x,y] or 3D [x,y,z] coordinates
        for the second point.
    normalize: bool
        If this is set to true, this normalizes the metric to be within
        the range of 0 and 1. This is used such that the metric behaves
        similar to an IoU for object detection. Otherwise, by default
        it is -1 for perpendicular vectors and 1 for orthogonal.

    Returns
    -------
    float
        The distance between two points.
    """
    cosine = np.dot(center1, center2) / \
        (np.linalg.norm(center1) * np.linalg.norm(center2))
    # normalize ranges -1 to 1 into 0 to 1.
    if normalize:
        cosine = (cosine + 1) / 2
    return cosine


def minkowski_distance(a: np.ndarray, b: np.ndarray, p: int = 2) -> np.ndarray:
    """
    Computes Minkowski distances between two sets of points:

    Parameters
    ----------
    a: np.ndarray
        An array of points with shape [N, D].
    b: np.ndarray
        An array of points with shape [M, D].
    p: int
        The order of the Minkowski distance.

    Returns
    -------
    np.ndarray
        A matrix of Minkowski distances with shape [N, M].
    """
    diff = np.abs(a[:, None, :] - b[None, :, :])   # [N, M, D]
    return np.sum(diff ** p, axis=-1) ** (1 / p)   # [N, M]


def box_diagonals(boxes: np.ndarray) -> np.ndarray:
    """
    Computes the diagonal lengths of bounding boxes.

    Parameters
    ----------
    boxes: np.ndarray
        An array of bounding boxes with shape [N, 4]
        in the format [xmin, ymin, xmax, ymax].

    Returns
    -------
    np.ndarray
        An array of diagonal lengths for each bounding box.
    """
    p1 = boxes[:, :2]
    p2 = boxes[:, 2:]
    return np.sqrt(np.sum((p1 - p2)**2, axis=-1))  # faster version


def box_centers(boxes: np.ndarray) -> np.ndarray:
    """
    Computes the center points of bounding boxes.

    Parameters
    ----------
    boxes: np.ndarray
        An array of bounding boxes with shape [N, 4]
        in the format [xmin, ymin, xmax, ymax].

    Returns
    -------
    np.ndarray
        An array of center points for each bounding box.
    """
    return np.column_stack([
        (boxes[:, 0] + boxes[:, 2]) / 2,
        (boxes[:, 1] + boxes[:, 3]) / 2
    ])


def sigmoid(p: np.ndarray) -> np.ndarray:
    """
    The sigmoid function that maps values between 0 and 1.

    Parameters
    ----------
    p: np.ndarray
        An array of values to transform.

    Returns
    -------
    np.ndarray
        An array of values with sigmoid applied.
    """
    return 1 / (1 + np.exp(-p))


def softmax(x: np.ndarray) -> np.ndarray:
    """
    Transform values between 0 and 1.

    Parameters
    ----------
    x: np.ndarray
        An array of values to transform.

    Returns
    -------
    np.ndarray
        The array with softmax transformations.
    """
    # Subtract the maximum for numerical stability
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

# Useful functions to deal with 3D geometry.
# Source: https://github.com/varunagrawal/bbox/blob/master/bbox/geometry.py


def x_rotation(angle: float) -> np.ndarray:
    """
    Rotation around the x-axis.
    Source: https://en.wikipedia.org/wiki/Rotation_matrix

    Parameters
    ----------
    angle: float
        The angle of rotation in radians.

    Returns
    -------
    np.ndarrau
        Rotation matrix around the x-axis.
    """
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([[1, 0, 0],
                     [0, c, -s],
                     [0, s, c]])


def y_rotation(angle: float) -> np.ndarray:
    """
    Rotation around the y-axis.
    Source: https://en.wikipedia.org/wiki/Rotation_matrix

    Parameters
    ----------
    angle: float
        The angle of rotation in radians.

    Returns
    -------
    np.ndarray
        Rotation matrix around the y-axis.
    """
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([[c, 0, s],
                     [0, 1, 0],
                     [-s, 0, c]])


def z_rotation(angle: float) -> np.ndarray:
    """
    Rotation around the z-axis.
    Source: https://en.wikipedia.org/wiki/Rotation_matrix

    Parameters
    ----------
    angle: float
        The angle of rotation in radians.

    Returns
    -------
    np.ndarray
        Rotation matrix around the z-axis.
    """
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([[c, -s, 0],
                     [s, c, 0],
                     [0, 0, 1]])


def transform(
    box_size: Union[list, np.ndarray, tuple],
    heading_angle: float,
    center: Union[list, np.ndarray, tuple]
) -> np.ndarray:
    """
    Provides rotations and formation of the 3D box corners.

    Parameters
    ----------
    box_size: Union[list, np.ndarray, tuple]
        Can be unpacked to width, height, length respectively.
    heading_angle: float
        The angle in radians to rotate around the y-axis.
    center: Union[list, np.ndarray, tuple]
        In the order of the x-center, y-center, and z-center coordinates.

    Returns
    -------
    np.ndarray
        This is an (3, 8) array which represents the 3D bounding box corners
        where rows are the [x,y,z] coordinates and columns
        are the 8 corner points.
    """
    rotation = y_rotation(heading_angle)
    w, h, l = box_size
    x_corners = [-l / 2, l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2, -l / 2]
    y_corners = [-h / 2, -h / 2, -h / 2, -h / 2, h / 2, h / 2, h / 2, h / 2]
    z_corners = [-w / 2, -w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2, w / 2]

    corners_3d = np.dot(rotation, np.vstack([x_corners, y_corners, z_corners]))
    corners_3d[0, :] = corners_3d[0, :] + center[0]
    corners_3d[1, :] = corners_3d[1, :] + center[1]
    corners_3d[2, :] = corners_3d[2, :] + center[2]
    return corners_3d


def box3d_vol(corners: np.ndarray) -> float:
    """
    Computes the volume of the 3D bounding box based on the corners provided.

    Parameters
    ----------
    corners: np.ndarray
        This is an (8, 3) array of the bounding box corners
        with no assumption on axis direction.

    Returns
    -------
    float
        The volume of the bounding box.
    """
    a = np.sqrt(np.sum((corners[0, :] - corners[1, :])**2))
    b = np.sqrt(np.sum((corners[1, :] - corners[2, :])**2))
    c = np.sqrt(np.sum((corners[0, :] - corners[4, :])**2))
    return a * b * c


def get_corners(sizes: list, box_angles: list, centers: list) -> list:
    """
    Transforms a list of sizes, angles, and centers into 3D box corners.

    Parameters
    ----------
    sizes: list
        Contains lists that can be unpacked
        to width, height, length respectively.
    box_angles: list
        Contains the angles in radians to rotate around the y-axis.
    centers: list
        Contains lists in the order of the
        x-center, y-center, and z-center coordinates.

    Returns
    -------
    list
        A list of (8,3) corners.
    """
    # corner formats should be [[[x,y,z], [x,y,z], ... x6]]
    corners = list()
    if 0 not in [len(sizes), len(box_angles), len(centers)]:
        for size, angle, center in zip(sizes, box_angles, centers):
            corners.append(transform(size, angle, center))
    return corners


def get_plane(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """
    Get plane equation from 3 points.
    Returns the coefficients of `ax + by + cz + d = 0`

    Parameters
    ----------
    a: np.ndarray
        First point [x, y, z].
    b: np.ndarray
        Second point [x, y, z].
    c: np.ndarray
        Third point [x, y, z].

    Returns
    -------
    np.ndarray
        The plane coefficients [A, B, C, D].
    """
    ab = b - a
    ac = c - a

    x = np.cross(ab, ac)
    d = -np.dot(x, a)
    pl = np.hstack((x, d))
    return pl


def point_plane_dist(
        pt: np.ndarray, plane: np.ndarray, signed: bool = False) -> float:
    """
    Get the signed distance from a point `pt` to a plane `plane`.
    Reference: http://mathworld.wolfram.com/Point-PlaneDistance.html

    Plane is of the format [A, B, C, D], where the plane equation is Ax+By+Cz+D=0
    Point is of the form [x, y, z]
    `signed` flag indicates whether to return signed distance.

    Parameters
    ----------
    pt: np.ndarray
        The point [x, y, z].
    plane: np.ndarray
        The plane coefficients [A, B, C, D].
    signed: bool, optional
        Whether to return signed distance. Default is False.

    Returns
    -------
    float
        The distance from the point to the plane. If `signed` is True,
        the distance can be negative indicating the point is on the opposite
        side of the plane normal.
    """
    v = plane[0:3]
    dist = (np.dot(v, pt) + plane[3]) / np.linalg.norm(v)

    if signed:
        return dist
    else:
        return np.abs(dist)


def edges_of(vertices: np.ndarray) -> list:
    """
    Return the vectors for the edges of the polygon defined by `vertices`.

    Parameters
    ----------
    vertices: np.ndarray
        A 2D array representing the vertices of a polygon.

    Returns
    -------
    list
        A list of 2D arrays representing the edge vectors.
    """
    edges = []
    num_vertices = len(vertices)

    for i in range(num_vertices):
        edge = vertices[(i + 1) % num_vertices] - vertices[i]
        edges.append(edge)

    return edges


def orthogonal(v: np.ndarray) -> np.ndarray:
    """
    Return a 90 degree clockwise rotation of the vector `v`.

    Parameters
    ----------
    v: np.ndarray
        2D array representing a vector.

    Returns
    -------
    np.ndarray
        A 2D array representing the orthogonal vector.
    """
    return np.array([-v[1], v[0]])


def is_separating_axis(o: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> tuple:
    """
    Return True and the push vector if `o` is a separating axis
    of `p1` and `p2`. Otherwise, return False and None.

    Parameters
    ----------
    o: np.ndarray
        2D array representing a vector.
    p1: np.ndarray
        2D array of points representing a polygon.
    p2: np.ndarray
        2D array of points representing a polygon.

    Returns
    -------
    tuple
        A tuple where the first element is a boolean indicating
        if `o` is a separating axis, and the second element is the push vector
        if they are not separated, otherwise None.
    """
    min1, max1 = float('+inf'), float('-inf')
    min2, max2 = float('+inf'), float('-inf')

    for v in p1:
        projection = np.dot(v, o)

        min1 = min(min1, projection)
        max1 = max(max1, projection)

    for v in p2:
        projection = np.dot(v, o)

        min2 = min(min2, projection)
        max2 = max(max2, projection)

    if max1 >= min2 and max2 >= min1:
        d = min(max2 - min1, max1 - min2)
        # push a bit more than needed so the shapes do not overlap in future
        # tests due to float precision
        d_over_o_squared = d / np.dot(o, o) + 1e-10
        pv = d_over_o_squared * o
        return False, pv
    else:
        return True, None


def polygon_collision(p1: np.ndarray, p2: np.ndarray) -> bool:
    """
    Return True if the shapes collide. Otherwise, return False.

    p1 and p2 are np.arrays, the vertices of the polygons in the
    counterclockwise direction.

    Source: https://hackmd.io/s/ryFmIZrsl

    Parameters
    ----------
    p1: np.ndarray
        2D array of points representing a polygon.
    p2: np.ndarray
        2D array of points representing a polygon.

    Returns
    -------
    bool
        True if the shapes collide, False otherwise.
    """
    edges = edges_of(p1)
    edges += edges_of(p2)
    orthogonals = [orthogonal(e) for e in edges]

    push_vectors = []
    for o in orthogonals:
        separates, pv = is_separating_axis(o, p1, p2)

        if separates:
            # they do not collide and there is no push vector
            return False
        else:
            push_vectors.append(pv)
    return True


def polygon_area(polygon: np.ndarray) -> float:
    """
    Get the area of a polygon which is represented by a 2D array of points.
    Area is computed using the Shoelace Algorithm.

    Parameters
    ----------
        polygon: 2D array of points.

    Returns
    -------
    float
        The area of the polygon.
    """
    x = polygon[:, 0]
    y = polygon[:, 1]
    area = (np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))
    return np.abs(area) / 2


def line_intersection(
    e1: np.ndarray,
    e2: np.ndarray,
    s: np.ndarray,
    e: np.ndarray
) -> np.ndarray:
    """
    Compute the intersection point of two lines (e1,e2) and (s,e).

    Parameters
    ----------
    e1: np.ndarray
        The first point of the first line.
    e2: np.ndarray
        The second point of the first line.
    s: np.ndarray
        The first point of the second line.
    e: np.ndarray
        The second point of the second line.

    Returns
    -------
    np.ndarray
        The intersection point of the two lines.
    """
    dc = e1 - e2
    dp = s - e
    n1 = np.cross(e1, e2)
    n2 = np.cross(s, e)
    n3 = 1.0 / (np.cross(dc, dp))
    return np.array([(n1 * dp[0] - n2 * dc[0]) * n3,
                     (n1 * dp[1] - n2 * dc[1]) * n3])


def is_inside_edge(p: np.ndarray, e1: np.ndarray, e2: np.ndarray) -> bool:
    """
    Return True if e is inside edge (e1, e2)

    Parameters
    ----------
    p: np.ndarray
        The point to check.
    e1: np.ndarray
        The first point of the edge.
    e2: np.ndarray
        The second point of the edge.

    Returns
    -------
    bool
        True if point is inside edge, False otherwise.
    """
    return np.cross(e2 - e1, p - e1) >= 0


def polygon_intersection(poly1: np.ndarray, poly2: np.ndarray) -> np.ndarray:
    """
    Use the Sutherland-Hodgman algorithm to
    compute the intersection of 2 convex polygons.

    Parameters
    ----------
    poly1: np.ndarray
        A 2D array of points representing the first polygon.
    poly2: np.ndarray
        A 2D array of points representing the second polygon.

    Returns
    -------
    np.ndarray
        A 2D array of points representing the intersection polygon.
    """

    output_list = poly1
    # e1 and e2 are the edge vertices for each edge in the clipping polygon
    e1 = poly2[-1]

    for e2 in poly2:
        # If there is no point of intersection
        if len(output_list) == 0:
            break

        input_list = output_list
        output_list = []
        s = input_list[-1]

        for e in input_list:
            if is_inside_edge(e, e1, e2):
                # if s in not inside edge (e1, e2)
                if not is_inside_edge(s, e1, e2):
                    # line intersects edge hence we compute intersection point
                    output_list.append(line_intersection(e1, e2, s, e))
                output_list.append(e)
            # is s inside edge (e1, e2)
            elif is_inside_edge(s, e1, e2):
                output_list.append(line_intersection(e1, e2, s, e))

            s = e
        e1 = e2
    return np.array(output_list)
