import streamlit as st
import folium
import requests
import ipaddress
import phonenumbers

from streamlit_folium import st_folium


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="GeoTrace Pro",
    page_icon="🌐",
    layout="wide"
)


# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #07111f, #101c30);
    color: #e6edf7;
}

h1, h2, h3 {
    color: #60a5fa;
}

div[data-testid="stMetric"] {
    background: #142238;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263a56;
}

.stButton > button {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

.stButton > button:hover {
    background: #1d4ed8;
    color: white;
}

div[data-testid="stTabs"] button {
    color: #bfdbfe;
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------

st.title("🌐 GeoTrace Pro")
st.caption("IP Intelligence • Geolocation • Phone Validation")

st.info(
    "Təhsil və məlumat analizi layihəsi. "
    "Nəticələr istifadə olunan mənbələrin dəqiqliyindən asılıdır."
)


# ---------------- FUNCTIONS ----------------

def analyze_ip(ip_text):
    """IP formatını yoxlayır və public IP üçün məlumat axtarır."""

    try:
        ip_obj = ipaddress.ip_address(ip_text.strip())
    except ValueError:
        return {"error": "Daxil etdiyin IP ünvanının formatı düzgün deyil."}

    if not ip_obj.is_global:
        return {
            "error": (
                "Bu, internetdə geolokasiya üçün uyğun public IP deyil. "
                "Private və xüsusi təyinatlı IP-lərdən real şəhər "
                "və koordinat müəyyən etmək mümkün deyil."
            )
        }

    try:
        response = requests.get(
            f"https://ipapi.co/{ip_obj}/json/",
            timeout=12,
            headers={"User-Agent": "GeoTracePro-Educational/1.0"}
        )

        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            return {
                "error": data.get(
                    "reason",
                    "IP məlumatı xidmət tərəfindən qaytarılmadı."
                )
            }

        return {"data": data}

    except requests.Timeout:
        return {
            "error": "Sorğu vaxt aşımına düşdü. Bir az sonra yenidən yoxla."
        }

    except requests.RequestException:
        return {
            "error": (
                "IP məlumat xidmətinə qoşulmaq mümkün olmadı. "
                "İnternet bağlantını yoxla."
            )
        }

    except ValueError:
        return {"error": "Xidmətdən oxuna bilən məlumat alınmadı."}


def show_ip_map(data):
    """Koordinatlar varsa xəritədə göstərir."""

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        st.warning("Bu IP üçün xəritədə göstərilə bilən koordinat yoxdur.")
        return

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            st.warning("Xidmət etibarlı koordinatlar qaytarmadı.")
            return

        map_object = folium.Map(
            location=[latitude, longitude],
            zoom_start=8,
            tiles="CartoDB dark_matter"
        )

        folium.Marker(
            [latitude, longitude],
            tooltip="IP geolokasiya nəticəsi",
            popup="Təxmini IP mövqeyi",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(map_object)

        st_folium(
            map_object,
            width=None,
            height=420,
            key="ip_location_map"
        )

        st.caption(
            "Xəritə IP ünvanına əsaslanan təxmini mövqeyi göstərir; "
            "cihazın dəqiq GPS yeri deyil."
        )

    except (TypeError, ValueError):
        st.warning("Koordinatları xəritədə göstərmək mümkün olmadı.")


# ---------------- TABS ----------------

tab_gps, tab_ip, tab_phone = st.tabs([
    "📍 GPS və xəritə",
    "🌐 IP analizi",
    "📱 Telefon analizi"
])


# ---------------- GPS TAB ----------------

with tab_gps:
    st.subheader("📍 GPS və xəritə")

    st.write(
        "Bu bölmə hazırda nümayiş üçündür. "
        "Real cihaz koordinatlarını almaq üçün ayrıca brauzer "
        "geolokasiya funksiyası əlavə edilməlidir."
    )

    if st.button("🗺️ Nümunə xəritəni göstər", key="demo_map"):
        demo_map = folium.Map(
            location=[40.4093, 49.8671],
            zoom_start=11,
            tiles="CartoDB dark_matter"
        )

        folium.Marker(
            [40.4093, 49.8671],
            popup="Nümunə nöqtə — Bakı",
            tooltip="Demo"
        ).add_to(demo_map)

        st_folium(
            demo_map,
            width=None,
            height=420,
            key="demo_location_map"
        )

        st.caption(
            "Bu, nümunə nöqtədir. İstifadəçinin real GPS koordinatları deyil."
        )


# ---------------- IP TAB ----------------


# ---------------- IP TAB ----------------

with tab_ip:
    st.subheader("🌐 IP Intelligence")
    st.write(
        "Public IP ünvanını daxil et. Sistem IP məlumat xidmətindən "
        "əlavə məlumat əldə etməyə çalışacaq."
    )

    ip_input = st.text_input(
        "IP ünvanı",
        placeholder="Məsələn: 8.8.8.8",
        key="ip_input"
    )

    if "ip_analysis_result" not in st.session_state:
        st.session_state.ip_analysis_result = None

    if st.button("🔎 IP-ni analiz et", key="analyze_ip"):
        if not ip_input.strip():
            st.session_state.ip_analysis_result = {
                "error": "Əvvəlcə IP ünvanı daxil et."
            }
        else:
            with st.spinner("IP məlumatları yoxlanılır..."):
                st.session_state.ip_analysis_result = analyze_ip(ip_input)

    result = st.session_state.ip_analysis_result

    if result:
        if "error" in result:
            st.error(result["error"])
        else:
            data = result["data"]

            country = data.get("country_name") or "Məlumat yoxdur"
            city = data.get("city") or "Məlumat yoxdur"
            region = data.get("region") or "Məlumat yoxdur"
            organization = (
                data.get("org")
                or data.get("asn")
                or "Məlumat yoxdur"
            )

            st.success("IP məlumatı əldə edildi.")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "🌍 Ölkə",
                    country,
                    data.get("country_code", "")
                )
                st.metric("🏙️ Şəhər", city)
                st.metric("📍 Region", region)

            with col2:
                st.metric("🌐 IP ünvanı", data.get("ip", ip_input))
                st.metric("🏢 Provayder / təşkilat", organization)
                st.metric(
                    "🕒 Saat qurşağı",
                    data.get("timezone") or "Məlumat yoxdur"
                )

            st.divider()
            st.subheader("🗺️ Təxmini IP mövqeyi")
            show_ip_map(data)

            st.caption(
                "IP geolokasiyası təxminidir və cihazın dəqiq GPS "
                "mövqeyini göstərmir."
            )



# ---------------- PHONE TAB ----------------

with tab_phone:
    st.subheader("📱 Telefon nömrəsinin yoxlanılması")

    st.write(
        "Telefon nömrəsinin beynəlxalq formatını və "
        "mümkün nömrə diapazonuna uyğunluğunu yoxla."
    )

    phone_input = st.text_input(
        "Telefon nömrəsi",
        placeholder="Məsələn: +994501234567",
        key="phone_input"
    )

    if st.button("🔎 Nömrəni yoxla", key="analyze_phone"):

        if not phone_input.strip():
            st.warning("Əvvəlcə telefon nömrəsi daxil et.")

        else:
            try:
                parsed = phonenumbers.parse(phone_input, None)

                possible = phonenumbers.is_possible_number(parsed)
                valid = phonenumbers.is_valid_number(parsed)

                country = (
                    phonenumbers.region_code_for_number(parsed)
                    or "Məlumat yoxdur"
                )

                formatted = phonenumbers.format_number(
                    parsed,
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "📋 Format",
                        "Uyğundur" if possible else "Uyğun deyil"
                    )

                with col2:
                    st.metric(
                        "✅ Nömrə diapazonu",
                        "Uyğundur" if valid else "Təsdiqlənmədi"
                    )

                st.write("**Beynəlxalq format:**", formatted)
                st.write("**Ölkə kodu / region:**", country)

                st.caption(
                    "Bu yoxlama nömrənin sahibini, canlı yerini və ya "
                    "hazırda aktiv olub-olmadığını müəyyən etmir."
                )

            except phonenumbers.NumberParseException:
                st.error(
                    "Nömrə oxuna bilmədi. Beynəlxalq formatda, "
                    "məsələn +994501234567 kimi daxil et."
                )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "GeoTrace Pro | Educational Cybersecurity Project | "
    "Nəticələr xarici məlumat xidmətlərinin əlçatanlığından asılıdır."
)