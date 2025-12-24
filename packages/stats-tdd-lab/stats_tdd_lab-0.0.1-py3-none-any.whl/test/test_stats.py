"""Classe des tests du module stats.py."""
import io

import pytest
from pytest import approx

from stats.stats import InvalidGrade, Module, compute_stats, load_module_from_file


@pytest.fixture
def sample_module():
    """Génère un module."""
    m = Module()
    m.add_student("Durden", "Tyler", [15, 10, 12])
    m.add_student("Singer", "Marla", [12, 14, 5])
    m.add_student("Paulson", "Bob", [5, 6, 10])
    m.add_student("Face", "Angel", [12, 20, 14])
    return m

@pytest.fixture
def sample_content():
    """Génère un fichier de notes."""
    content = """Durden, Tyler, 15, 10, 12
Singer, Marla, 12, 14, 5
Paulson, Bob, 5, 6, 10
Face, Angel, 12, 20, 14"""
    file_content = io.StringIO(content)
    return file_content

@pytest.fixture
def invalid_sample_content():
    """Génère un fichier de notes erroné."""
    content = """Durden, Tyler, oui, 10, 12
Singer, Marla, 12, 14, 5
Paulson, Bob, 5, 6, 10
Face, Angel, 12, 20, 14"""
    file_content = io.StringIO(content)
    return file_content

def test_n_students(sample_module):
    """Vérifie que le nombre d'étudiants inscrits est correct."""
    assert sample_module.n_students() == 4

def test_is_student_enrolled(sample_module):
    """Vérifie qu'un étudiant est inscrit au module."""
    assert sample_module.is_enrolled("Durden", "Tyler")
    assert not sample_module.is_enrolled("Simpson", "Homer")

def test_overall_grade(sample_module):
    """Vérifie que les moyennes sont correctes."""
    assert sample_module.overall_grade("Durden", "Tyler") == approx(12.33, abs=0.01)
    assert sample_module.overall_grade("Singer", "Marla") == approx(10.33, abs=0.01)
    assert sample_module.overall_grade("Paulson", "Bob") == approx(7.00, abs=0.01)
    assert sample_module.overall_grade("Face", "Angel") == approx(15.33, abs=0.01)

def test_input_output_computation(sample_content):
    """Vérifie que le fichier de sortie est correct."""
    output_file = io.StringIO()
    compute_stats(sample_content, output_file)
    assert output_file.getvalue() == """Durden, Tyler, 12.33
Singer, Marla, 10.33
Paulson, Bob, 7.00
Face, Angel, 15.33
"""

def test_load_module_from_file(sample_content):
    """Vérifie que le fichier d'entrée est bien analysé."""
    module = load_module_from_file(sample_content)
    assert module.n_students() == 4
    assert module.is_enrolled("Durden", "Tyler")
    assert not module.is_enrolled("Simpson", "Homer")
    assert module.get_grades("Durden", "Tyler") == [15, 10, 12]

def test_student_list(sample_module):
    """Vérifie que la liste des étudiants est correcte."""
    students = sample_module.student_list()
    assert len(students) == 4
    assert ("Durden", "Tyler") in students
    assert ("Simpson", "Homer") not in students

def test_raises_exception(invalid_sample_content, sample_content):
    """Vérifie qu'une erreur est levée lorsqu'une note est incorrecte."""
    with pytest.raises(InvalidGrade):
        compute_stats(invalid_sample_content, sample_content)