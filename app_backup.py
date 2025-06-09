import streamlit as st
import requests
import time
import pytz
from datetime import datetime
import matplotlib.pyplot as plt

# Konfigurasi
API_KEY = "1b67ed28df7beecb47878263ea8d09a7"
threshold = 2.5  # m/s
lat = -7.9885
lon = 110.3783
interval = 5  # detik

jakarta_tz = pytz.timezone("Asia/Jakarta")

if "timestamps" not in st.session_state:
    st.session_state.timestamps = []
if "wind_speeds" not in st.session_state:
    st.session_state.wind_speeds = []

def get_wind_speed():
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['wind']['speed']
    except Exception as e:
        st.error(f"❌ Gagal mengambil data: {e}")
        return None

st.set_page_config(page_title="Monitoring Kecepatan Angin", layout="centered")
st.title("🌬️ Monitoring Kecepatan Angin")
st.markdown("Lokasi: **Yogyakarta**, Koordinat: `-7.9885, 110.3783`")
st.markdown(f"Ambang batas kecepatan angin: **{threshold} m/s**")
st.markdown("---")


placeholder_status = st.empty()
placeholder_chart = st.empty()
placeholder_counter = st.empty()

run = st.checkbox("▶️ Jalankan monitoring")

if run:
    while True:
        wind_speed = get_wind_speed()
        current_time = datetime.now(jakarta_tz).strftime("%H:%M:%S")
        st.session_state.timestamps.append(current_time)

        if wind_speed is not None:
            st.session_state.wind_speeds.append(wind_speed)
            status_msg = f"📡 {current_time} - Kecepatan angin: **{wind_speed:.2f} m/s**"

            if wind_speed > threshold:
                status_msg += "  🚨 **ALERT: Melebihi ambang batas!**"
                st.markdown(
                    """
                    <audio autoplay>
                        <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                    </audio>
                    """,
                    unsafe_allow_html=True
                )
                placeholder_status.warning(status_msg)
            else:
                placeholder_status.success(status_msg)
        else:
            st.session_state.wind_speeds.append(0)
            placeholder_status.warning("⚠️ Gagal mengambil data, diset ke 0.")

        total_data = len(st.session_state.wind_speeds)
        placeholder_counter.info(f"📊 Total data yang sudah masuk: **{total_data}**")

        timestamps_plot = st.session_state.timestamps[-20:]
        wind_speeds_plot = st.session_state.wind_speeds[-20:]

        with placeholder_chart.container():
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(timestamps_plot, wind_speeds_plot, marker='o', color='blue', label='Kecepatan Angin')
            ax.axhline(y=threshold, color='red', linestyle='--', label='Ambang Batas')
            ax.set_title("Grafik Kecepatan Angin (m/s) - Tampilan Bergerak")
            ax.set_xlabel("Waktu (WIB)")
            ax.set_ylabel("Kecepatan (m/s)")
            ax.tick_params(axis='x', rotation=45)
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

        time.sleep(interval)
else:
    st.info("✅ Klik checkbox di atas untuk memulai monitoring.")
