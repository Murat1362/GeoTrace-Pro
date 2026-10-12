import json
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
    "Bu səhifə öz məkanını könüllü paylaşmaq istəyən "
    "istifadəçilər üçündür."
)

st.info(
    "Davam etdikdə GPS koordinatların GeoTrace Pro sisteminə "
    "göndəriləcək və qorunan idarəetmə panelində görünə biləcək. "
    "Yalnız razısansa davam et."
)

display_name = st.text_input(
    "Ad və ya istifadəçi adı",
    max_chars=80,
    placeholder="Məsələn, Murad"
)

consent = st.checkbox(
    "Koordinatlarımın paylaşılmasına razılıq verirəm."
)

if consent and display_name.strip():

    try:
        supabase_url = st.secrets["SUPABASE_URL"].rstrip("/")
        supabase_key = st.secrets["SUPABASE_KEY"]

        if not supabase_url.startswith("https://"):
            raise ValueError("Supabase URL HTTPS formatında olmalıdır.")

        if not supabase_key.startswith("sb_publishable_"):
            raise ValueError(
                "SUPABASE_KEY sahəsində Publishable key olmalıdır."
            )

    except Exception as exc:
        st.error(
            "Supabase parametrləri tapılmadı və ya düzgün deyil. "
            "Streamlit Settings → Secrets bölməsini yoxla."
        )
        st.stop()

    components.html(
        f"""
        <div style="
            background:#142238;
            color:#e6edf7;
            padding:20px;
            border-radius:12px;
            font-family:Arial,sans-serif;
        ">
            <h3>📍 Məkan paylaşımı</h3>

            <p>
                GPS paylaşımını başlatmaq üçün düyməyə bas.
                Brauzer məkan icazəsi istəyəcək.
                Paylaşımı istənilən vaxt dayandıra bilərsən.
            </p>

            <button id="start" style="
                background:#2563eb;
                color:white;
                border:0;
                padding:12px 18px;
                border-radius:8px;
                cursor:pointer;
                margin-right:8px;
            ">Paylaşımı başlat</button>

            <button id="stop" style="
                background:#b91c1c;
                color:white;
                border:0;
                padding:12px 18px;
                border-radius:8px;
                cursor:pointer;
            " disabled>Paylaşımı dayandır</button>

            <p id="status" role="status" aria-live="polite">
                Paylaşım hələ başlamayıb.
            </p>

            <div id="coords"></div>

            <script>
            const SUPABASE_URL = {json.dumps(supabase_url)};
            const SUPABASE_KEY = {json.dumps(supabase_key)};
            const DISPLAY_NAME = {json.dumps(display_name.strip())};

            const startButton = document.getElementById("start");
            const stopButton = document.getElementById("stop");
            const statusBox = document.getElementById("status");
            const coordsBox = document.getElementById("coords");

            let watchId = null;
            let sessionId = null;
            let lastSent = 0;
            let sharing = false;

            function setStatus(message) {{
                statusBox.textContent = message;
            }}

            async function sendLocation(position) {{
                if (!sharing) return;

                const now = Date.now();

                // Eyni sessiyada çox tez-tez məlumat göndərmə.
                if (now - lastSent < 10000) return;

                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                const accuracy = position.coords.accuracy;

                const payload = {{
                    display_name: DISPLAY_NAME,
                    latitude: latitude,
                    longitude: longitude,
                    is_active: true,
                    session_id: sessionId
                }};

                try {{
                    const response = await fetch(
                        SUPABASE_URL + "/rest/v1/location_shares",
                        {{
                            method: "POST",
                            headers: {{
                                "apikey": SUPABASE_KEY,
                                "Authorization": "Bearer " + SUPABASE_KEY,
                                "Content-Type": "application/json",
                                "Prefer": "return=minimal"
                            }},
                            body: JSON.stringify(payload)
                        }}
                    );

                    if (!response.ok) {{
                        throw new Error("HTTP " + response.status);
                    }}

                    lastSent = now;

                    setStatus(
                        "Məkan paylaşılır. Son yenilənmə: " +
                        new Date().toLocaleTimeString()
                    );

                    coordsBox.textContent =
                        "Enlik: " + latitude.toFixed(6) +
                        " | Uzunluq: " + longitude.toFixed(6) +
                        " | Dəqiqlik: təxminən " +
                        Math.round(accuracy) + " metr";

                }} catch (error) {{
                    setStatus(
                        "Məkan göndərilmədi. Bağlantını və Supabase "
                        + "icazələrini yoxlamaq lazımdır."
                    );
                    console.error(error);
                }}
            }}

            startButton.addEventListener("click", function() {{
                if (sharing) return;

                if (!navigator.geolocation) {{
                    setStatus("Brauzer GPS funksiyasını dəstəkləmir.");
                    return;
                }}

                sharing = true;
                sessionId = crypto.randomUUID();
                lastSent = 0;

                startButton.disabled = true;
                stopButton.disabled = false;

                setStatus("GPS icazəsi gözlənilir...");

                watchId = navigator.geolocation.watchPosition(
                    sendLocation,
                    function(error) {{
                        setStatus(
                            error.code === 1
                            ? "Məkan icazəsi verilmədi."
                            : "GPS məlumatını almaq mümkün olmadı."
                        );

                        if (error.code === 1) {{
                            sharing = false;

                            if (watchId !== null) {{
                                navigator.geolocation.clearWatch(watchId);
                            }}

                            startButton.disabled = false;
                            stopButton.disabled = true;
                        }}
                    }},
                    {{
                        enableHighAccuracy: true,
                        timeout: 20000,
                        maximumAge: 5000
                    }}
                );
            }});

            stopButton.addEventListener("click", function() {{
                sharing = false;

                if (watchId !== null) {{
                    navigator.geolocation.clearWatch(watchId);
                    watchId = null;
                }}

                startButton.disabled = false;
                stopButton.disabled = true;

                setStatus(
                    "Məkan paylaşımı dayandırıldı. "
                    + "Yeni GPS koordinatları göndərilməyəcək."
                );
            }});
            </script>
        </div>
        """,
        height=360
    )

elif consent:
    st.warning("Davam etmək üçün ad və ya istifadəçi adı daxil et.")

else:
    st.info(
        "Məkan paylaşımına razılıq verməsən, koordinatların göndərilməyəcək."
    )

st.caption(
    "Məkan məlumatlarını yalnız könüllü paylaş. "
    "Paylaşımı dayandırmaq yeni koordinatların göndərilməsini dayandırır. "
    "Əvvəl göndərilmiş məlumatlar ayrıca silinməlidir."
)