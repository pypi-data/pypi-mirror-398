from .student import Student


def main():
    print("=" * 50)
    print("ДЕМОНСТРАЦИЯ PROPERTY В КЛАССЕ STUDENT")
    print("=" * 50)

    student = Student("Иван Петров")
    print(f"\n1. Создан: {student}")

    print("\n2. Добавляем оценки...")
    student.add_grade(5)
    student.add_grade(4)
    student.add_grade(3)
    print(f"   Оценки: {student.grades}")
    print(f"   Средняя: {student.average_grade}")
    print(f"   Статус: {student.status}")

    print("\n3. Меняем имя студента...")
    student.name = "Иван Сидоров"
    print(f"   Новое имя: {student.name}")

    print("\n4. Устанавливаем новые оценки...")
    student.grades = [5, 5, 4, 5]
    print(f"   Новые оценки: {student.grades}")
    print(f"   Средняя: {student.average_grade:.2f}")
    print(f"   Статус: {student.status}")

    print("\n5. Проверка валидации...")
    try:
        student.name = ""  # Пустое имя
    except ValueError as e:
        print(f"   Ошибка при смене имени: {e}")

    try:
        student.grades = [5, 6, 3]
    except ValueError as e:
        print(f"   Ошибка при установке оценок: {e}")

    print("\n" + "=" * 50)
    print("ИТОГ:")
    print(student)
    print("=" * 50)


if __name__ == "__main__":
    main()
