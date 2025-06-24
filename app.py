import streamlit as st
import requests
import time
import pytz
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

# Initial Setup
load_dotenv()
st.set_page_config(page_title="Monitoring Kecepatan Angin", layout="wide")

API_KEY_WEATHER = os.getenv("OPENWEATHER_API_KEY") or "1b67ed28df7beecb47878263ea8d09a7"
API_KEY_GEOCODE = os.getenv("OPENCAGE_API_KEY") or "3bbfdc22fbe447a78f393559ab330ea8"
THRESHOLD_MPS = 10.28888
REFRESH_INTERVAL = 5
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

# Helper Functions
def mps_to_knots(mps: float) -> float:
    return mps * 1.94384

def get_location_name(lat: float, lon: float) -> str:
    try:
        res = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={API_KEY_GEOCODE}")
        res.raise_for_status()
        results = res.json()
        return results["results"][0]["formatted"] if results["results"] else "Lokasi tidak ditemukan"
    except Exception as e:
        return f"Error lokasi: {e}"

def get_wind_speed(lat: float, lon: float) -> float | None:
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=metric"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()['wind']['speed']
    except Exception as e:
        st.error(f"❌ Gagal ambil data cuaca: {e}")
        return None

def get_coordinates_from_ip() -> tuple[float, float]:
    # Lokasi fallback Jakarta Selatan
    fallback_lat, fallback_lon = -6.1556659, 106.8416636
    try:
        res = requests.get("https://ipapi.co/json/")
        res.raise_for_status()
        data = res.json()
        lat = data.get("latitude", fallback_lat)
        lon = data.get("longitude", fallback_lon)
        return lat, lon
    except:
        return fallback_lat, fallback_lon


# Main App
def main():
    # CSS ringan & bersih
    st.markdown("""
        <style>
        .main-title {
            text-align: center;
            color: #2E86C1;
            font-size: 2.3rem;
            font-weight: 600;
            margin-top: 0.5rem;
            margin-bottom: 0.3rem;
        }
        .subtext {
            text-align: center;
            font-size: 1rem;
            margin-top: -0.3rem;
            margin-bottom: 0.8rem;
        }
        iframe {
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title
    st.markdown("<div class='main-title'>Monitoring Kecepatan Angin</div>", unsafe_allow_html=True)

    # Ambil lokasi berdasarkan IP saat pertama kali load aplikasi
    if "latitude" not in st.session_state or "longitude" not in st.session_state:
        ip_lat, ip_lon = get_coordinates_from_ip()
        st.session_state.latitude = ip_lat
        st.session_state.longitude = ip_lon

    # Input manual lokasi di atas
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.session_state.latitude = st.number_input("Latitude", value=st.session_state.latitude, format="%.6f")
    with col2:
        st.session_state.longitude = st.number_input("Longitude", value=st.session_state.longitude, format="%.6f")
    with col3:
        if st.button("📍 Lokasi Otomatis"):
            ip_lat, ip_lon = get_coordinates_from_ip()
            st.session_state.latitude = ip_lat
            st.session_state.longitude = ip_lon
            st.success(f"Lokasi otomatis: {ip_lat:.6f}, {ip_lon:.6f}")

    # Data lokasi & threshold
    lat = st.session_state.latitude
    lon = st.session_state.longitude
    location_name = get_location_name(lat, lon)
    threshold_knots = mps_to_knots(THRESHOLD_MPS)

    st.markdown(f"""
        <div class="subtext">
            📌 <strong>{location_name}</strong><br>
            Koordinat: <code>{lat:.6f}, {lon:.6f}</code> | 🚨 Ambang Batas: <span style='color:red'>{threshold_knots:.2f} knot</span>
        </div>
        <hr style='margin-top:10px; margin-bottom:10px'>
    """, unsafe_allow_html=True)

    # Inisialisasi grafik
    st.session_state.setdefault("timestamps", [])
    st.session_state.setdefault("wind_speeds", [])

    run_monitoring = st.checkbox("▶ Jalankan Monitoring Angin", value=False)

    colL, colR = st.columns(2)

    # Peta dengan marker
    with colL:
        st.markdown("### 🌍 Peta Angin")
        components.html(
            f"""
            <iframe
                src="https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=10&marker=true&markerLat={lat}&markerLon={lon}&overlay=wind"
                style="width:100%; height:450px; border:none;">
            </iframe>
            """,
            height=500,
        )

    # Dashboard statistik
    with colR:
        st.markdown("### 📊 Statistik Kecepatan Angin")
        placeholder_status = st.empty()
        placeholder_chart = st.empty()
        placeholder_counter = st.empty()

        if run_monitoring:
            while True:
                wind_mps = get_wind_speed(lat, lon)
                now = datetime.now(JAKARTA_TZ).strftime("%H:%M:%S")
                st.session_state.timestamps.append(now)

                if wind_mps is not None:
                    wind_knots = mps_to_knots(wind_mps)
                    st.session_state.wind_speeds.append(wind_knots)

                    if wind_knots > threshold_knots:
                        placeholder_status.markdown(
                            f"### 🚨 <span style='color:red;'>WASPADA!</span> Angin: <strong>{wind_knots:.2f} knot</strong> ({now})",
                            unsafe_allow_html=True,
                        )
                        st.markdown("""
                            <audio autoplay>
                                <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                            </audio>
                        """, unsafe_allow_html=True)
                    else:
                        placeholder_status.markdown(
                            f"### ✅ Kecepatan Angin: <strong>{wind_knots:.2f} knot</strong> ({now})",
                            unsafe_allow_html=True,
                        )
                else:
                    st.session_state.wind_speeds.append(0)
                    placeholder_status.warning("⚠️ Gagal mengambil data. Nilai dianggap 0.")

                placeholder_counter.info(f"📈 Total Data: **{len(st.session_state.wind_speeds)}**")

                # Plot grafik
                time_data = st.session_state.timestamps[-20:]
                wind_data = st.session_state.wind_speeds[-20:]

                with placeholder_chart.container():
                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(time_data, wind_data, marker='o', color='#1F77B4')
                    ax.axhline(y=threshold_knots, color='red', linestyle='--', label='Ambang Batas')
                    ax.set_title("Grafik Kecepatan Angin (20 Data Terakhir)")
                    ax.set_xlabel("Waktu (WIB)")
                    ax.set_ylabel("Kecepatan (knot)")
                    ax.tick_params(axis='x', rotation=45)
                    ax.grid(True, linestyle=':', alpha=0.6)
                    ax.legend()
                    plt.tight_layout()
                    st.pyplot(fig, clear_figure=True)

                time.sleep(REFRESH_INTERVAL)
        else:
            st.info("💡 Aktifkan monitoring dengan mencentang checkbox di atas.")

if __name__ == "__main__":
    main()
