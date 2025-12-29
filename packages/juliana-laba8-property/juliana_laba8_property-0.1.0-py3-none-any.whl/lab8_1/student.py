class Student:

    def __init__(self, name: str):
        self._name = name
        self._grades = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value.strip():
            raise ValueError("Имя не может быть пустым")
        self._name = value

    @property
    def grades(self) -> list:
        return self._grades.copy()

    @grades.setter
    def grades(self, value: list):
        if not all(isinstance(g, (int, float)) for g in value):
            raise TypeError("Все оценки должны быть числами")
        if not all(0 <= g <= 5 for g in value):
            raise ValueError("Оценки должны быть от 0 до 5")
        self._grades = value

    @property
    def average_grade(self) -> float:
        if not self._grades:
            return 0.0
        return sum(self._grades) / len(self._grades)

    @property
    def status(self) -> str:
        avg = self.average_grade
        if avg >= 4.5:
            return "Отличник"
        elif avg >= 3.5:
            return "Хорошист"
        elif avg >= 2.5:
            return "Троечник"
        else:
            return "Должник"

    def add_grade(self, grade: float):
        if not isinstance(grade, (int, float)):
            raise TypeError("Оценка должна быть числом")
        if not 0 <= grade <= 5:
            raise ValueError("Оценка должна быть от 0 до 5")
        self._grades.append(grade)

    def __str__(self) -> str:
        return f"Студент {self.name}: {len(self._grades)} оценок, средняя {self.average_grade:.2f} ({self.status})"
    