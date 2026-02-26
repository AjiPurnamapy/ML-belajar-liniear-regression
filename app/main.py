import joblib
import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.schemas.models import SalaryInputV2, SalaryOutputV2, HealthOutput, HistoryOutput
from app.services.predictor import predict_salaries_v2
from app.services.history import save_prediction, get_all_history, get_history_by_id
from app.db.database import get_db, engine, Base


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ml_models = {}
APP_VERSION = "2.0.0"
MODEL_VERSION = "salary-linear-v2"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🔄 Menginisialisasi database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tabel database siap!")

    # Load Model ML
    logger.info("🔄 Loading model ML V2...")
    try:
        ml_models["gaji_model_v2"] = joblib.load("ml/gaji_model_v2.pkl")
        logger.info("✅ Model V2 berhasil di-load ke memori! Siap melayani request.")
    except FileNotFoundError:
        logger.error("❌ File 'ml/gaji_model_v2.pkl' tidak ditemukan. Jalankan train_model_v2.py dulu!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        sys.exit(1)
    yield 

    # Shutdown
    logger.info("🛑 Aplikasi berhenti. Membersihkan resource...")
    ml_models.clear()


app = FastAPI(
    title="API Prediksi Gaji V2",
    description=(
        "API untuk memprediksi estimasi gaji berdasarkan pengalaman kerja, kota, dan level jabatan. "
        "Menggunakan model pipeline (OneHotEncoder + LinearRegression) yang dilatih dengan data sintetik. "
        "Format input pengalaman: Y.M (Tahun.Bulan), contoh: 2.6 = 2 tahun 6 bulan."
    ),
    version=APP_VERSION,
    lifespan=lifespan
)

@app.get("/", tags=["Info"])
def read_root():
    """
    Endpoint sederhana untuk konfirmasi server hidup.
    Tidak butuh model ML, tidak butuh auth — hanya salam pembuka.
    """
    return {
        "message": "Selamat datang di API Prediksi Gaji V2",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthOutput, tags=["Info"])
def health_check():
    """
    Endpoint untuk monitoring — cek apakah server dan model dalam kondisi baik.
    """
    model_loaded = "gaji_model_v2" in ml_models and ml_models["gaji_model_v2"] is not None
    
    return {
        "status": "ok" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "version": APP_VERSION,
    }

@app.post("/predict", response_model=SalaryOutputV2, tags=["Prediksi"])
async def predict_salary(data: SalaryInputV2, db: AsyncSession = Depends(get_db)):
    """
    Endpoint utama: prediksi gaji berdasarkan pengalaman kerja, kota, dan level jabatan.
    Mendukung batch processing (banyak orang sekaligus).
    """
    
    if "gaji_model_v2" not in ml_models or ml_models["gaji_model_v2"] is None:
        logger.critical("Model V2 hilang dari memori runtime!")
        raise HTTPException(
            status_code=500,
            detail="Model machine learning tidak aktif"
        )
    try:
        result = await run_in_threadpool(
            predict_salaries_v2,
            ml_models["gaji_model_v2"],
            data.years_experience,
            data.city,
            data.job_level
        )

        try:
            await save_prediction(
                session=db,
                prediction_result=result,
                model_version=MODEL_VERSION,
            )
        except Exception as db_err:
            logger.error(f"Gagal menyimpan histori ke DB: {db_err}")
            
        return result

    except ValueError as e:
        logger.warning(f"Input tidak valid: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error saat prediksi: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memproses data"
        )

@app.get("/history", response_model=list[HistoryOutput], tags=["History"])
async def get_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    record = await get_all_history(db, limit=limit)
    return record

@app.get("/history/{history_id}", response_model=HistoryOutput, tags=["History"])
async def get_history_detail(history_id: int, db: AsyncSession = Depends(get_db)):
    record = await get_history_by_id(db, history_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"History dengan ID {history_id} tidak ditemukan!"
        )
    return record