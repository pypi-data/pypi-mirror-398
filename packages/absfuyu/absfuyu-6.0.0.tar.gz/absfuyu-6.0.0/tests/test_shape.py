"""
Test: Shape

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

import math

import pytest

from absfuyu.general.shape import (
    Circle,
    Cube,
    Cuboid,
    Cylinder,
    HemiSphere,
    Hexagon,
    Parallelogram,
    Pentagon,
    Rectangle,
    Rhombus,
    Sphere,
    Square,
    Trapezoid,
    Triangle,
)


@pytest.mark.abs_shape
class TestTriangle:
    def test_initialization_valid(self) -> None:
        """Test valid triangle initialization."""
        triangle = Triangle(3, 4, 5)
        assert triangle.a == 3
        assert triangle.b == 4
        assert triangle.c == 5

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative side lengths."""
        with pytest.raises(ValueError, match="Side lengths must be positive."):
            Triangle(-1, 2, 3)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero side lengths."""
        with pytest.raises(ValueError, match="Side lengths must be positive."):
            Triangle(0, 1, 2)

    def test_initialization_invalid_triangle_inequality(self) -> None:
        """Test initialization that violates the triangle inequality theorem."""
        with pytest.raises(
            ValueError, match="The provided lengths do not form a valid triangle."
        ):
            Triangle(1, 2, 3)  # 1 + 2 is not greater than 3

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        triangle = Triangle(3, 4, 5)
        assert triangle.perimeter() == 12

    def test_area(self) -> None:
        """Test area calculation using Heron's formula."""
        triangle = Triangle(3, 4, 5)
        assert math.isclose(triangle.area(), 6.0)

    def test_is_right_angled(self) -> None:
        """Test right-angled triangle detection."""
        right_triangle = Triangle(3, 4, 5)
        assert right_triangle.is_right_angled() is True

        not_right_triangle = Triangle(2, 2, 3)
        assert not_right_triangle.is_right_angled() is False

    def test_is_equilateral(self) -> None:
        """Test equilateral triangle detection."""
        equilateral_triangle = Triangle(5, 5, 5)
        assert equilateral_triangle.is_equilateral() is True

        not_equilateral_triangle = Triangle(5, 5, 4)
        assert not_equilateral_triangle.is_equilateral() is False

    def test_is_isosceles(self) -> None:
        """Test isosceles triangle detection."""
        isosceles_triangle = Triangle(5, 5, 3)
        assert isosceles_triangle.is_isosceles() is True

        not_isosceles_triangle = Triangle(3, 4, 5)
        assert not_isosceles_triangle.is_isosceles() is False

    @pytest.mark.parametrize(
        ["a", "b", "c", "result"],
        [
            (5, 5, 5, "equilateral"),
            (5, 5, 3, "isosceles"),
            (1, 1, math.sqrt(2), "right-angled isosceles"),
            (3, 4, 5, "right-angled"),
            (3, 4, 6, "scalene"),
        ],
    )
    def test_triangle_type(
        self, a: int | float, b: int | float, c: int | float, result: str
    ) -> None:
        """Test the type of the triangle."""
        triangle = Triangle(a, b, c)
        assert triangle.triangle_type() == result

    def test_is_acute(self) -> None:
        """Test acute triangle detection."""
        acute_triangle = Triangle(4, 5, 6)  # Angles <90 degrees
        assert acute_triangle.is_acute() is True

        obtuse_triangle = Triangle(3, 4, 6)  # One angle >90 degrees
        assert obtuse_triangle.is_acute() is False

    def test_is_obtuse(self) -> None:
        """Test obtuse triangle detection."""
        obtuse_triangle = Triangle(3, 4, 6)  # One angle >90 degrees
        assert obtuse_triangle.is_obtuse() is True

        acute_triangle = Triangle(4, 5, 6)  # Angles <90 degrees
        assert acute_triangle.is_obtuse() is False

    def test_get_angles(self) -> None:
        """Test angle calculation."""
        triangle = Triangle(3, 4, 5)

        angles = [round(x, 2) for x in triangle.get_angles()]

        # Check if angles are approximately correct (in degrees)
        expected_angles = [36.87, 53.13, 90.0]

        for angle in angles:
            assert any(
                math.isclose(angle, expected_angle, abs_tol=1e-4)
                for expected_angle in expected_angles
            )

    def test_scale(self) -> None:
        """Test scaling of the triangle."""
        triangle = Triangle(3, 4, 5)

        # Scale by a factor of 2
        triangle.scale(2)

        assert triangle.a == 6
        assert triangle.b == 8
        assert triangle.c == 10

    def test_scale_invalid_factor(self) -> None:
        """Test scaling with an invalid factor."""
        triangle = Triangle(3, 4, 5)

        with pytest.raises(ValueError) as excinfo:
            triangle.scale(-1)
        assert str(excinfo.value) == "Scaling factor must be positive."

    def test_is_similar(self) -> None:
        """Test similarity of triangles."""
        triangle1 = Triangle(3, 4, 5)
        triangle2 = Triangle(6, 8, 10)  # Similar to triangle1 (scaled by factor of two)

        assert triangle1.is_similar(triangle2) is True

        different_triangle = Triangle(7, 8, 9)
        assert triangle1.is_similar(different_triangle) is False


@pytest.mark.abs_shape
class TestCircle:
    def test_initialization_valid(self) -> None:
        """Test valid circle initialization."""
        circle = Circle(5)
        assert circle.radius == 5

    def test_initialization_invalid(self) -> None:
        """Test initialization with invalid (non-positive) radius."""
        with pytest.raises(ValueError, match="Radius must be a positive number."):
            Circle(-1)
        with pytest.raises(ValueError, match="Radius must be a positive number."):
            Circle(0)

    def test_diameter(self) -> None:
        """Test diameter calculation."""
        circle = Circle(5)
        assert circle.diameter() == 10

    def test_perimeter(self) -> None:
        """Test perimeter calculation (same as circumference)."""
        circle = Circle(5)
        assert math.isclose(circle.perimeter(), 2 * math.pi * 5)

    def test_circumference(self) -> None:
        """Test circumference calculation."""
        circle = Circle(5)
        assert math.isclose(circle.circumference(), 2 * math.pi * 5)

    def test_area(self) -> None:
        """Test area calculation."""
        circle = Circle(5)
        assert math.isclose(circle.area(), math.pi * 5**2)

    def test_scale_valid(self) -> None:
        """Test scaling with a valid (positive) factor."""
        circle = Circle(5)
        circle.scale(2)
        assert circle.radius == 10

    def test_scale_invalid(self) -> None:
        """Test scaling with an invalid (non-positive) factor."""
        circle = Circle(5)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            circle.scale(-1)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            circle.scale(0)

    def test_equality(self) -> None:
        """Test equality comparison (__eq__)."""
        circle1 = Circle(5)
        circle2 = Circle(5)
        circle3 = Circle(6)
        assert circle1 == circle2
        assert not (circle1 == circle3)

    def test_less_than(self) -> None:
        """Test less than comparison (__lt__)."""
        circle1 = Circle(5)
        circle2 = Circle(6)
        assert circle1 < circle2
        assert not (circle2 < circle1)
        assert not (circle1 < circle1)  # Not less than itself

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal comparison (__le__)."""
        circle1 = Circle(5)
        circle2 = Circle(6)
        circle3 = Circle(5)
        assert circle1 <= circle2
        assert circle1 <= circle3
        assert not (circle2 <= circle1)

    def test_from_area_valid(self) -> None:
        circle = Circle.from_area(math.pi * 5**2)  # Area of circle with radius 5
        assert math.isclose(circle.radius, 5)
        assert Circle(5).radius == Circle.from_area(Circle(5).area()).radius

    def test_from_area_invalid(self) -> None:
        with pytest.raises(ValueError, match="Area must be positive."):
            Circle.from_area(-10)

    def test_from_circumference_valid(self) -> None:
        circle = Circle.from_circumference(
            2 * math.pi * 5
        )  # Circumference of circle with radius 5
        assert math.isclose(circle.radius, 5)
        assert (
            Circle(5).radius
            == Circle.from_circumference(Circle(5).circumference()).radius
        )

    def test_from_circumference_invalid(self) -> None:
        with pytest.raises(ValueError, match="Circumference must be positive."):
            Circle.from_circumference(-10)


@pytest.mark.abs_shape
class TestSquare:
    def test_valid_side(self) -> None:
        square = Square(5)
        assert square.side == 5

    def test_invalid_side(self) -> None:
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Square(-5)
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Square(0)

    def test_perimeter(self) -> None:
        square = Square(5)
        assert square.perimeter() == 20

    def test_area(self) -> None:
        square = Square(5)
        assert square.area() == 25

    def test_diagonal(self) -> None:
        square = Square(5)
        assert square.diagonal() == math.sqrt(2) * 5

    def test_from_perimeter_valid(self) -> None:
        square = Square.from_perimeter(20)
        assert square.side == 5
        assert Square(5).side == Square.from_perimeter(Square(5).perimeter()).side

    def test_from_perimeter_invalid(self) -> None:
        with pytest.raises(ValueError, match="Perimeter must be a positive number."):
            Square.from_perimeter(-20)

    def test_from_area_valid(self) -> None:
        square = Square.from_area(25)
        assert square.side == 5
        assert Square(5).side == Square.from_area(Square(5).area()).side

    def test_from_area_invalid(self) -> None:
        with pytest.raises(ValueError, match="Area must be a positive number."):
            Square.from_area(-25)

    def test_scale_valid(self) -> None:
        """Test scaling with a valid (positive) factor."""
        square = Square(5)
        square.scale(2)
        assert square.side == 10

    def test_scale_invalid(self) -> None:
        """Test scaling with an invalid (non-positive) factor."""
        square = Square(5)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            square.scale(-1)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            square.scale(0)


@pytest.mark.abs_shape
class TestRectangle:
    def test_initialization_valid(self) -> None:
        """Test valid rectangle initialization."""
        rectangle = Rectangle(5, 3)
        assert rectangle.length == 5
        assert rectangle.width == 3

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative length or width."""
        with pytest.raises(
            ValueError, match="Length and width must be positive numbers."
        ):
            Rectangle(-1, 2)
        with pytest.raises(
            ValueError, match="Length and width must be positive numbers."
        ):
            Rectangle(0, 1)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero length or width."""
        with pytest.raises(
            ValueError, match="Length and width must be positive numbers."
        ):
            Rectangle(0, 0)

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        rectangle = Rectangle(5, 3)
        assert rectangle.perimeter() == 16

    def test_area(self) -> None:
        """Test area calculation."""
        rectangle = Rectangle(5, 3)
        assert rectangle.area() == 15

    def test_diagonal(self) -> None:
        """Test diagonal calculation."""
        rectangle = Rectangle(5, 3)
        assert math.isclose(rectangle.diagonal(), math.sqrt(5**2 + 3**2))

    def test_is_square_true(self) -> None:
        """Test is_square method for a square."""
        square = Rectangle(4, 4)
        assert square.is_square() is True

    def test_is_square_false(self) -> None:
        """Test is_square method for a non-square rectangle."""
        rectangle = Rectangle(5, 3)
        assert rectangle.is_square() is False

    def test_scale_valid(self) -> None:
        """Test scaling with a valid (positive) factor."""
        rectangle = Rectangle(5, 3)
        rectangle.scale(2)

        assert rectangle.length == 10
        assert rectangle.width == 6

    def test_scale_invalid(self) -> None:
        """Test scaling with an invalid (non-positive) factor."""
        rectangle = Rectangle(5, 3)

        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            rectangle.scale(-1)

        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            rectangle.scale(0)


@pytest.mark.abs_shape
class TestPentagon:
    def test_initialization_valid(self) -> None:
        """Test valid pentagon initialization."""
        pentagon = Pentagon(5)
        assert pentagon.side == 5

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Pentagon(-1)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Pentagon(0)

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        pentagon = Pentagon(5)
        assert pentagon.perimeter() == 25

    def test_area(self) -> None:
        """Test area calculation."""
        pentagon = Pentagon(5)
        expected_area = (5 / 4) * (5**2) / math.tan(math.pi / 5)
        assert math.isclose(pentagon.area(), expected_area)

    def test_apothem(self) -> None:
        """Test apothem calculation."""
        pentagon = Pentagon(5)
        expected_apothem = (pentagon.side / 2) / math.tan(math.pi / 5)
        assert math.isclose(pentagon.apothem(), expected_apothem)

    def test_area2(self) -> None:
        """Test area calculation using the apothem."""
        pentagon = Pentagon(5)
        expected_area2 = 0.5 * pentagon.perimeter() * pentagon.apothem()
        assert math.isclose(pentagon.area2(), expected_area2)

    def test_from_area_valid(self) -> None:
        """
        Test creating a Pentagon instance from a valid area.
        """
        area = 43.01193501  # Area of pentagon with side 5
        pentagon = Pentagon.from_area(area)
        assert math.isclose(pentagon.side, 5)
        assert Pentagon(5).side == Pentagon.from_area(Pentagon(5).area()).side

    def test_from_area_invalid(self) -> None:
        """
        Test creating a Pentagon instance from an invalid (negative) area.
        """
        with pytest.raises(ValueError, match="Area must be positive."):
            Pentagon.from_area(-10)

    def test_from_perimeter_valid(self) -> None:
        """
        Test creating a Pentagon instance from a valid perimeter.
        """
        perimeter = 5 * 5  # Perimeter of pentagon with side 5
        pentagon = Pentagon.from_perimeter(perimeter)
        assert math.isclose(pentagon.side, 5)
        assert Pentagon(5).side == Pentagon.from_perimeter(Pentagon(5).perimeter()).side

    def test_from_perimeter_invalid(self) -> None:
        """
        Test creating a Pentagon instance from an invalid (negative) perimeter.
        """
        with pytest.raises(ValueError, match="Perimeter must be positive."):
            Pentagon.from_perimeter(-10)


@pytest.mark.abs_shape
class TestHexagon:
    def test_initialization_valid(self) -> None:
        """Test valid hexagon initialization."""
        hexagon = Hexagon(5)
        assert hexagon.side == 5

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Hexagon(-1)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Hexagon(0)

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        hexagon = Hexagon(5)
        assert hexagon.perimeter() == 30

    def test_area(self) -> None:
        """Test area calculation."""
        hexagon = Hexagon(5)
        expected_area = (3 * math.sqrt(3) / 2) * (5**2)
        assert math.isclose(hexagon.area(), expected_area)

    def test_apothem(self) -> None:
        """Test apothem calculation."""
        hexagon = Hexagon(5)
        expected_apothem = hexagon.side / (2 * math.tan(math.pi / 6))
        assert math.isclose(hexagon.apothem(), expected_apothem)

    def test_from_area_valid(self) -> None:
        """Test creating a Hexagon instance from a valid area."""
        area = (3 * math.sqrt(3) / 2) * (5**2)  # Area of hexagon with side length 5
        hexagon = Hexagon.from_area(area)
        assert math.isclose(hexagon.side, 5)
        assert Hexagon(5).side == Hexagon.from_area(Hexagon(5).area()).side

    def test_from_area_invalid(self) -> None:
        """Test creating a Hexagon instance from an invalid (negative) area."""
        with pytest.raises(ValueError, match="Area must be positive."):
            Hexagon.from_area(-10)

    def test_from_perimeter_valid(self) -> None:
        """Test creating a Hexagon instance from a valid perimeter."""
        perimeter = 6 * 5  # Perimeter of hexagon with side length 5
        hexagon = Hexagon.from_perimeter(perimeter)
        assert math.isclose(hexagon.side, 5)
        assert Hexagon(5).side == Hexagon.from_perimeter(Hexagon(5).perimeter()).side

    def test_from_perimeter_invalid(self) -> None:
        """Test creating a Hexagon instance from an invalid (negative) perimeter."""
        with pytest.raises(ValueError, match="Perimeter must be positive."):
            Hexagon.from_perimeter(-10)


@pytest.mark.abs_shape
class TestParallelogram:
    def test_initialization_valid(self) -> None:
        """Test valid parallelogram initialization."""
        parallelogram = Parallelogram(base=5, height=3, a=4)
        assert parallelogram.base == 5
        assert parallelogram.height == 3
        assert parallelogram.a == 4
        assert parallelogram.phi is None  # phi wasn't specified

    def test_initialization_invalid_base(self) -> None:
        """Test initialization with invalid base."""
        with pytest.raises(ValueError, match="Base must be a positive number."):
            Parallelogram(base=-1, height=3, a=4)
        with pytest.raises(ValueError, match="Base must be a positive number."):
            Parallelogram(base=0, height=3, a=4)

    def test_initialization_invalid_height(self) -> None:
        """Test initialization with invalid height."""
        with pytest.raises(ValueError, match="Height must be a positive number."):
            Parallelogram(base=5, height=-1, a=4)
        with pytest.raises(ValueError, match="Height must be a positive number."):
            Parallelogram(base=5, height=0, a=4)

    def test_initialization_invalid_a(self) -> None:
        """Test initialization with invalid side a."""
        with pytest.raises(ValueError, match="Side 'a' must be a positive number."):
            Parallelogram(base=5, height=3, a=-1)
        with pytest.raises(ValueError, match="Side 'a' must be a positive number."):
            Parallelogram(base=5, height=3, a=0)

    def test_initialization_invalid_phi(self) -> None:
        """Test initialization with invalid angle phi."""
        with pytest.raises(
            ValueError, match="Angle 'phi' must be between 0 and 180 degrees."
        ):
            Parallelogram(base=5, height=3, phi=-1)
        with pytest.raises(
            ValueError, match="Angle 'phi' must be between 0 and 180 degrees."
        ):
            Parallelogram(base=5, height=3, phi=0)
        with pytest.raises(
            ValueError, match="Angle 'phi' must be between 0 and 180 degrees."
        ):
            Parallelogram(base=5, height=3, phi=180)
        with pytest.raises(
            ValueError, match="Angle 'phi' must be between 0 and 180 degrees."
        ):
            Parallelogram(base=5, height=3, phi=181)

    def test_perimeter_with_a(self) -> None:
        """Test perimeter calculation with side a provided."""
        parallelogram = Parallelogram(base=5, height=3, a=4)
        assert parallelogram.perimeter() == 18

    def test_perimeter_with_phi(self) -> None:
        """Test perimeter calculation with angle phi provided."""
        parallelogram = Parallelogram(base=5, height=3, phi=60)
        expected_perimeter = 2 * (5 + 3 / math.sin(math.radians(60)))
        assert math.isclose(parallelogram.perimeter(), expected_perimeter)

    def test_perimeter_invalid(self) -> None:
        """Test perimeter calculation when neither a nor phi is provided."""
        parallelogram = Parallelogram(base=5, height=3)
        with pytest.raises(ValueError, match="Side a or phi must be provided"):
            parallelogram.perimeter()

    def test_area(self) -> None:
        """Test area calculation."""
        parallelogram = Parallelogram(base=5, height=3)
        assert parallelogram.area() == 15


@pytest.mark.abs_shape
class TestRhombus:
    def test_initialization_valid(self) -> None:
        """Test valid rhombus initialization."""
        rhombus = Rhombus(6, 8)
        assert rhombus.d1 == 6
        assert rhombus.d2 == 8

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative diagonal lengths."""
        with pytest.raises(ValueError, match="Diagonal d1 must be a positive number."):
            Rhombus(-1, 8)

        with pytest.raises(ValueError, match="Diagonal d2 must be a positive number."):
            Rhombus(6, -1)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero diagonal lengths."""
        with pytest.raises(ValueError, match="Diagonal d1 must be a positive number."):
            Rhombus(0, 8)

        with pytest.raises(ValueError, match="Diagonal d2 must be a positive number."):
            Rhombus(6, 0)

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        rhombus = Rhombus(6, 8)
        expected_side = rhombus.side()
        assert rhombus.perimeter() == 4 * expected_side

    def test_area(self) -> None:
        """Test area calculation."""
        rhombus = Rhombus(6, 8)
        expected_area = (rhombus.d1 * rhombus.d2) / 2
        assert rhombus.area() == expected_area

    def test_side_calculation(self) -> None:
        """Test side length calculation."""
        rhombus = Rhombus(6, 8)
        expected_side = math.sqrt((rhombus.d1 / 2) ** 2 + (rhombus.d2 / 2) ** 2)
        assert math.isclose(rhombus.side(), expected_side)


@pytest.mark.abs_shape
class TestTrapezoid:
    def test_initialization_valid(self):
        """Test valid trapezoid initialization."""
        trapezoid = Trapezoid(a=5, b=3, c=4, d=6, h=2)
        assert trapezoid.a == 5
        assert trapezoid.b == 3
        assert trapezoid.c == 4
        assert trapezoid.d == 6
        assert trapezoid.h == 2

    def test_initialization_invalid_base_a(self) -> None:
        """Test initialization with invalid base a."""
        with pytest.raises(ValueError, match="Base 'a' must be a positive number."):
            Trapezoid(a=-1, b=3, c=4, d=6, h=2)

        with pytest.raises(ValueError, match="Base 'a' must be a positive number."):
            Trapezoid(a=0, b=3, c=4, d=6, h=2)

    def test_initialization_invalid_base_b(self) -> None:
        """Test initialization with invalid base b."""
        with pytest.raises(ValueError, match="Base 'b' must be a positive number."):
            Trapezoid(a=5, b=-1, c=4, d=6, h=2)

        with pytest.raises(ValueError, match="Base 'b' must be a positive number."):
            Trapezoid(a=5, b=0, c=4, d=6, h=2)

    def test_initialization_invalid_side_c(self) -> None:
        """Test initialization with invalid side c."""
        with pytest.raises(ValueError, match="Side 'c' must be a positive number."):
            Trapezoid(a=5, b=3, c=-1, d=6, h=2)

    def test_initialization_invalid_side_d(self) -> None:
        """Test initialization with invalid side d."""
        with pytest.raises(ValueError, match="Side 'd' must be a positive number."):
            Trapezoid(a=5, b=3, c=4, d=-1, h=2)

    def test_initialization_invalid_height(self) -> None:
        """Test initialization with invalid height."""
        with pytest.raises(ValueError, match="Height 'h' must be a positive number."):
            Trapezoid(a=5, b=3, c=4, d=6, h=-1)

        with pytest.raises(ValueError, match="Height 'h' must be a positive number."):
            Trapezoid(a=5, b=3, c=4, d=6, h=0)

    def test_perimeter_with_sides(self) -> None:
        """Test perimeter calculation when sides c and d are provided."""
        trapezoid = Trapezoid(a=5, b=3, c=4, d=6)
        assert trapezoid.perimeter() == 18  # 5 + 3 + 4 + 6

    def test_perimeter_invalid(self) -> None:
        """Test perimeter calculation when sides c and d are not provided."""
        trapezoid = Trapezoid(a=5, b=3)
        with pytest.raises(
            ValueError, match="'c' and 'd' must be provided to calculate perimeter."
        ):
            trapezoid.perimeter()

    def test_area(self) -> None:
        """Test area calculation."""
        trapezoid = Trapezoid(a=5, b=3, h=2)
        expected_area = (trapezoid.a + trapezoid.b) * trapezoid.h / 2
        assert trapezoid.area() == expected_area

    def test_area_invalid(self) -> None:
        """Test area calculation when height is not provided."""
        trapezoid = Trapezoid(a=5, b=3)
        with pytest.raises(ValueError, match="'h' must be provided to calculate area."):
            trapezoid.area()


@pytest.mark.abs_shape
class TestCube:
    def test_initialization_valid(self) -> None:
        """Test valid cube initialization."""
        cube = Cube(3)
        assert cube.side == 3

    def test_initialization_invalid_negative(self) -> None:
        """Test initialization with negative side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Cube(-1)

    def test_initialization_invalid_zero(self) -> None:
        """Test initialization with zero side length."""
        with pytest.raises(ValueError, match="Side length must be a positive number."):
            Cube(0)

    def test_surface_area(self) -> None:
        """Test surface area calculation."""
        cube = Cube(3)
        expected_surface_area = 6 * (3**2)
        assert cube.surface_area() == expected_surface_area

    def test_volume(self) -> None:
        """Test volume calculation."""
        cube = Cube(3)
        expected_volume = 3**3
        assert cube.volume() == expected_volume

    def test_surface_area_side(self) -> None:
        """Test surface area of one side calculation."""
        cube = Cube(3)
        expected_surface_area_side = 4 * (3**2)
        assert cube.surface_area_side() == expected_surface_area_side

    def test_face_area(self) -> None:
        """Test face area calculation."""
        cube = Cube(3)
        expected_face_area = 3**2
        assert cube.face_area() == expected_face_area

    def test_diagonal(self) -> None:
        """Test diagonal calculation."""
        cube = Cube(3)
        expected_diagonal = 3 * math.sqrt(3)
        assert math.isclose(cube.diagonal(), expected_diagonal)

    def test_scale_valid(self) -> None:
        """Test scaling with a valid (positive) factor."""
        cube = Cube(5)
        cube.scale(2)
        assert cube.side == 10

    def test_scale_invalid(self) -> None:
        """Test scaling with an invalid (non-positive) factor."""
        cube = Cube(5)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            cube.scale(-1)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            cube.scale(0)

    def test_from_surface_area_valid(self) -> None:
        """Test creating a Cube instance from a valid surface area."""
        surface_area = 6 * (5**2)  # Surface area of a cube with side length 5
        cube = Cube.from_surface_area(surface_area)
        assert math.isclose(cube.side, 5)
        assert Cube(5).side == Cube.from_surface_area(Cube(5).surface_area()).side

    def test_from_surface_area_invalid(self) -> None:
        """Test creating a Cube instance from an invalid (negative) surface area."""
        with pytest.raises(ValueError, match="Surface area must be positive."):
            Cube.from_surface_area(-10)

    def test_from_volume_valid(self) -> None:
        """Test creating a Cube instance from a valid volume."""
        volume = 5**3  # Volume of a cube with side length 5
        cube = Cube.from_volume(volume)
        assert math.isclose(cube.side, 5)
        assert Cube(5).side == Cube.from_volume(Cube(5).volume()).side

    def test_from_volume_invalid(self) -> None:
        """Test creating a Cube instance from an invalid (negative) volume."""
        with pytest.raises(ValueError, match="Volume must be positive."):
            Cube.from_volume(-10)


@pytest.mark.abs_shape
class TestCuboid:
    def test_valid_dimensions(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        assert cuboid.length == 5
        assert cuboid.width == 4
        assert cuboid.height == 3

    def test_invalid_dimensions(self) -> None:
        with pytest.raises(ValueError, match="Length must be a positive number."):
            Cuboid(length=-5, width=4, height=3)

        with pytest.raises(ValueError, match="Width must be a positive number."):
            Cuboid(length=5, width=-4, height=3)

        with pytest.raises(ValueError, match="Height must be a positive number."):
            Cuboid(length=5, width=4, height=-3)

    def test_zero_dimensions(self) -> None:
        with pytest.raises(ValueError, match="Length must be a positive number."):
            Cuboid(length=0, width=4, height=3)
        with pytest.raises(ValueError, match="Width must be a positive number."):
            Cuboid(length=5, width=0, height=3)
        with pytest.raises(ValueError, match="Height must be a positive number."):
            Cuboid(length=5, width=4, height=0)

    def test_surface_area(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        assert cuboid.surface_area() == 94

    def test_surface_area_side(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        assert cuboid.surface_area_side() == 54

    def test_volume(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        assert cuboid.volume() == 60

    def test_diagonal(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        assert cuboid.diagonal() == math.sqrt(5**2 + 4**2 + 3**2)

    def test_scale_valid(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        cuboid.scale(2)
        assert cuboid.length == 10
        assert cuboid.width == 8
        assert cuboid.height == 6

    def test_scale_invalid(self) -> None:
        cuboid = Cuboid(length=5, width=4, height=3)
        with pytest.raises(ValueError, match="Scaling factor must be positive."):
            cuboid.scale(-2)


@pytest.mark.abs_shape
class TestSphere:
    """Test suite for the Sphere class."""

    def test_initialization_valid(self) -> None:
        """Test initializing Sphere with a valid radius."""
        sphere = Sphere(5)
        assert sphere.radius == 5

    def test_initialization_invalid(self) -> None:
        """Test initializing Sphere with an invalid (negative) radius."""
        with pytest.raises(ValueError, match="Radius must be a positive number."):
            Sphere(-5)

    def test_surface_area(self) -> None:
        """Test calculating the surface area of the sphere."""
        sphere = Sphere(5)
        expected_surface_area = 4 * math.pi * (5**2)
        assert math.isclose(sphere.surface_area(), expected_surface_area)

    def test_volume(self) -> None:
        """Test calculating the volume of the sphere."""
        sphere = Sphere(5)
        expected_volume = (4 / 3) * math.pi * (5**3)
        assert math.isclose(sphere.volume(), expected_volume)

    def test_from_volume_valid(self) -> None:
        """Test creating a Sphere instance from a valid volume."""
        volume = (4 / 3) * math.pi * (5**3)  # Volume of sphere with radius 5
        sphere = Sphere.from_volume(volume)
        assert math.isclose(sphere.radius, 5)
        assert Sphere(5).radius == Sphere.from_volume(Sphere(5).volume()).radius

    def test_from_volume_invalid(self) -> None:
        """Test creating a Sphere instance from an invalid (negative) volume."""
        with pytest.raises(ValueError, match="Volume must be a positive number."):
            Sphere.from_volume(-10)

    def test_from_surface_area_valid(self) -> None:
        """Test creating a Sphere instance from valid surface area."""
        surface_area = 4 * math.pi * (5**2)  # Surface area of sphere with radius 5
        sphere = Sphere.from_surface_area(surface_area)
        assert math.isclose(sphere.radius, 5)
        assert (
            Sphere(5).radius
            == Sphere.from_surface_area(Sphere(5).surface_area()).radius
        )

    def test_from_surface_area_invalid(self) -> None:
        """Test creating a Sphere instance from an invalid (negative) surface area."""
        with pytest.raises(ValueError, match="Surface area must be a positive number."):
            Sphere.from_surface_area(-10)


@pytest.mark.abs_shape
class TestHemiSphere:
    """
    Test suite for the HemiSphere class.
    """

    def test_initialization_valid(self) -> None:
        """
        Test initializing HemiSphere with a valid radius.
        """
        hemisphere = HemiSphere(5)
        assert hemisphere.radius == 5

    def test_initialization_invalid(self) -> None:
        """
        Test initializing HemiSphere with an invalid (negative) radius.
        """
        with pytest.raises(ValueError, match="Radius must be a positive number."):
            HemiSphere(-5)

    def test_surface_area(self) -> None:
        """
        Test calculating the surface area of the hemisphere.
        """
        hemisphere = HemiSphere(5)
        expected_surface_area = 3 * math.pi * 5**2
        assert math.isclose(hemisphere.surface_area(), expected_surface_area)

    def test_surface_area_curved(self) -> None:
        """
        Test calculating the curved surface area of the hemisphere.
        """
        hemisphere = HemiSphere(5)
        expected_surface_area_curved = 2 * math.pi * 5**2
        assert math.isclose(
            hemisphere.surface_area_curved(), expected_surface_area_curved
        )

    def test_surface_area_base(self) -> None:
        """
        Test calculating the base surface area of the hemisphere
        """
        hemisphere = HemiSphere(5)
        expected_surface_area_base = math.pi * 5**2
        assert math.isclose(hemisphere.surface_area_base(), expected_surface_area_base)

    def test_volume(self) -> None:
        """
        Test calculating the volume of the hemisphere.
        """
        hemisphere = HemiSphere(5)
        expected_volume = (2 / 3) * math.pi * 5**3
        assert math.isclose(hemisphere.volume(), expected_volume)

    def test_from_volume_valid(self) -> None:
        """
        Test creating a HemiSphere instance from a valid volume.
        """
        volume = (2 / 3) * math.pi * 5**3
        hemisphere = HemiSphere.from_volume(volume)
        assert math.isclose(hemisphere.radius, 5)
        assert (
            HemiSphere(5).radius
            == HemiSphere.from_volume(HemiSphere(5).volume()).radius
        )

    def test_from_volume_invalid(self) -> None:
        """
        Test creating a HemiSphere instance from an invalid (negative) volume.
        """
        with pytest.raises(ValueError, match="Volume must be positive."):
            HemiSphere.from_volume(-10)

    def test_from_surface_area_valid(self) -> None:
        """
        Test creating a HemiSphere instance from a valid surface area.
        """
        surface_area = 3 * math.pi * 5**2
        hemisphere = HemiSphere.from_surface_area(surface_area)
        assert math.isclose(hemisphere.radius, 5)
        assert (
            HemiSphere(5).radius
            == HemiSphere.from_surface_area(HemiSphere(5).surface_area()).radius
        )

    def test_from_surface_area_invalid(self) -> None:
        """
        Test creating a HemiSphere instance from an invalid (negative) surface area.
        """
        with pytest.raises(ValueError, match="Surface area must be positive."):
            HemiSphere.from_surface_area(-10)


@pytest.mark.abs_shape
class TestCylinder:
    """Test suite for the Cylinder class."""

    def test_initialization_valid(self) -> None:
        """Test initializing Cylinder with valid radius and height."""
        cylinder = Cylinder(5, 10)
        assert cylinder.radius == 5
        assert cylinder.height == 10

    def test_initialization_invalid_radius(self) -> None:
        """Test initializing Cylinder with an invalid (negative) radius."""
        with pytest.raises(ValueError, match="Radius must be a positive number."):
            Cylinder(-5, 10)

    def test_initialization_invalid_height(self) -> None:
        """Test initializing Cylinder with an invalid (negative) height."""
        with pytest.raises(ValueError, match="Height must be a positive number."):
            Cylinder(5, -10)

    def test_surface_area(self) -> None:
        """Test calculating the total surface area of the cylinder."""
        cylinder = Cylinder(5, 10)
        expected_surface_area = 2 * math.pi * 5 * (5 + 10)
        assert math.isclose(cylinder.surface_area(), expected_surface_area)

    def test_surface_area_curved(self) -> None:
        """Test calculating the curved surface area of the cylinder."""
        cylinder = Cylinder(5, 10)
        expected_curved_surface_area = 2 * math.pi * 5 * 10
        assert math.isclose(
            cylinder.surface_area_curved(), expected_curved_surface_area
        )

    def test_volume(self) -> None:
        """Test calculating the volume of the cylinder."""
        cylinder = Cylinder(5, 10)
        expected_volume = math.pi * (5**2) * 10
        assert math.isclose(cylinder.volume(), expected_volume)
