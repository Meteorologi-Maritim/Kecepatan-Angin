import streamlit as st
import requests
import time
import pytz
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

# --- Initial Configuration ---
load_dotenv()

# API Keys
API_KEY_WEATHER = os.getenv("OPENWEATHER_API_KEY") or "1b67ed28df7beecb47878263ea8d09a7"
API_KEY_GEOCODE = os.getenv("OPENCAGE_API_KEY") or "3bbfdc22fbe447a78f393559ab330ea8"

# Wind speed threshold (converted from m/s to knots for consistency)
THRESHOLD_MPS = 10.28888  

# Monitored location coordinates (currently set to a location in Bali)
# LATITUDE = -7.869
# LONGITUDE = 115.601
LATITUDE = -8.596
LONGITUDE = 112.260

# Data refresh interval in seconds
REFRESH_INTERVAL_SECONDS = 5

# Timezone for display
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

# --- Helper Functions ---
def mps_to_knots(mps: float) -> float:
    """Converts meters per second (mps) to knots."""
    return mps * 1.94384

def get_location_name(lat: float, lon: float) -> str:
    """
    Retrieves the human-readable location name from coordinates using OpenCage Geocoding API.
    """
    try:
        response = requests.get(
            f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={API_KEY_GEOCODE}"
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        results = response.json()
        if results["results"]:
            return results["results"][0]["formatted"]
        else:
            return "Lokasi tidak ditemukan"
    except requests.exceptions.RequestException as e:
        return f"Error mengambil lokasi: {e}"

def get_wind_speed() -> float | None:
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY_WEATHER}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['wind']['speed']
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil data cuaca: {e}")
        return None

# --- Main Application Logic ---
def main():
    # Convert threshold to knots once at the beginning
    threshold_knots = mps_to_knots(THRESHOLD_MPS)

    # Get location name once at the beginning
    location_name = get_location_name(LATITUDE, LONGITUDE)

    # Streamlit Page Configuration
    st.set_page_config(page_title=f"Monitoring Angin - {location_name}", layout="wide")

    st.markdown("<h1 style='text-align: center; color: #2E86C1;'> MONITORING KECEPATAN ANGIN</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 1.1em;'>📍 Lokasi Saat Ini: <strong>{location_name}</strong> Koordinat: <code>{LATITUDE}, {LONGITUDE}</code></p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 1.1em;'>🚨 Ambang Batas Peringatan: <strong style='color: red;'>{threshold_knots:.2f} knot</strong></p>", unsafe_allow_html=True)

    st.markdown("---")

    # Initialize session state for data storage
    if "timestamps" not in st.session_state:
        st.session_state.timestamps = []
    if "wind_speeds" not in st.session_state:
        st.session_state.wind_speeds = []

    run_monitoring = st.checkbox("▶ **Jalankan Monitoring Data Angin**")

    # Layout using two columns
    col1, col2 = st.columns([1, 1])

    # --- Left Column: Interactive Map ---
    with col1:
        st.markdown("## 🌍 Peta Angin Interaktif")
        components.html(
            f"""
            <iframe
                src="https://embed.windy.com/embed2.html?lat={LATITUDE}&lon={LONGITUDE}&zoom=10&marker=true&markerLat={LATITUDE}&markerLon={LONGITUDE}&overlay=wind"
                style="width:100%; height:450px; border:none;"
                loading="lazy">
            </iframe>
            """,
            height=600,
        )

    # --- Right Column: Dashboard ---
    with col2:
        st.markdown("## 📊 Dashboard Data Angin")
        # Placeholders for dynamic content updates
        placeholder_status = st.empty()
        placeholder_chart = st.empty()
        placeholder_counter = st.empty()

        if run_monitoring:
            while True:
                wind_speed_mps = get_wind_speed()
                current_time = datetime.now(JAKARTA_TZ).strftime("%H:%M:%S")
                st.session_state.timestamps.append(current_time)

                if wind_speed_mps is not None:
                    wind_speed_knots = mps_to_knots(wind_speed_mps)
                    st.session_state.wind_speeds.append(wind_speed_knots)

                    if wind_speed_knots > threshold_knots:
                        placeholder_status.markdown(
                            f"### 🚨 **WASPADA! Kecepatan Angin: {wind_speed_knots:.2f} knot** "
                            f"<span style='color:red;'>({current_time})</span>", unsafe_allow_html=True
                        )
                        # Play a sound for alert
                        st.markdown(
                            """
                            <audio autoplay>
                                <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                            </audio>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        placeholder_status.markdown(
                            f"### ✅ **Kecepatan Angin Saat Ini: {wind_speed_knots:.2f} knot** "
                            f"<span style='color:green;'>({current_time})</span>", unsafe_allow_html=True
                        )
                else:
                    st.session_state.wind_speeds.append(0) # Append 0 or last known value
                    placeholder_status.warning("⚠️ Gagal mengambil data, nilai ditampilkan 0.")

                total_data = len(st.session_state.wind_speeds)
                placeholder_counter.info(f"📈 Total Data Tercatat: **{total_data}**")

                # --- Wind Speed Chart (last 20 data points) ---
                timestamps_plot = st.session_state.timestamps[-20:]
                wind_speeds_plot = st.session_state.wind_speeds[-20:]

                with placeholder_chart.container():
                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(timestamps_plot, wind_speeds_plot, marker='o', color='#2E86C1', label='Kecepatan Angin (knot)')
                    ax.axhline(y=threshold_knots, color='red', linestyle='--', label='Ambang Batas')
                    ax.set_title("Grafik 20 Data Kecepatan Angin Terakhir")
                    ax.set_xlabel("Waktu (WIB)")
                    ax.set_ylabel("Kecepatan (knot)")
                    ax.tick_params(axis='x', rotation=45, labelsize=8)
                    ax.legend()
                    ax.grid(True, linestyle=':', alpha=0.7)
                    plt.tight_layout() # Adjust layout to prevent labels from overlapping

                    # Use st.pyplot with `clear_figure=True` for better performance and memory management
                    st.pyplot(fig, clear_figure=True)

                time.sleep(REFRESH_INTERVAL_SECONDS)
        else:
            st.info("💡 Klik tombol 'Jalankan Monitoring Data Angin' di atas untuk memulai pemantauan.")

if __name__ == "__main__":
    main()