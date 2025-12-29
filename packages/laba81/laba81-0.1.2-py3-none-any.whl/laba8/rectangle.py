class Rectangle:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if value <= 0:
            raise ValueError("Ширина должна быть больше 0")
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value <= 0:
            raise ValueError("Высота должна быть больше 0")
        self._height = value

    @property
    def area(self):
        return self._width * self._height

    @property
    def perimeter(self):
        return 2 * (self._width + self._height)

    @property
    def is_square(self):
        return self._width == self._height

    def scale(self, factor: float):
        if factor <= 0:
            raise ValueError("Множитель должен быть больше 0")
        self._width *= factor
        self._height *= factor

    def __str__(self):
        shape = "квадрат" if self.is_square else "прямоугольник"
        return f"{shape}: {self._width}x{self._height}, площадь={self.area}"
