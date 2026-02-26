# KONSTANTA — Nilai yang valid untuk setiap fitur kategorik
# Definisikan di sini agar konsisten antara training dan prediksi
# Kalau mau tambah kota baru, cukup tambah di sini

VALID_CITIES = ["jakarta", "medan", "bandung", "surabaya", "yogyakarta", "binjai"]
VALID_JOB_LEVELS = ["junior", "mid", "senior", "lead", "principal", "fresh graduate"]

# Bobot gaji per kota (relatif terhadap bandung sebagai baseline)
CITY_MULTIPLIER = {
    "jakarta"   : 1.35,    # Jakarta 35% lebih tinggi dari baseline
    "surabaya"  : 1.10,
    "medan"     : 1.20,
    "bandung"   : 0.90,
    "yogyakarta": 1.15,
    "binjai"    : 1.00,   # baseline
}

# Bobot gaji per level jabatan
LEVEL_MULTIPLIER = {
    "junior"   : 0.80,
    "mid"      : 1.00,   # baseline
    "senior"   : 1.40,
    "lead"     : 1.80,
    "principal": 2.20,
    "fresh graduate": 0.60,
}
