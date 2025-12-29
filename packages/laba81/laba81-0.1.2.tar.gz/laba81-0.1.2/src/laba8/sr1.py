from src.laba8.rectangle import Rectangle


def demonstrate_rectangle():
    rect = Rectangle(5, 10)
    print(rect)
    print(f"Площадь: {rect.area}")
    print(f"Периметр: {rect.perimeter}")
    print(f"Квадрат? {rect.is_square}")

    rect.width = 8
    print(f"Новая ширина: {rect.width}")
    print(f"Новая площадь: {rect.area}")

    rect.scale(2)
    print(f"После масштабирования 2x: {rect}")

    square = Rectangle(4, 4)
    print(f"\n{square}")
    print(f"Квадрат? {square.is_square}")


demonstrate_rectangle()
