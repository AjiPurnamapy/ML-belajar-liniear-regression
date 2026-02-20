import numpy as np     
from sklearn.linear_model import LinearRegression  
import joblib   

def main():
    X_train = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]).reshape(-1, 1)   
    y_train = np.array([2.3, 3.4, 4.1, 5.8, 6.1, 7.9, 8.2, 9.9, 10, 11.2, 12.5, 13.5])

    print("DATA SIAP. MEMULAI TRAINING....")

    model = LinearRegression() 
    model.fit(X_train, y_train)

    print("TRAINING SELESAI")

    sample_input = np.array([[20]])
    prediksi = model.predict(sample_input)

    print(f"TEST PREDIKSI: {sample_input[0]} TAHUN PENGALAMAN -> GAJI {prediksi[0]:.2f} JUTA")
    print(f"INSIGHT MODEL: SETIAP TAMBAH 1 TAHUN GAJI NAIK SEKITAR {model.coef_[0]:.2f} JUTA")

    filename = "gaji_model.pkl"
    joblib.dump(model, filename)
    print(f"MODEL DISIMPAN KE FILE '{filename}'. SIAP DIPAKAI DI FASTAPI!")

if __name__ == "__main__":
    main()