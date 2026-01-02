"""
Absfuyu: Shape
--------------
Shapes

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Polygon
    "Triangle",
    "Circle",
    "Square",
    "Rectangle",
    "Pentagon",
    "Hexagon",
    "Parallelogram",
    "Rhombus",
    "Trapezoid",
    # 3D Shape
    "Cube",
    "Cuboid",
    "Sphere",
    "HemiSphere",
    "Cylinder",
]


# Library
# ---------------------------------------------------------------------------
import math
from abc import ABC, abstractmethod
from typing import ClassVar, Self, override

from absfuyu.core import BaseClass


# Class
# ---------------------------------------------------------------------------
class Shape(BaseClass):
    """Shape base class"""

    pass


class Polygon(ABC, Shape):
    """2D Shape class base"""

    POLYGON_LIST: ClassVar[list[str]] = []

    def __init__(self, num_of_sides: int) -> None:
        """
        Initialize a polygon with number of sides.

        Parameters
        ----------
        num_of_sides : int
            Number of sides of the polygon.

        Raises
        ------
        ValueError
            If the number of sides smaller than 3.
        """
        if num_of_sides <= 2:
            raise ValueError("Number of sides must be larger than 2.")

        self._num_of_sides = num_of_sides

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        # cls.POLYGON_LIST.append(cls)  # append type
        cls.POLYGON_LIST.append(cls.__name__)  # append name

    @abstractmethod
    def perimeter(self):
        pass

    @abstractmethod
    def area(self):
        pass


class EqualSidesPolygon(Polygon):
    """
    Base class for polygons with equal side length
    """

    def __init__(self, side: int | float, num_of_sides: int) -> None:
        """
        Initialize a polygon with equal side length.

        Parameters
        ----------
        side : int | float
            Length of each side.

        num_of_sides : int
            Number of sides of the polygon.

        Raises
        ------
        ValueError
            If the side is not positive or number of sides smaller than 3.
        """
        super().__init__(num_of_sides=num_of_sides)

        if side <= 0:
            raise ValueError("Side length must be a positive number.")

        self.side = side

    @override
    def perimeter(self) -> int | float:
        """
        Calculate the perimeter of the polygon.

        Returns
        -------
        int | float
            The perimeter of the polygon.
        """
        return self.side * self._num_of_sides

    @abstractmethod
    @override
    def area(self):
        pass

    def interior_angle(self) -> float:
        """
        Calculate the interior angle of the polygon.

        Returns
        -------
        float
            The interior angle in degrees.
        """
        return (self._num_of_sides - 2) * 180 / self._num_of_sides


class ThreeDimensionShape(ABC, Shape):
    SHAPE_LIST: ClassVar[list[str]] = []

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        # cls.SHAPE_LIST.append(cls)  # append type
        cls.SHAPE_LIST.append(cls.__name__)  # append name

    @abstractmethod
    def surface_area(self):
        pass

    @abstractmethod
    def volume(self):
        pass


# Class - Polygon
# ---------------------------------------------------------------------------
class Triangle(Polygon):
    def __init__(
        self,
        a: int | float,
        b: int | float,
        c: int | float,
    ) -> None:
        """
        Initializes a Triangle instance with three sides.

        Parameters
        ----------
        a : int | float
            The length of the first side.

        b : int | float
            The length of the second side.

        c : int | float
            The length of the third side.

        Raises
        ------
        ValueError
            If any side length is not positive or if the sides do not form a valid triangle.
        """
        super().__init__(num_of_sides=3)

        if a <= 0 or b <= 0 or c <= 0:
            raise ValueError("Side lengths must be positive.")

        # Check for triangle inequality theorem
        if (a + b <= c) or (a + c <= b) or (b + c <= a):
            raise ValueError("The provided lengths do not form a valid triangle.")

        self.a = a
        self.b = b
        self.c = c

    @override
    def perimeter(self) -> int | float:
        """
        Calculates and returns the perimeter of the triangle.
        """
        return self.a + self.b + self.c

    @override
    def area(self) -> int | float:
        """
        Calculates and returns the area of the triangle using Heron's formula.
        """
        s = self.perimeter() / 2  # Semi-perimeter
        # Heron formula
        res = math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))
        return res

    def is_right_angled(self) -> bool:
        """
        Checks if the triangle is a right-angled triangle
        (one vertex has degree of 90) using the Pythagorean theorem.

        Returns
        -------
        bool
            ``True`` if the triangle is right-angled, ``False`` otherwise.
        """
        sides = sorted([self.a, self.b, self.c])
        # return (
        #     sides[0] ** 2 + sides[1] ** 2 == sides[2] ** 2
        # )  # Pytagorean formula

        # Using ``==`` to compare floating-point numbers can be
        # unreliable due to precision issues. Use a tolerance instead
        return abs(sides[2] ** 2 - (sides[0] ** 2 + sides[1] ** 2)) < 1e-6

    def is_equilateral(self) -> bool:
        """
        Checks if the triangle is an equilateral triangle
        (3 sides have the same length).

        Returns
        -------
        bool
            ``True`` if the triangle is equilateral, ``False`` otherwise.
        """
        return self.a == self.b and self.b == self.c

    def is_isosceles(self) -> bool:
        """
        Checks if the triangle is an isosceles triangle
        (at least two sides are equal).

        Returns
        -------
        bool
            ``True`` if the triangle is isosceles, ``False`` otherwise.
        """
        return self.a == self.b or self.b == self.c or self.c == self.a

    def triangle_type(self) -> str:
        """
        Determines the type of triangle based on its sides.

        Returns
        -------
        str
            A string describing the type of triangle: ``"equilateral"``, ``"isosceles"``,
            ``"right-angled"``, or ``"scalene"`` if none of the other types apply.
        """

        if self.is_equilateral():
            return "equilateral"
        elif self.is_isosceles():
            if self.is_right_angled():
                return "right-angled isosceles"
            return "isosceles"
        elif self.is_right_angled():
            return "right-angled"
        else:
            return "scalene"

    def is_acute(self) -> bool:
        """
        Checks if the triangle is an acute triangle
        (all angles less than 90 degrees).

        Returns
        -------
        bool
            ``True`` if the triangle is acute, ``False`` otherwise.
        """
        sides = sorted([self.a, self.b, self.c])
        return sides[0] ** 2 + sides[1] ** 2 > sides[2] ** 2

    def is_obtuse(self) -> bool:
        """
        Checks if the triangle is an obtuse triangle
        (one angle greater than 90 degrees).

        Returns
        -------
        bool
            ``True`` if the triangle is obtuse, ``False`` otherwise.
        """
        sides = sorted([self.a, self.b, self.c])
        return sides[0] ** 2 + sides[1] ** 2 < sides[2] ** 2

    def get_angles(self) -> tuple[float, float, float]:
        """
        Calculates and returns the angles of the triangle in degrees.

        Returns
        -------
        tuple[float, float, float]
            A tuple containing the angles in degrees (angle_A, angle_B, angle_C).
        """
        a, b, c = self.a, self.b, self.c
        angle_A = math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
        angle_B = math.degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
        angle_C = math.degrees(math.acos((a**2 + b**2 - c**2) / (2 * a * b)))
        return angle_A, angle_B, angle_C

    def scale(self, factor: int | float) -> None:
        """
        Scales the triangle by a given factor, changing the lengths of all sides.

        Parameters
        ----------
        factor : int | float
            The scaling factor.  Must be positive.

        Raises
        ------
        ValueError
            If the scaling factor is not positive.
        """
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")
        self.a *= factor
        self.b *= factor
        self.c *= factor

    def is_similar(self, other: Self) -> bool:
        """
        Checks if this triangle is similar to another triangle.

        Parameters
        ----------
        other : Triangle
            The other triangle to compare to.

        Returns
        -------
        bool
            ``True`` if the triangles are similar, ``False`` otherwise.
        """
        ratios = sorted([self.a / other.a, self.b / other.b, self.c / other.c])
        return abs(ratios[0] - ratios[2]) < 1e-6

    def vis(self) -> str:
        """Visualization of Triangle"""
        out = """
              A
             /\\
         c /....\\b
        B/........\\C
               a
        """
        return out


class Circle(Polygon):
    def __init__(self, radius: int | float) -> None:
        """
        Initializes a Circle instance with a specified radius.

        Parameters
        ----------
        radius : int | float
            The radius of the circle. Must be positive.

        Raises
        ------
        ValueError
            If the radius is not positive.
        """
        if radius <= 0:
            raise ValueError("Radius must be a positive number.")
        self.radius = radius

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            raise NotImplementedError("Not supported")
        return math.isclose(self.radius, other.radius)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            raise NotImplementedError("Not supported")
        return self.radius < other.radius

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            raise NotImplementedError("Not supported")
        return self.radius <= other.radius

    def diameter(self) -> int | float:
        """Returns the diameter of the circle."""
        return 2 * self.radius

    @override
    def perimeter(self) -> float:
        """Returns the circumference of the circle."""
        return 2 * math.pi * self.radius

    def circumference(self) -> float:
        """Returns the circumference of the circle."""
        return self.perimeter()  # type: ignore

    @override
    def area(self) -> float:
        """Returns the area of the circle."""
        return math.pi * self.radius**2

    def scale(self, factor: int | float) -> None:
        """
        Scales the circle by a given factor, changing its radius.

        Parameters
        ----------
        factor : int | float
            The scaling factor. Must be positive.

        Raises
        ------
        ValueError
            If the scaling factor is not positive.
        """
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")

        self.radius *= factor

    @classmethod
    def from_area(cls, area: int | float) -> Self:
        """
        Creates a Circle instance from its area.

        Parameters
        ----------
        area : int | float
            The area of the circle. Must be positive.

        Raises
        ------
        ValueError
            If the area is not positive.
        """
        if area <= 0:
            raise ValueError("Area must be positive.")

        radius = math.sqrt(area / math.pi)
        return cls(radius)

    @classmethod
    def from_circumference(cls, circumference: int | float) -> Self:
        """
        Creates a Circle instance from its circumference.

        Parameters
        ----------
        circumference : int | float
            The circumference of the circle. Must be positive.

        Raises
        ------
        ValueError
            If the circumference is not positive.
        """
        if circumference <= 0:
            raise ValueError("Circumference must be positive.")

        radius = circumference / (2 * math.pi)
        return cls(radius)


class Square(EqualSidesPolygon):
    def __init__(self, side: int | float) -> None:
        """
        Initializes a Square instance with specified side.

        Parameters
        ----------
        side : int | float
            The length of the rectangle. Must be positive.

        Raises
        ------
        ValueError
            If the side is not positive.
        """
        super().__init__(side=side, num_of_sides=4)

    @override
    def area(self) -> int | float:
        """Calculate the area of the square."""
        return self.side**2

    def diagonal(self) -> float:
        """Calculate the length of the diagonal of the square."""
        return math.sqrt(2) * self.side

    @classmethod
    def from_perimeter(cls, perimeter: int | float) -> Self:
        """Create a Square instance from its perimeter."""
        if perimeter <= 0:
            raise ValueError("Perimeter must be a positive number.")
        return cls(perimeter / 4)

    @classmethod
    def from_area(cls, area: int | float) -> Self:
        """Create a Square instance from its area."""
        if area <= 0:
            raise ValueError("Area must be a positive number.")
        return cls(math.sqrt(area))

    def scale(self, factor: int | float) -> None:
        """
        Scales the square by a given factor.

        Parameters
        ----------
        factor : int | float
            The scaling factor. Must be positive.

        Raises
        ------
        ValueError
            If the scaling factor is not positive.
        """
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")

        self.side *= factor


class Rectangle(Polygon):
    def __init__(self, length: int | float, width: int | float) -> None:
        """
        Initializes a Rectangle instance with specified length and width.

        Parameters
        ----------
        length : int | float
            The length of the rectangle. Must be positive.
        width : int | float
            The width of the rectangle. Must be positive.

        Raises
        ------
        ValueError
            If either length or width is not positive.
        """
        super().__init__(num_of_sides=4)

        if length <= 0 or width <= 0:
            raise ValueError("Length and width must be positive numbers.")

        self.length = max(length, width)
        self.width = min(length, width)

    @override
    def perimeter(self) -> int | float:
        """Calculates and returns the perimeter of the rectangle."""
        return 2 * (self.length + self.width)

    @override
    def area(self) -> int | float:
        """Calculates and returns the area of the rectangle."""
        return self.length * self.width

    def diagonal(self) -> float:
        """Calculates and returns the length of the diagonal of the rectangle."""
        return math.sqrt(self.length**2 + self.width**2)

    def is_square(self) -> bool:
        """Checks if the rectangle is a square (length equals width)."""
        return self.length == self.width

    def scale(self, factor: int | float) -> None:
        """
        Scales the rectangle by a given factor.

        Parameters
        ----------
        factor : int | float
            The scaling factor. Must be positive.

        Raises
        ------
        ValueError
            If the scaling factor is not positive.
        """
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")

        self.length *= factor
        self.width *= factor


class Pentagon(EqualSidesPolygon):
    def __init__(self, side: int | float) -> None:
        """
        Initializes a Pentagon instance with a specified side length.

        Parameters
        ----------
        side : int | float
            The length of one side of the pentagon. Must be positive.

        Raises
        ------
        ValueError
            If the side length is not positive.
        """
        super().__init__(side=side, num_of_sides=5)

    @override
    def area(self) -> float:
        """Calculates and returns the area of the pentagon using a specific formula."""
        res = 0.25 * math.sqrt(5 * (5 + 2 * math.sqrt(5))) * self.side**2
        return res

    def apothem(self) -> float:
        """Calculates and returns the apothem of the pentagon."""
        res = (self.side / 2) / math.tan(36 * math.pi / 180)
        return res

    def area2(self) -> float:
        """Calculates the area using the apothem and perimeter."""
        res = 0.5 * self.perimeter() * self.apothem()
        return res  # type: ignore

    @classmethod
    def from_area(cls, area: int | float) -> Self:
        """
        Creates a Pentagon instance from its area.

        Parameters
        ----------
        area : int | float
            The area of the pentagon. Must be positive.

        Raises
        ------
        ValueError
            If the area is not positive.
        """
        if area <= 0:
            raise ValueError("Area must be positive.")

        # Calculate side length from area
        side = math.sqrt((4 * area)) / math.sqrt(math.sqrt(5 * (5 + 2 * math.sqrt(5))))
        return cls(side)

    @classmethod
    def from_perimeter(cls, perimeter: int | float) -> Self:
        """
        Creates a Pentagon instance from its perimeter.

        Parameters
        ----------
        perimeter : int | float
            The perimeter of the pentagon. Must be positive.

        Raises
        ------
        ValueError
            If the perimeter is not positive.
        """
        if perimeter <= 0:
            raise ValueError("Perimeter must be positive.")

        # Calculate side length from perimeter
        side = perimeter / 5
        return cls(side)


class Hexagon(EqualSidesPolygon):
    def __init__(self, side: int | float) -> None:
        """
        Initializes a Hexagon instance with a specified side length.

        Parameters
        ----------
        side : int | float
            The length of one side of the hexagon. Must be positive.

        Raises
        ------
        ValueError
            If the side length is not positive.
        """
        super().__init__(side=side, num_of_sides=6)

    @override
    def area(self) -> float:
        """Calculates and returns the area of the hexagon."""
        res = self.side**2 * (3 * math.sqrt(3) / 2)
        return res

    def apothem(self) -> float:
        """Calculates and returns the apothem of the hexagon."""
        return self.side / (2 * math.tan(math.pi / 6))

    def area2(self) -> float:
        """Calculates the area using the apothem and perimeter."""
        return 0.5 * self.perimeter() * self.apothem()  # type: ignore

    @classmethod
    def from_area(cls, area: int | float) -> Self:
        """
        Creates a Hexagon instance from its area.

        Parameters
        ----------
        area : int | float
            The area of the hexagon. Must be positive.

        Raises
        ------
        ValueError
            If the area is not positive.
        """
        if area <= 0:
            raise ValueError("Area must be positive.")

        # Calculate side length from area
        side = math.sqrt((2 * area) / (3 * math.sqrt(3)))
        return cls(side)

    @classmethod
    def from_perimeter(cls, perimeter: int | float) -> Self:
        """
        Creates a Hexagon instance from its perimeter.

        Parameters
        ----------
        perimeter : int | float
            The perimeter of the hexagon. Must be positive.

        Raises
        ------
        ValueError
            If the perimeter is not positive.
        """
        if perimeter <= 0:
            raise ValueError("Perimeter must be positive.")

        # Calculate side length from perimeter
        side = perimeter / 6
        return cls(side)


class Parallelogram(Polygon):
    def __init__(
        self,
        base: int | float,
        height: int | float,
        *,
        a: int | float | None = None,
        phi: int | float | None = None,
    ) -> None:
        """
        Initializes a Parallelogram instance with specified dimensions.

        Parameters
        ----------
        base : int | float
            The length of the base of the parallelogram. Must be positive.

        height : int | float
            The height of the parallelogram. Must be positive.

        a : int | float | None
            The length of one side of the parallelogram. Must be positive if provided.

        phi : int | float | None
            The angle in degrees opposite the base, adjacent to height. Must be between 0 and 180 if provided.

        Raises
        ------
        ValueError
            If base or height is not positive, or if angle is not in valid range.
        """
        super().__init__(num_of_sides=4)

        if base <= 0:
            raise ValueError("Base must be a positive number.")

        if height <= 0:
            raise ValueError("Height must be a positive number.")

        if a is not None and a <= 0:
            raise ValueError("Side 'a' must be a positive number.")

        if phi is not None and (phi <= 0 or phi >= 180):
            raise ValueError("Angle 'phi' must be between 0 and 180 degrees.")

        self.base = base
        self.height = height
        self.a = a
        self.phi = phi

    @override
    def perimeter(self) -> int | float:
        """
        Calculates and returns the perimeter of the parallelogram.

        Raises
        ------
        ValueError
            If neither side ``a`` nor angle ``phi`` is provided.
        """
        if self.a is not None:
            return 2 * (self.base + self.a)
        if self.phi is not None:
            side_b = self.height / math.sin(math.radians(self.phi))
            return 2 * (self.base + side_b)
            # return 2 * (self.base + self.height * math.cos(self.phi * math.pi / 180))
        raise ValueError("Side a or phi must be provided")

    @override
    def area(self) -> int | float:
        """Calculates and returns the area of the parallelogram."""
        return self.base * self.height


class Rhombus(Polygon):
    def __init__(self, d1: int | float, d2: int | float) -> None:
        """
        Initializes a Rhombus instance with specified diagonal lengths.

        Parameters
        ----------
        d1 : int | float
            The length of the first diagonal. Must be positive.

        d2 : int | float
            The length of the second diagonal. Must be positive.

        Raises
        ------
        ValueError
            If either diagonal length is not positive.
        """
        super().__init__(num_of_sides=4)

        if d1 <= 0:
            raise ValueError("Diagonal d1 must be a positive number.")

        if d2 <= 0:
            raise ValueError("Diagonal d2 must be a positive number.")

        self.d1 = d1
        self.d2 = d2

    @override
    def perimeter(self) -> float:
        """Calculates and returns the perimeter of the rhombus."""
        return 2 * math.sqrt(self.d1**2 + self.d2**2)

    @override
    def area(self) -> float:
        """Calculates and returns the area of the rhombus."""
        return (self.d1 * self.d2) / 2

    def side(self) -> float:
        """Calculates and returns the length of one side of the rhombus."""
        return self.perimeter() / self._num_of_sides  # type: ignore


class Trapezoid(Polygon):
    def __init__(
        self,
        a: int | float,
        b: int | float,
        c: int | float | None = None,
        d: int | float | None = None,
        h: int | float | None = None,
    ) -> None:
        """
        Initializes a Trapezoid instance with specified dimensions.

        Parameters
        ----------
        a : int | float
            The length of base 1. Must be positive.

        b : int | float
            The length of base 2. Must be positive.

        c : int | float | None
            The length of side 1. Must be positive if provided.

        d : int | float | None
            The length of side 2. Must be positive if provided.

        h : int | float | None
            The height of the trapezoid. Must be positive if provided.

        Raises
        ------
        ValueError
            If base lengths or height are not positive, or if both sides are not provided.
        """
        super().__init__(num_of_sides=4)

        if a <= 0:
            raise ValueError("Base 'a' must be a positive number.")

        if b <= 0:
            raise ValueError("Base 'b' must be a positive number.")

        if c is not None and c <= 0:
            raise ValueError("Side 'c' must be a positive number.")

        if d is not None and d <= 0:
            raise ValueError("Side 'd' must be a positive number.")

        if h is not None and h <= 0:
            raise ValueError("Height 'h' must be a positive number.")

        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.h = h

    @override
    def perimeter(self) -> int | float:
        """Calculates and returns the perimeter of the trapezoid."""
        if self.c is not None and self.d is not None:
            return sum([self.a, self.b, self.c, self.d])
        raise ValueError("'c' and 'd' must be provided to calculate perimeter.")

    @override
    def area(self) -> float:
        """Calculates and returns the area of the trapezoid."""
        if self.h is not None:
            return 0.5 * (self.a + self.b) * self.h
        raise ValueError("'h' must be provided to calculate area.")


# Class - 3D Shape
# ---------------------------------------------------------------------------
class Cube(ThreeDimensionShape):
    def __init__(self, side: int | float) -> None:
        """
        Initializes a Cube instance with a specified side length.

        Parameters
        ----------
        side : int | float
            The length of one side of the cube. Must be positive.

        Raises
        ------
        ValueError
            If the side length is not positive.
        """
        if side <= 0:
            raise ValueError("Side length must be a positive number.")

        self.side = side

    @override
    def surface_area(self) -> int | float:
        """Calculates and returns the surface area of the cube."""
        return 6 * self.side**2

    def surface_area_side(self) -> int | float:
        """Calculates and returns the surface area (side only) of the cube."""
        return 4 * self.side**2

    @override
    def volume(self) -> int | float:
        """Calculates and returns the volume of the cube."""
        return self.side**3

    def face_area(self) -> int | float:
        """Calculates and returns the area of one face of the cube."""
        return self.side**2

    def diagonal(self) -> float:
        """Calculates and returns the length of the space diagonal of the cube."""
        return self.side * math.sqrt(3)

    def scale(self, factor: int | float) -> None:
        """Scales the cube by a given factor."""
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")

        self.side *= factor

    @classmethod
    def from_surface_area(cls, surface_area: int | float) -> Self:
        """
        Creates a Cube instance from its surface area.

        Parameters
        ----------
        surface_area : int | float
            The surface area of the cube. Must be positive.

        Raises
        ------
        ValueError
            If surface area is not positive.
        """
        if surface_area <= 0:
            raise ValueError("Surface area must be positive.")

        # Calculate side length from surface area
        side = math.sqrt(surface_area / 6)
        return cls(side)

    @classmethod
    def from_volume(cls, volume: int | float) -> Self:
        """
        Creates a Cube instance from its volume.

        Parameters
        ----------
        volume : int | float
            The volume of the cube. Must be positive.

        Raises
        ------
        ValueError
            If volume is not positive.
        """
        if volume <= 0:
            raise ValueError("Volume must be positive.")

        # Calculate side length from volume
        side = volume ** (1 / 3)
        return cls(side)


class Cuboid(ThreeDimensionShape):
    def __init__(
        self,
        length: int | float,
        width: int | float,
        height: int | float,
    ) -> None:
        """
        Initializes a Cuboid instance with specified dimensions.

        Parameters
        ----------
        length : int | float
            The length of the cuboid. Must be positive.

        width : int | float
            The width of the cuboid. Must be positive.

        height : int | float
            The height of the cuboid. Must be positive.

        Raises
        ------
        ValueError
            If any dimension is not positive.
        """
        if length <= 0:
            raise ValueError("Length must be a positive number.")

        if width <= 0:
            raise ValueError("Width must be a positive number.")

        if height <= 0:
            raise ValueError("Height must be a positive number.")

        self.length = length
        self.width = width
        self.height = height

    @override
    def surface_area(self) -> int | float:
        """Calculates and returns the surface area of the cuboid."""
        res = 2 * (
            self.length * self.width
            + self.width * self.height
            + self.length * self.height
        )
        return res

    def surface_area_side(self) -> int | float:
        """Calculates and returns the surface area of the sides of the cuboid."""
        res = 2 * self.height * (self.length + self.width)
        return res

    @override
    def volume(self) -> int | float:
        """Calculates and returns the volume of the cuboid."""
        return self.length * self.width * self.height

    def diagonal(self) -> float:
        """Calculates and returns the length of the space diagonal of the cuboid."""
        return math.sqrt(self.length**2 + self.width**2 + self.height**2)

    def scale(self, factor: int | float) -> None:
        """Scales the dimensions of the cuboid by a given factor."""
        if factor <= 0:
            raise ValueError("Scaling factor must be positive.")

        self.length *= factor
        self.width *= factor
        self.height *= factor


class Sphere(ThreeDimensionShape):
    def __init__(self, radius: int | float) -> None:
        """
        Initializes a Sphere instance with the specified radius.

        Parameters
        ----------
        radius : int | float
            The radius of the sphere. Must be positive.

        Raises
        ------
        ValueError
            If radius is not positive.
        """
        if radius <= 0:
            raise ValueError("Radius must be a positive number.")

        self.radius = radius

    @override
    def surface_area(self) -> float:
        """Calculates and returns the surface area of the sphere."""
        return 4 * math.pi * self.radius**2

    @override
    def volume(self) -> float:
        """Calculates and returns the volume of the sphere."""
        return (4 / 3) * math.pi * self.radius**3

    @classmethod
    def from_volume(cls, volume: int | float) -> Self:
        """
        Creates a Sphere instance from its volume.

        Parameters
        ----------
        volume : int | float
            The volume of the sphere. Must be positive.

        Raises
        ------
        ValueError
            If volume is not positive.
        """
        if volume <= 0:
            raise ValueError("Volume must be a positive number.")

        radius = ((3 * volume) / (4 * math.pi)) ** (1 / 3)
        return cls(radius)

    @classmethod
    def from_surface_area(cls, surface_area: int | float) -> Self:
        """
        Creates a Sphere instance from its surface area.

        Parameters
        ----------
        surface_area : int | float
            The surface area of the sphere. Must be positive.

        Raises
        ------
        ValueError
            If surface area is not positive.
        """
        if surface_area <= 0:
            raise ValueError("Surface area must be a positive number.")

        radius = math.sqrt(surface_area / (4 * math.pi))
        return cls(radius)


class HemiSphere(ThreeDimensionShape):
    def __init__(self, radius: int | float) -> None:
        """
        Initializes a HemiSphere instance with the specified radius.

        Parameters
        ----------
        radius : int | float
            The radius of the hemisphere. Must be positive.

        Raises
        ------
        ValueError
            If the radius is not positive.
        """
        if radius <= 0:
            raise ValueError("Radius must be a positive number.")

        self.radius = radius

    @override
    def surface_area(self) -> float:
        """
        Calculates and returns the total surface area of the hemisphere.
        """
        return 3 * math.pi * self.radius**2

    def surface_area_curved(self) -> float:
        """
        Calculates and returns the curved surface area of the hemisphere.
        """
        return 2 * math.pi * self.radius**2

    def surface_area_base(self) -> float:
        """
        Calculates and returns the area of the base (circular) of the hemisphere.
        """
        return math.pi * self.radius**2

    @override
    def volume(self) -> float:
        """
        Calculates and returns the volume of the hemisphere.
        """
        return (2 / 3) * math.pi * self.radius**3

    @classmethod
    def from_volume(cls, volume: int | float) -> Self:
        """
        Creates a HemiSphere instance from its volume.

        Parameters
        ----------
        volume : int | float
            The volume of the hemisphere. Must be positive.

        Raises
        ------
        ValueError
            If the volume is not positive.
        """
        if volume <= 0:
            raise ValueError("Volume must be positive.")

        radius = (3 * volume / (2 * math.pi)) ** (1 / 3)
        return cls(radius)

    @classmethod
    def from_surface_area(cls, surface_area: int | float) -> Self:
        """
        Creates a HemiSphere instance from its total surface area.

        Parameters
        ----------
        surface_area : int | float
            The total surface area of the hemisphere. Must be positive.

        Raises
        ------
        ValueError
            If the surface area is not positive.
        """
        if surface_area <= 0:
            raise ValueError("Surface area must be positive.")

        radius = math.sqrt(surface_area / (3 * math.pi))
        return cls(radius)


class Cylinder(ThreeDimensionShape):
    def __init__(self, radius: int | float, height: int | float) -> None:
        """
        Initializes a Cylinder instance with the specified radius and height.

        Parameters
        ----------
        radius : int | float
            The radius of the cylinder. Must be positive.

        height : int | float
            The height of the cylinder. Must be positive.

        Raises
        ------
        ValueError
            If radius or height is not positive.
        """
        if radius <= 0:
            raise ValueError("Radius must be a positive number.")

        if height <= 0:
            raise ValueError("Height must be a positive number.")

        self.radius = radius
        self.height = height

    @override
    def surface_area(self) -> float:
        """Calculates and returns the total surface area of the cylinder."""
        res = 2 * math.pi * self.radius * (self.radius + self.height)
        return res

    def surface_area_curved(self) -> float:
        """Calculates and returns the curved surface area of the cylinder."""
        res = 2 * math.pi * self.radius * self.height
        return res

    @override
    def volume(self) -> float:
        """Calculates and returns the volume of the cylinder."""
        return math.pi * self.radius**2 * self.height
