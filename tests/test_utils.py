"""
tests/test_utils.py — Unit test untuk utility functions dan Pydantic schemas

Cara jalankan:
    pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.converters import convert_ym_to_years
from app.schemas.models import SalaryInputV2
from pydantic import ValidationError


class TestConvertYMToYears:
    """Kumpulan test untuk fungsi convert_ym_to_years."""

    def test_konversi_normal(self):
        """Test konversi angka yang valid."""
        assert convert_ym_to_years(2.6)  == 2.5    # 2 thn 6 bln
        assert convert_ym_to_years(3.0)  == 3.0    # 3 thn 0 bln
        assert convert_ym_to_years(1.3)  == 1.25   # 1 thn 3 bln

    def test_nol_bulan(self):
        """Tahun bulat (tanpa bulan) harus tetap sama."""
        assert convert_ym_to_years(5.0) == 5.0
        assert convert_ym_to_years(0.0) == 0.0

    def test_bulan_maksimal(self):
        """11 bulan adalah nilai bulan tertinggi yang valid."""
        result = convert_ym_to_years(2.11)
        assert result == pytest.approx(2 + 11/12, rel=1e-3)

    def test_format_bulan_tidak_valid(self):
        """Bulan >= 12 harus raise ValueError."""
        with pytest.raises(ValueError, match="Format tidak valid"):
            convert_ym_to_years(2.12)   # bulan ke-12

        with pytest.raises(ValueError, match="Format tidak valid"):
            convert_ym_to_years(1.15)   # bulan ke-15

    def test_nilai_negatif(self):
        """Nilai negatif harus raise ValueError."""
        with pytest.raises(ValueError, match="tidak boleh negatif"):
            convert_ym_to_years(-1.0)


class TestSalaryInputV2Validator:
    """Test untuk Pydantic validators di SalaryInputV2."""

    def test_input_valid(self):
        data = SalaryInputV2(
            years_experience=[1.0, 2.6],
            city=["jakarta", "bandung"],
            job_level=["junior", "senior"]
        )
        assert len(data.years_experience) == 2
        assert data.city == ["jakarta", "bandung"]
        assert data.job_level == ["junior", "senior"]

    def test_input_kosong_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[],
                city=[],
                job_level=[]
            )

    def test_input_negatif_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[-1.0],
                city=["jakarta"],
                job_level=["junior"]
            )

    def test_format_bulan_invalid_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[2.12],
                city=["jakarta"],
                job_level=["junior"]
            )

    def test_kota_tidak_valid_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[2.0],
                city=["wakanda"],
                job_level=["junior"]
            )

    def test_level_tidak_valid_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[2.0],
                city=["jakarta"],
                job_level=["ceo"]
            )

    def test_panjang_list_tidak_sama_ditolak(self):
        """Semua list harus panjang sama — ini validasi @model_validator."""
        with pytest.raises(ValidationError, match="Panjang semua list harus sama"):
            SalaryInputV2(
                years_experience=[1.0, 2.0],
                city=["jakarta"],          # ← hanya 1
                job_level=["junior", "mid"]
            )

    def test_normalisasi_case(self):
        """Input huruf besar harus dinormalisasi ke lowercase."""
        data = SalaryInputV2(
            years_experience=[3.0],
            city=["JAKARTA"],
            job_level=["Senior"]
        )
        assert data.city == ["jakarta"]
        assert data.job_level == ["senior"]

    def test_maks_pengalaman_ditolak(self):
        """Pengalaman > 50 tahun harus ditolak."""
        with pytest.raises(ValidationError):
            SalaryInputV2(
                years_experience=[51.0],
                city=["jakarta"],
                job_level=["principal"]
            )