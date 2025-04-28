import os
import re
import geopandas as gpd
import pandas as pd
import numpy as np
import streamlit as st

# Dictionary lokasi folder dan alokasi ODP per kecamatan
kecamatan_info = {
    "lowokwaru":     {"path": os.path.join("utils", "data", "Lowokwaru"),      "total_odp": 329},
    "blimbing":      {"path": os.path.join("utils", "data", "Blimbing"),       "total_odp": 42},
    "klojen":        {"path": os.path.join("utils", "data", "Klojen"),         "total_odp": 40},
    "kedungkandang": {"path": os.path.join("utils", "data", "Kedungkandang"),  "total_odp": 101},
    "sukun":         {"path": os.path.join("utils", "data", "Sukun"),          "total_odp": 5}
}

@st.cache_data(ttl=600)
def process_kecamatan_data(odp_capacity: int = 16) -> dict:
    """
    Baca semua GeoJSON di subfolder utils/data/<kecamatan>,
    hitung Homepass, alokasi ODP, SAM, SOM, kategori, dan 
    kembalikan dict {kecamatan: DataFrame}.
    """
    results = {}

    for kecamatan, info in kecamatan_info.items():
        folder_path = info["path"]
        total_odp   = info["total_odp"]

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder data tidak ditemukan di: {folder_path}")

        # List semua file .geojson
        geojson_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".geojson")]
        data = []

        for file in geojson_files:
            file_path = os.path.join(folder_path, file)
            gdf = gpd.read_file(file_path)

            # Parsing nama kelurahan dari nama file
            if kecamatan == "lowokwaru":
                match = re.search(r'kelurahan\s+(.+)\.geojson', file, re.IGNORECASE)
                kel = match.group(1) if match else file.replace(".geojson", "")
            else:
                prefix = f"Homepass Kecamatan {kecamatan.capitalize()} Kelurahan "
                kel = file.replace(prefix, "").replace(".geojson", "")

            kel = kel.strip().title()
            homepass_count = len(gdf)
            data.append({"kelurahan": kel, "homepass": homepass_count})

        # Bangun DataFrame dan hitung alokasi
        df = pd.DataFrame(data)
        total_homepass = df["homepass"].sum()
        df["odp_float"] = df["homepass"] / total_homepass * total_odp
        df["odp_floor"] = np.floor(df["odp_float"]).astype(int)
        df["sisa"] = df["odp_float"] - df["odp_floor"]
        sisa_odp = total_odp - df["odp_floor"].sum()

        df = df.sort_values("sisa", ascending=False)
        df.iloc[:sisa_odp, df.columns.get_loc("odp_floor")] += 1

        df["SAM"] = df["odp_floor"] * odp_capacity
        df["SOM"] = (df["SAM"] * 0.3).round(0).astype(int)
        df = df.rename(columns={"odp_floor": "ODP"})

        df = df.sort_values("SOM", ascending=False).reset_index(drop=True)
        df["ranking"] = df["SOM"].rank(ascending=False).astype(int)
        mean_som = df["SOM"].mean()
        df["kategori_potensi"] = df["SOM"].apply(
            lambda x: "🔥 High Potential" if x >= mean_som else "❄️ Low Potential"
        )

        # Simpan hasil untuk kecamatan ini
        results[kecamatan] = df[
            ["ranking", "kelurahan", "homepass", "ODP", "SAM", "SOM", "kategori_potensi"]
        ]

    return results
