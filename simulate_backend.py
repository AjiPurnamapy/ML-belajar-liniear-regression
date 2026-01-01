import httpx
import json

ML_API_TEST = "http://127.0.0.1:8000/predict"

def hitung_prediksi_gaji(list_pengalaman):
    payload ={
        "years_experience": list_pengalaman
    }

    try:
        response = httpx.post(ML_API_TEST, json=payload, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            return data["estimated_salary_million"]
        else:
            print(f"API menolak: {response.status_code} - {response.text}")
            return None
        
    except httpx.ConnectError:
        print("GAGAL connect! pastikan server API ML (Uvicorn) sudah nyala")
        return None
    except Exception as e:
        print(f"Error tidak dikenal: {e}")
        return None
    
if __name__ == "__main__":
    user_a = 2.3   # Pengalaman user
    user_b = 3.1
    user_c = 20

    hasil = hitung_prediksi_gaji([user_a, user_b, user_c])

    if hasil:
        print("\n HASIL DARI API ML:")
        print(f"- User A (2.3 thn): Rp {hasil[0]} Juta")
        print(f"- User B (3.1 thn): Rp {hasil[1]} Juta")
        print(f"- User C (20 thn): Rp {hasil[2]} Juta")
        print("\n Data ini siap disimpan ke database postgres!")