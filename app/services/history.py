import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.db.models import PredictionHistory

async def save_prediction(session: AsyncSession, prediction_result: dict, model_version: str) -> PredictionHistory:
    """
    Simpan Hasil Prediksi ke Database.
    Menggunakan .get() untuk field opsional agar kompatibel
    dengan berbagai versi output predictor.
    """
    record = PredictionHistory(
        input_years=prediction_result["input_years"],
        converted_years=prediction_result["converted_years_decimal"],
        city=prediction_result.get("city"),
        job_level=prediction_result.get("job_level"),
        predicted_salaries=prediction_result["estimated_salary_million"],
        data_count=len(prediction_result["input_years"]),
        model_version=model_version,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return record

async def get_all_history(
    session: AsyncSession,
    page: int = 1,
    size: int = 10,
) -> dict:
    """
    Ambil riwayat prediksi dengan paginasi.

    Args:
        session : Sesi database async
        page    : Nomor halaman (mulai dari 1)
        size    : Jumlah item per halaman

    Returns:
        dict berisi metadata paginasi dan list items
    """
    # Hitung total data
    count_query = select(func.count(PredictionHistory.id))
    total_result = await session.execute(count_query)
    total_data = total_result.scalar_one()

    total_pages = max(1, math.ceil(total_data / size))

    # Ambil data sesuai halaman
    offset = (page - 1) * size
    data_query = (
        select(PredictionHistory)
        .order_by(desc(PredictionHistory.created_at))
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(data_query)
    items = result.scalars().all()

    return {
        "total_data": total_data,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": size,
        "items": items,
    }

async def get_history_by_id(session: AsyncSession, history_id: int) -> PredictionHistory | None:
    result = await session.execute(
        select(PredictionHistory).where(PredictionHistory.id == history_id)
    )
    return result.scalar_one_or_none()