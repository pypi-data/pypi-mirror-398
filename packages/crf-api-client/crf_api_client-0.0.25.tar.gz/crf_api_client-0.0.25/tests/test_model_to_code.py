# ruff: noqa: S101
from typing import List, Optional

from pydantic import BaseModel

from crf_api_client.warehouse import model_to_code


class Skill(BaseModel):
    """
    A skill required for a job position.

    This model represents a specific skill with its name and optional description.
    """

    name: str
    description: Optional[str] = None


class JobDescription(BaseModel):
    """
    A job description posting.

    This model represents a job posting with its title, company, and required skills.
    """

    title: str
    company: str
    location: Optional[str] = None
    required_skills: List[Skill]
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None


def test_model_to_code_with_nested_models():
    # Generate the code
    generated_code = model_to_code(JobDescription)

    # Check that both docstrings are present
    assert "A skill required for a job position" in generated_code
    assert "This model represents a specific skill" in generated_code
    assert "A job description posting" in generated_code
    assert "This model represents a job posting" in generated_code

    # Check that the model structure is correct
    assert "class Skill(BaseModel):" in generated_code
    assert "class JobDescription(BaseModel):" in generated_code
    assert "required_skills: List[Skill]" in generated_code


def test_model_to_code_with_renamed_class():
    # Test with a custom class name
    generated_code = model_to_code(JobDescription, class_name="CustomJobDescription")

    assert "class CustomJobDescription(BaseModel):" in generated_code
    assert "A job description posting" in generated_code

    # Original nested model name should remain unchanged
    assert "class Skill(BaseModel):" in generated_code
    assert "A skill required for a job position" in generated_code
