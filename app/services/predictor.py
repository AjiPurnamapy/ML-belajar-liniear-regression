import logging
from app.utils.converters import convert_ym_to_years

logger = logging.getLogger(__name__)


def predict_salaries_v2(model, years_list: list[float], city_list: list[str], level_list: list[str]) -> dict:
    """
    Fungsi prediksi V2: terima list pengalaman kerja, kota, dan level jabatan,
    kembalikan prediksi gaji.

    Validasi panjang array sudah dilakukan di Pydantic schema (SalaryInputV2),
    jadi di sini kita fokus pada logika ML saja.

    Args:
        model      : Pipeline scikit-learn (ColumnTransformer + LinearRegression)
        years_list : list pengalaman dalam format Y.M (contoh: [2.6, 3.0])
        city_list  : list kota (contoh: ["jakarta", "bandung"])
        level_list : list level jabatan (contoh: ["junior", "senior"])

    Returns:
        dict berisi input asli, hasil konversi, dan hasil prediksi
    """

    # Konversi format Y.M → desimal murni
    # Validasi format sudah dilakukan oleh Pydantic, jadi ini murni konversi
    converted = [convert_ym_to_years(ym) for ym in years_list]

    logger.info(f"Konversi Y.M V2 selesai, batch size: {len(years_list)}")

    # Gabungkan menjadi format 2D: [[tahun, kota, level], ...]
    # Pipeline V2 menggunakan ColumnTransformer yang menerima list of list
    input_records = [
        [tahun, kota, level]
        for tahun, kota, level in zip(converted, city_list, level_list)
    ]

    raw_predictions = model.predict(input_records)

    # Ubah numpy array → list of float biasa (agar bisa di-serialize ke JSON)
    result = [round(float(x), 2) for x in raw_predictions]

    logger.info(f"Prediksi V2 selesai: {len(result)} data diproses")

    return {
        "input_years": years_list,
        "city": city_list,
        "job_level": level_list,
        "converted_years_decimal": converted,
        "estimated_salary_million": result,
        "message": f"Berhasil memprediksi {len(result)} data sekaligus!"
    }
