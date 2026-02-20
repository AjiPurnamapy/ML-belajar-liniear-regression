from pydantic import BaseModel, Field, field_validator
from typing import List

class SalaryInput(BaseModel):
    years_experience: List[float] = Field(
        ...,
        examples= [[1.0, 2.5, 3.0, 4.5]],
        description="Format Tahun.Bulan (Y.M). Contoh: 2.6 = 2 tahun 6 bulan"
    )

    @field_validator("years_experience")
    @classmethod
    def validate_experience(cls, v):
        if not v:
            raise ValueError("List tidak boleh kosong")
        for val in v:
            if val < 0:
                raise ValueError(f"Pengalaman tidak boleh negatif: {val}")
            months = round((val - int(val)) * 10)
            if months >= 12:
                raise ValueError(f"Format bulan tidak valid pada nilai: {val}")
            return v

class SalaryOutput(BaseModel):
    input_years: List[float]
    converted_years_decimal: List[float]
    estimated_salary_million: List[float]
    message: str