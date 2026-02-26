import numpy as np
import joblib
import os
import sys

# Windows CMD Unicode patch
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.constants import VALID_CITIES, VALID_JOB_LEVELS, CITY_MULTIPLIER, LEVEL_MULTIPLIER

def generate_training_data(n_sample: int = 200) -> tuple:
    """
    Generate data training sintetik.

    Formula gaji:
        gaji = (2.0 + years × 0.9) × city_multiplier × level_multiplier × (1 + noise)

    Karena ini hubungan MULTIPLIKATIF, kita gunakan log transform pada target
    agar cocok dengan LinearRegression yang bersifat ADITIF:
        log(gaji) = log(base) + log(city_mult) + log(level_mult)
    """
    np.random.seed(42)

    rows = []
    targets = []

    for city in VALID_CITIES:
        for level in VALID_JOB_LEVELS:

            exp_range = {
                "fresh graduate": (0.0, 1.0),
                "junior": (0.5, 2.0),
                "mid"   : (2.0, 5.0),
                "senior": (5.0, 9.0),
                "lead"  : (8.0, 12.0),
                "principal": (12.0, 25.0)
            }[level]

            for _ in range(8):
                years = round(np.random.uniform(*exp_range), 1)

                base_salary = 2.0 + (years * 0.9)
                salary = base_salary * CITY_MULTIPLIER[city] * LEVEL_MULTIPLIER[level]

                noise = np.random.uniform(-0.10, 0.10)
                salary = salary * (1 + noise)
                salary = round(max(salary, 0.5), 2)

                rows.append([years, city, level])
                targets.append(salary)

    # Tambahan sampel random untuk variasi
    for _ in range(40):
        years = round(np.random.uniform(0.5, 12.0), 1)
        city = np.random.choice(VALID_CITIES)
        level = np.random.choice(VALID_JOB_LEVELS)

        base_salary = 2.0 + (years * 0.9)
        salary = base_salary * CITY_MULTIPLIER[city] * LEVEL_MULTIPLIER[level]
        noise = np.random.uniform(-0.15, 0.15)
        salary = round(max(salary * (1 + noise), 0.5), 2)

        rows.append([years, city, level])
        targets.append(salary)

    return np.array(rows, dtype=object), np.array(targets, dtype=float)

def build_pipeline() -> TransformedTargetRegressor:
    """
    Buat pipeline preprocessing + model dengan log transform pada target.

    Menggunakan TransformedTargetRegressor dari sklearn yang secara otomatis:
    - np.log() pada y saat fit  → LinearRegression belajar di log-space
    - np.exp() pada y saat predict → hasil dikembalikan ke skala asli

    Ini menghindari masalah pickle karena semua class berasal dari sklearn.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "city_encoder",
                OneHotEncoder(
                    categories=[VALID_CITIES],
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                [1]
            ),
            (
                "level_encoder",
                OneHotEncoder(
                    categories=[VALID_JOB_LEVELS],
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                [2]
            ),
        ],
        remainder="passthrough"
    )

    inner_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", LinearRegression())
    ])

    # TransformedTargetRegressor: sklearn built-in log/exp wrapper
    # func=np.log → transform y sebelum fit
    # inverse_func=np.exp → transform balik prediksi
    model = TransformedTargetRegressor(
        regressor=inner_pipeline,
        func=np.log,
        inverse_func=np.exp
    )

    return model


def main():
    print("=" * 55)
    print("  TRAINING MODEL V2 — MULTI FITUR (LOG TRANSFORM)")
    print("  Fitur: Pengalaman + Kota + Level Jabatan")
    print("=" * 55)
    
    # Generate data
    print("\n🔄 Generating data training...")
    X, y = generate_training_data(n_sample=200)

    print(f"✅ Data siap: {len(X)} sampel")
    print(f"   Kota     : {VALID_CITIES}")
    print(f"   Level    : {VALID_JOB_LEVELS}")
    print(f"   Rentang gaji: {y.min():.1f} - {y.max():.1f} juta")

    # Build dan training
    print("\n🔄 Memulai training (log-transformed via TransformedTargetRegressor)...")
    model = build_pipeline()
    model.fit(X, y)
    print("✅ Training selesai!")

    # Evaluasi
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)

    print("\n📊 Evaluasi Model:")
    print(f"   MAE (rata-rata error): {mae:.3f} juta = Rp {mae*1_000_000:,.0f}")
    print(f"   R² Score            : {r2:.4f} ({r2*100:.1f}% akurasi)")

    # Tes prediksi dengan perbandingan ekspektasi
    print("\n🧪 Tes Prediksi vs Ekspektasi:")
    test_cases = [
        [3.0, "jakarta",    "mid"],
        [3.0, "bandung",    "mid"],
        [3.0, "jakarta",    "senior"],
        [7.0, "jakarta",    "senior"],
        [1.0, "yogyakarta", "junior"],
        [2.5, "bandung",    "mid"],       # Kasus Sari
        [0.5, "jakarta",    "fresh graduate"],
    ]

    print(f"   {'Pengalaman':<10} {'Kota':<12} {'Level':<15} {'Prediksi':<14} {'Ekspektasi'}")
    print(f"   {'-'*65}")
    for case in test_cases:
        prediksi = model.predict([case])[0]
        base = 2.0 + (case[0] * 0.9)
        ekspektasi = base * CITY_MULTIPLIER[case[1]] * LEVEL_MULTIPLIER[case[2]]
        print(f"   {case[0]:<10} {case[1]:<12} {case[2]:<15} Rp {prediksi:>5.2f}       Rp {ekspektasi:>5.2f}")

    # Simpan model
    os.makedirs("ml", exist_ok=True)
    output_path = "ml/gaji_model_v2.pkl"
    joblib.dump(model, output_path)

    print(f"\n💾 Model disimpan ke '{output_path}'")
    print("   Jalankan server: python -m uvicorn app.main:app --reload")
    print("=" * 55)

if __name__ == "__main__":
    main()