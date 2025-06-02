import matplotlib.pyplot as plt
import numpy as np

def ray_seg_matching(p, d, a, b):
    """
    Check if the ray defined by point p and direction d intersects with the segment defined by the points a and b.

    :param p: Point from which the ray starts.
    :type p: numpy.ndarray(shape=(2,))
    :param d: Direction of the ray.
    :type d: numpy.ndarray(shape=(2,))
    :param a: Start point of the segment.
    :type a: numpy.ndarray(shape=(2,))
    :param b: End point of the segment.
    :type b: numpy.ndarray(shape=(2,))
    :return: True if the ray intersects with the segment, False otherwise.
    :rtype: bool
    .. note:: The function uses Cramer's rule to solve the system of equations that determines the intersection point.
    """
    v1 = b - a
    v2 = p - a

    # cramer's rule
    denom = np.linalg.det(np.array([v1, d]).T)
    if denom == 0:
        # The ray and the segment are parallel
        return False
    u = np.linalg.det(np.array([v2, d]).T) / denom
    t = np.linalg.det(np.array([v1, v2]).T) / denom

    if 0 <= u <= 1:
        return True
    return False

def ray_rect_matching(p, d, verts):
    """
    Check if the ray defined by point p and direction d intersects with the rectangle defined by its 4 vertices.

    :param p: Point from which the ray starts.
    :type p: numpy.ndarray(shape=(2,))
    :param d: Direction of the ray.
    :type d: numpy.ndarray(shape=(2,))
    :param verts: Vertices of the rectangle.
    :type verts: numpy.ndarray(shape=(4, 2))
    :return: True if the ray intersects with the rectangle, False otherwise.
    :rtype: bool

    .. note:: The function checks for intersection with each segment of the rectangle.
    """
    if any(ray_seg_matching(p, d, verts[i], verts[(i + 1) % len(verts)]) for i in range(len(verts))):
        return True
    return False

def main():
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    ax.grid(True, alpha=0.5, linestyle='--')
    ax.set_xlim(-1, 10)
    ax.set_ylim(-1, 10)

    #def the rectangle
    rect = plt.Rectangle((6,4), 2, 4, linewidth=1, color='blue', angle=34, alpha=0.3)
    vertices = np.array(rect.get_verts())
    segments = np.diff(vertices, axis=0)

    for i, (x, y) in enumerate(vertices[:-1], start=1):
        ax.scatter(x, y, color='red', s=10)
        ax.annotate(f"{i}", xy=(x, y), textcoords="offset points", xytext=(0, 10), ha='center')


    ax.quiver(vertices[:-1, 0], vertices[:-1, 1], segments[:, 0], segments[:, 1], color=['red', 'blue', 'green', 'purple'], scale_units='xy', scale=1)

    p1 = np.array([3.3, 0.8])
    p2 = np.array([0.9, 1.1])
    d1 = -1 * np.array([0.8, 2.3])
    d2 = np.array([1.5, 0.3])

    ax.arrow(*p1, *d1, head_width=0.2, head_length=0.2, color="k")
    ax.annotate("P1", xy=p1, textcoords="offset points", xytext=(0, 10), ha='center')
    ax.arrow(*p2, *d2, head_width=0.2, head_length=0.2, color="k")
    ax.annotate("P2", xy=p2, textcoords="offset points", xytext=(0, 10), ha='center')

    # Check if the ray intersects with the segment
    # for p1 and d1 
    print("P1")
    for i in range(len(vertices)-1):
        a = vertices[i]
        b = vertices[i + 1]
        print(f"Segment {i+1} -> {i+2}")
        if ray_seg_matching(p1, d1, a, b):
            print(f"INTERSECTS")
        else:
            print(f"NO INTERSECTS")
    # for p2 and d2
    print("---------\nP2")
    for i in range(len(vertices) - 1):
        a = vertices[i]
        b = vertices[i + 1]
        print(f"Segment {i+1} -> {i+2}")
        if ray_seg_matching(p2, d2, a, b):
            print(f"INTERSECTS")
        else:
            print(f"NO INTERSECTS")


    # Check if the ray intersects with the rectangle
    print("---------\nP1 and Rect defined by vertices 1-2-3-4")
    if ray_rect_matching(p1, d1, vertices[:-1]):
        print("INTERSECTS")
    else:
        print("NO INTERSECTS")
    print("---------\nP2 and Rect defined by vertices 1-2-3-4")
    if ray_rect_matching(p2, d2, vertices[:-1]):
        print("INTERSECTS")
    else:
        print("NO INTERSECTS")

    ax.add_patch(rect)
    plt.show()

if __name__ == "__main__":
    main()