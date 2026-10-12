import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="GeoTrace Pro | Məkan paylaşımı",
    page_icon="📍",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #07111f, #101c30);
    color: #e6edf7;
}

h1, h2, h3 {
    color: #60a5fa;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

.stButton > button {
    width: 100%;
    background: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📍 GeoTrace Pro")
st.subheader("Məkan paylaşımı")

st.write(
    "Bu səhifə öz məkanını könüllü şəkildə paylaşmaq istəyən "
    "istifadəçilər üçündür."
)

st.warning(
    "Məkanını yalnız paylaşmaq istəyirsənsə davam et. "
    "Koordinatların əldə edilməsi üçün brauzerin icazəsi tələb olunur."
)

consent = st.checkbox(
    "Məkanımı bu səhifədə göstərməyə razılıq verirəm."
)

if consent:
    components.html(
        """
        <div style="
            background:#142238;
            color:#e6edf7;
            padding:18px;
            border-radius:12px;
            font-family:Arial;
        ">
            <h3>📍 Məkanını göstər</h3>

            <p>
                Düyməyə basdıqda brauzer məkan icazəsi istəyəcək.
                İcazə vermək istəmirsənsə, sorğunu rədd edə bilərsən.
            </p>

            <button id="locate" style="
                background:#2563eb;
                color:white;
                border:0;
                padding:12px 18px;
                border-radius:8px;
                cursor:pointer;
            ">
                Məkanımı göstər
            </button>

            <p id="status" style="margin-top:16px;">
                Hələ koordinat alınmayıb.
            </p>

            <div id="coords"></div>

            <script>
            const button = document.getElementById("locate");
            const status = document.getElementById("status");
            const coords = document.getElementById("coords");

            button.addEventListener("click", function() {
                if (!navigator.geolocation) {
                    status.textContent =
                        "Bu brauzer geolokasiyanı dəstəkləmir.";
                    return;
                }

                status.textContent =
                    "Brauzerin məkan icazəsi gözlənilir...";

                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const accuracy = position.coords.accuracy;

                        status.textContent =
                            "Koordinatlar uğurla əldə edildi.";

                        coords.innerHTML =
                            "<p>Enlik: " + lat.toFixed(6) + "</p>" +
                            "<p>Uzunluq: " + lon.toFixed(6) + "</p>" +
                            "<p>Təxmini dəqiqlik: " +
                            Math.round(accuracy) + " metr</p>" +
                            '<a target="_blank" rel="noopener" href="' +
                            'https://www.openstreetmap.org/?mlat=' +
                            lat + '&mlon=' + lon +
                            '#map=16/' + lat + '/' + lon +
                            '" style="color:#60a5fa;">' +
                            'Xəritədə aç</a>';
                    },

                    function(error) {
                        const messages = {
                            1: "Məkan icazəsi verilmədi.",
                            2: "Məkan məlumatı əldə edilə bilmədi.",
                            3: "Sorğunun vaxtı bitdi."
                        };

                        status.textContent =
                            messages[error.code] ||
                            "Naməlum xəta baş verdi.";
                    },

                    {
                        enableHighAccuracy: true,
                        timeout: 15000,
                        maximumAge: 0
                    }
                );
            });
            </script>
        </div>
        """,
        height=340
    )
else:
    st.info(
        "Davam etmək üçün məkan paylaşımı barədə razılıq "
        "xanasını öz istəyinlə işarələ."
    )

st.caption(
    "Bu ilkin versiya koordinatları yalnız həmin səhifədə göstərir. "
    "Koordinatları serverə göndərmir və başqa istifadəçilərə ötürmür."
)
