"""Calcule les moyennes des étudiants du module."""
import sys
from typing import TextIO


class InvalidGrade(Exception):
    """Exception à lever en cas de note invalide."""

    pass

class Module:
    """Classe stockant les informations du module."""

    def __init__(self) -> None :
        """Constructeur de la classe Module."""
        self.grades:dict[tuple[str, str], list[float]] = {}

    def add_student(self, lastname:str, firstname:str, grades:list[float]) -> None :
        """Ajoute un étudiant au module."""
        self.grades[(lastname, firstname)] = grades

    def n_students(self) -> int :
        """Renvoie le nombre d'étudiants."""
        return len(self.grades)
    
    def is_enrolled(self, lastname:str, firstname:str) -> bool :
        """Vérifie si un étudiant suit le module."""
        return (lastname, firstname) in self.grades
    
    def overall_grade(self, lastname:str, firstname:str) -> float :
        """Calcule la moyenne d'un étudiant.""" # noqa: D401
        grades = self.grades[(lastname, firstname)]
        return (grades[0]+grades[1]+grades[2])/3
    
    def student_list(self) -> list[tuple[str, str]]:
        """Renvoie la liste des étudiants."""
        return list(self.grades.keys())
    
    def get_grades(self, lastname:str, firstname:str) -> list[float]:
        """Renvoie les notes d'un étudiant."""
        return self.grades[(lastname, firstname)]

def compute_stats(input_file:TextIO=sys.stdin, output_file:TextIO=sys.stdout) -> None :
    """
    Extrait les infos et calcule les moyennes.
    
    :param input_file: fichier d'entrée.
    :param output_file: fichier de sortie.
    """
    module = load_module_from_file(input_file)
    for student in module.student_list():
        lastname, firstname = student
        grade = module.overall_grade(lastname, firstname)
        print(f"{lastname}, {firstname}, {grade:2.2f}",
        file=output_file)

def load_module_from_file(input_file:TextIO) -> Module:
    """
    Générer un module à partir des infos du fichier.
    
    :param input_file: fichier d'entrée.
    """
    m = Module()
    content = input_file.read().strip()
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        parts = line.split(', ')
        try:
            grade1 = float(parts[2])
            grade2 = float(parts[3])
            grade3 = float(parts[4])
        except ValueError as e:
            print(f"Erreur: Une des notes n'est pas numérique: {parts[2:]}")
            raise(InvalidGrade) from e
        m.add_student(parts[0], parts[1], [grade1, grade2, grade3])
    return m
    
if __name__ == "__main__": # pragma: no cover
    compute_stats()