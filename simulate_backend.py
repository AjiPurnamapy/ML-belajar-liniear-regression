import httpx
import json
import sys

# Windows CMD Unicode patch
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
PREDICT_URL = f"{BASE_URL}/predict"
HEALTH_URL = f"{BASE_URL}/health"
REGISTER_URL = f"{BASE_URL}/register"
TOKEN_URL = f"{BASE_URL}/token"

# Kredensial demo untuk simulasi
DEMO_USERNAME = "demo_hr"
DEMO_PASSWORD = "demo123456"

def cek_health_server() -> bool:
    """
    Cek apakah server hidup dan model ML sudah dimuat.
    Return True kalau server OK, False kalau ada masalah.
    """
    print("\n Mengecek Status server ...")
    try:
        response = httpx.get(HEALTH_URL, timeout=5.0)
        data = response.json()

        print(f"   Status      : {data['status']}")
        print(f"   Model loaded: {data['model_loaded']}")
        print(f"   Version     : {data['version']}")

        return data["status"] == "ok"
    
    except httpx.ConnectError:
        print("❌ Server tidak bisa dihubungi!")
        print("   Pastikan sudah menjalankan: uvicorn app.main:app --reload")
        return False

def register_user() -> bool:
    """
    Registrasi user demo. Kalau sudah ada (409), anggap sukses.
    """
    print("\n🔐 Registrasi user demo...")
    try:
        response = httpx.post(
            REGISTER_URL,
            json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
            timeout=5.0,
        )
        if response.status_code == 201:
            print(f"   ✅ User '{DEMO_USERNAME}' berhasil didaftarkan!")
            return True
        elif response.status_code == 409:
            print(f"   ℹ️  User '{DEMO_USERNAME}' sudah terdaftar, lanjut login.")
            return True
        else:
            print(f"   ❌ Registrasi gagal: {response.status_code} - {response.text}")
            return False
    except httpx.ConnectError:
        print("   ❌ Server tidak bisa dihubungi!")
        return False

def login_user() -> str | None:
    """
    Login dan dapatkan JWT token.
    Return token string atau None kalau gagal.
    """
    print("\n🔑 Login untuk mendapatkan token...")
    try:
        response = httpx.post(
            TOKEN_URL,
            data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
            timeout=5.0,
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"   ✅ Token diterima! (panjang: {len(token)} karakter)")
            return token
        else:
            print(f"   ❌ Login gagal: {response.status_code} - {response.text}")
            return None
    except httpx.ConnectError:
        print("   ❌ Server tidak bisa dihubungi!")
        return None

def hitung_prediksi_gaji(
    list_pengalaman: list[float],
    kota_list: list[str],
    level_list: list[str],
    token: str,
) -> list[float] | None:
    payload = {
        "years_experience": list_pengalaman,
        "city": kota_list,
        "job_level": level_list,
    }
    headers = {"Authorization": f"Bearer {token}"}

    print(f"\n📤 Mengirim request ke {PREDICT_URL}")
    print(f"   Payload: {json.dumps(payload)}")

    try:
        response = httpx.post(PREDICT_URL, json=payload, headers=headers, timeout=10.0)
        print(f"   Status HTTP : {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print(f"   Message     : {data['message']}")
            print("\n📥 Detail hasil:")
            print(f"   {'Input (Y.M)':<15} {'Konversi (thn)':<18} {'Prediksi Gaji'}")
            print(f"   {'-'*50}")

            for input_ym, converted, salary in zip(
                data["input_years"],
                data["converted_years_decimal"],
                data["estimated_salary_million"],
            ):
                print(f"   {input_ym:<15} {converted:<18} Rp {salary:.2f} juta")
            return data["estimated_salary_million"]
        
        elif response.status_code == 401:
            print("❌ Token tidak valid atau sudah kadaluwarsa!")
            return None
        elif response.status_code == 422:
            error_detail = response.json().get("detail", "Unknown error")
            print(f"❌ Validasi gagal (422): {error_detail}")
            return None
        elif response.status_code == 429:
            print("⚠️  Rate limit! Terlalu banyak request. Coba lagi nanti.")
            return None
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
        
    except httpx.ConnectError:
        print("GAGAL connect! pastikan server API ML (Uvicorn) sudah nyala")
        return None
    except httpx.TimeoutException:
        print("Request Timeout! Server terlalu lama merespons.")
        return None
    except Exception as e:
        print(f"Error tidak dikenal: {e}")
        return None

def demo_validasi_error(token: str):
    """
    Demonstrasi bagaimana API menangani input yang tidak valid.
    """
    print("\n" + "=" * 55)
    print("  DEMO: VALIDASI ERROR HANDLING")
    print("=" * 55)

    headers = {"Authorization": f"Bearer {token}"}
    kasus_error = [
        {
            "deskripsi": "Format bulan tidak valid (2.13 → bulan ke-13)",
            "input": [2.13]
        },
        {
            "deskripsi": "Nilai negatif",
            "input": [-1.0]
        },
        {
            "deskripsi": "List kosong",
            "input": []
        },
    ]
    for kasus in kasus_error:
        print(f"\n🧪 Test: {kasus['deskripsi']}")
        print(f"   Input: {kasus['input']}")
        try:
            response = httpx.post(
                PREDICT_URL,
                json={"years_experience": kasus["input"]},
                headers=headers,
                timeout=5.0
            )
            print(f"   HTTP {response.status_code}: {response.json().get('detail', response.text)}")
        except Exception as e:
            print(f"   Error: {e}")

def demo_akses_tanpa_token():
    """
    Demonstrasi bahwa endpoint dilindungi — akses tanpa token ditolak.
    """
    print("\n" + "=" * 55)
    print("  DEMO: AKSES TANPA TOKEN (Harus Ditolak)")
    print("=" * 55)

    print("\n🧪 Test: POST /predict tanpa Authorization header")
    try:
        response = httpx.post(
            PREDICT_URL,
            json={"years_experience": [3.0], "city": ["jakarta"], "job_level": ["mid"]},
            timeout=5.0,
        )
        print(f"   HTTP {response.status_code}: {response.json().get('detail', response.text)}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    print("=" * 55)
    print("  SIMULASI KLIEN API PREDIKSI GAJI (AUTH + RATE LIMIT)")
    print("=" * 55)

    # Step 1: Cek server
    if not cek_health_server():
        exit(1)

    # Step 2: Demo akses tanpa token (harus ditolak)
    demo_akses_tanpa_token()

    # Step 3: Register & Login
    if not register_user():
        exit(1)
    
    token = login_user()
    if not token:
        exit(1)

    # Step 4: Prediksi dengan token
    print("\n" + "=" * 55)
    print("  SKENARIO: BATCH PREDIKSI UNTUK 5 KANDIDAT")
    print("=" * 55)

    kandidat = {
        "Budi": 0.6,       # 0 tahun 6 bulan
        "Sari": 2.5,       # 2 tahun 5 bulan
        "Andi": 4.0,       # 4 tahun tepat
        "Dewi": 7.6,       # 7 tahun 6 bulan
        "Pak Budi": 12.0,  # 12 tahun
    }

    nama_list = list(kandidat.keys())
    pengalaman_list = list(kandidat.values())
    kota_list = ["jakarta", "bandung", "surabaya", "medan", "yogyakarta", "binjai"]
    level_list = ["junior", "mid", "senior", "lead", "principal", "fresh graduate"]
    
    kota_list = kota_list[:len(kandidat)]
    level_list = level_list[:len(kandidat)]

    hasil = hitung_prediksi_gaji(pengalaman_list, kota_list, level_list, token)

    if hasil:
        print("\n💼 Ringkasan untuk HR:")
        print(f"   {'Nama':<15} {'Kota':<14} {'Level':<12} {'Pengalaman':<12} {'Est. Gaji'}")
        print(f"   {'-'*65}")
        for nama, kota, level, pengalaman, gaji in zip(nama_list, kota_list, level_list, pengalaman_list, hasil):
            print(f"   {nama:<15} {kota:<14} {level:<12} {pengalaman:<12} Rp {gaji:.1f} juta")

        print("\n✅ Data siap untuk disimpan ke database PostgreSQL!")

    # Step 5: Demo error handling (dengan token)
    demo_validasi_error(token)

    print("\n✅ Simulasi selesai!")