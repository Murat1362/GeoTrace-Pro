import streamlit as st
import folium
import requests
import ipaddress
import phonenumbers
import hmac

from datetime import datetime, timezone, timedelta
from streamlit_folium import st_folium


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="GeoTrace Pro",
    page_icon="🌐",
    layout="wide"
)


# =====================================================
# DESIGN
# =====================================================

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


# =====================================================
# HEADER
# =====================================================

st.title("🌐 GeoTrace Pro")

st.caption(
    "IP Intelligence • GPS Geolocation • Phone Validation"
)

st.info(
    "Təhsil və məlumat analizi layihəsi. "
    "GPS məlumatları yalnız istifadəçinin könüllü razılığı "
    "ilə paylaşılmalıdır."
)


# =====================================================
# IP ANALYSIS
# =====================================================

def analyze_ip(ip_text):
    """IP formatını yoxlayır və public IP məlumatını əldə edir."""

    try:
        ip_obj = ipaddress.ip_address(ip_text.strip())

    except ValueError:
        return {
            "error": "Daxil etdiyin IP ünvanının formatı düzgün deyil."
        }

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
            headers={
                "User-Agent": "GeoTracePro-Educational/1.0"
            }
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
            "error": (
                "Sorğu vaxt aşımına düşdü. "
                "Bir az sonra yenidən yoxla."
            )
        }

    except requests.RequestException:
        return {
            "error": (
                "IP məlumat xidmətinə qoşulmaq mümkün olmadı. "
                "İnternet bağlantını yoxla."
            )
        }

    except ValueError:
        return {
            "error": "Xidmətdən oxuna bilən məlumat alınmadı."
        }


# =====================================================
# IP MAP
# =====================================================

def show_ip_map(data):
    """IP geolokasiya koordinatlarını xəritədə göstərir."""

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        st.warning(
            "Bu IP üçün xəritədə göstərilə bilən koordinat yoxdur."
        )
        return

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if not (
            -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            st.warning(
                "Xidmət etibarlı koordinatlar qaytarmadı."
            )
            return

        map_object = folium.Map(
            location=[latitude, longitude],
            zoom_start=8,
            tiles="OpenStreetMap"
        )

        folium.Marker(
            [latitude, longitude],
            tooltip="IP geolokasiya nəticəsi",
            popup="Təxmini IP mövqeyi",
            icon=folium.Icon(
                color="blue",
                icon="info-sign"
            )
        ).add_to(map_object)

        st_folium(
            map_object,
            width=None,
            height=420,
            key="ip_location_map"
        )

        st.caption(
            "IP geolokasiyası təxminidir. "
            "Bu, cihazın dəqiq GPS mövqeyi deyil."
        )

    except (TypeError, ValueError):
        st.warning(
            "Koordinatları xəritədə göstərmək mümkün olmadı."
        )


# =====================================================
# SUPABASE ADMIN PANEL
# =====================================================

def render_admin_panel():
    """Könüllü GPS paylaşımlarını administrator üçün göstərir."""

    st.subheader("🔐 Məkan idarəetmə paneli")

    st.write(
        "Bu panel könüllü GPS paylaşımı edən istifadəçilərin "
        "son koordinatlarını göstərmək üçündür."
    )

    # Konfiqurasiyanı yoxla.
    # Bu funksiya parametrlər yoxdursa belə bütün tətbiqi dayandırmır.
    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
        supabase_url = st.secrets["SUPABASE_URL"].rstrip("/")
        supabase_secret = st.secrets["SUPABASE_SECRET_KEY"]

    except Exception:
        st.error(
            "İdarəetmə panelinin parametrləri tapılmadı. "
            "Streamlit Settings → Secrets bölməsində "
            "ADMIN_PASSWORD, SUPABASE_URL və "
            "SUPABASE_SECRET_KEY parametrlərini yoxla."
        )
        return

    if not admin_password or not supabase_secret or not supabase_url:
        st.error("İdarəetmə panelinin parametrləri boşdur.")
        return

    # Parolla giriş vəziyyəti
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # -------------------------------------------------
    # LOGIN
    # -------------------------------------------------

    if not st.session_state.admin_authenticated:

        st.warning(
            "Məkan məlumatlarını görmək üçün administrator "
            "parolunu daxil et."
        )

        entered_password = st.text_input(
            "Administrator parolu",
            type="password",
            key="admin_password_input"
        )

        if st.button(
            "🔓 Daxil ol",
            key="admin_login"
        ):

            if hmac.compare_digest(
                entered_password,
                str(admin_password)
            ):
                st.session_state.admin_authenticated = True
                st.rerun()

            else:
                st.error("Parol yanlışdır.")

        return

    # -------------------------------------------------
    # AUTHENTICATED ADMIN
    # -------------------------------------------------

    col1, col2 = st.columns([4, 1])

    with col1:
        st.success("İdarəetmə panelinə giriş uğurludur.")

    with col2:
        if st.button(
            "🚪 Çıxış",
            key="admin_logout"
        ):
            st.session_state.admin_authenticated = False
            st.rerun()

    st.divider()

    st.caption(
        "Məlumatlar yalnız administratorun sorğusu zamanı "
        "Supabase-dən oxunur."
    )

    if st.button(
        "🔄 Məlumatları yenilə",
        key="refresh_locations"
    ):
        st.rerun()

    # -------------------------------------------------
    # FETCH LOCATION DATA
    # -------------------------------------------------

    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/location_shares",
            params={
                "select": (
                    "id,display_name,latitude,longitude,"
                    "is_active,created_at,updated_at,session_id"
                ),
                "order": "created_at.desc",
                "limit": "500"
            },
            headers={
                "apikey": supabase_secret,
                "Authorization": f"Bearer {supabase_secret}"
            },
            timeout=15
        )

        if response.status_code != 200:

            st.error(
                "Supabase məlumatları oxuya bilmədi. "
                f"HTTP status: {response.status_code}."
            )

            st.caption(
                "Supabase API açarının düzgünlüyünü, "
                "cədvəl icazələrini və server cavabını yoxla. "
                "Açarları heç kimə göndərmə."
            )

            return

        rows = response.json()

        if not isinstance(rows, list):
            st.error(
                "Supabase-dən gözlənilməyən məlumat formatı gəldi."
            )
            return

        # -------------------------------------------------
        # SELECT LATEST ROW PER SESSION
        # -------------------------------------------------

        latest_by_session = {}

        for row in rows:

            session_id = row.get("session_id")

            if not session_id:
                continue

            # Sorğu created_at üzrə azalan sıralanıb.
            # Beləliklə, hər sessiyanın ilk sətri ən yenidir.
            if session_id not in latest_by_session:
                latest_by_session[session_id] = row

        # -------------------------------------------------
        # FILTER RECENT COORDINATES
        # -------------------------------------------------

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=120)

        active_rows = []

        for row in latest_by_session.values():

            if row.get("is_active") is not True:
                continue

            timestamp = row.get("created_at")

            if not timestamp:
                continue

            try:
                created = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )

                if created.tzinfo is None:
                    created = created.replace(
                        tzinfo=timezone.utc
                    )

                # Son iki dəqiqədə yenilənən koordinatlar
                if created >= cutoff:
                    latitude = float(row["latitude"])
                    longitude = float(row["longitude"])

                    if (
                        -90 <= latitude <= 90
                        and -180 <= longitude <= 180
                    ):
                        active_rows.append(row)

            except (ValueError, TypeError, KeyError):
                continue

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "🟢 Son 2 dəqiqədə yenilənən sessiyalar",
                len(active_rows)
            )

        with col2:
            st.metric(
                "📦 Oxunan sətirlərin sayı",
                len(rows)
            )

        st.divider()

        # -------------------------------------------------
        # LOCATION MAP
        # -------------------------------------------------

        if active_rows:

            all_latitudes = [
                float(row["latitude"])
                for row in active_rows
            ]

            all_longitudes = [
                float(row["longitude"])
                for row in active_rows
            ]

            center_lat = sum(all_latitudes) / len(all_latitudes)
            center_lon = sum(all_longitudes) / len(all_longitudes)

            map_object = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=11,
                tiles="OpenStreetMap"
            )

            for row in active_rows:

                latitude = float(row["latitude"])
                longitude = float(row["longitude"])

                name = row.get("display_name") or "İstifadəçi"
                created_at = row.get("created_at") or "Məlumat yoxdur"

                popup_html = f"""
                <div style="width:230px">
                    <b>Ad:</b> {name}<br>
                    <b>Enlik:</b> {latitude:.6f}<br>
                    <b>Uzunluq:</b> {longitude:.6f}<br>
                    <b>Son qeyd:</b> {created_at}
                </div>
                """

                folium.Marker(
                    location=[latitude, longitude],
                    tooltip=name,
                    popup=folium.Popup(
                        popup_html,
                        max_width=300
                    ),
                    icon=folium.Icon(
                        color="green",
                        icon="map-marker"
                    )
                ).add_to(map_object)

            st.subheader("🗺️ Paylaşılan məkanlar")

            st_folium(
                map_object,
                width=None,
                height=500,
                key="shared_locations_admin_map"
            )

            # -------------------------------------------------
            # COORDINATES TABLE
            # -------------------------------------------------

            st.subheader("📍 Koordinatlar")

            table_data = []

            for row in active_rows:

                table_data.append({
                    "Ad": row.get("display_name", "İstifadəçi"),
                    "Enlik": row.get("latitude"),
                    "Uzunluq": row.get("longitude"),
                    "Son qeyd": row.get("created_at")
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                "Son 2 dəqiqədə yenilənmiş GPS paylaşımı tapılmadı."
            )

            st.write(
                "Məkan paylaşımı səhifəsinin işlədiyini və "
                "koordinatların Supabase-ə göndərildiyini yoxla."
            )

        st.caption(
            "Qeyd: iki dəqiqəlik müddət son koordinatın "
            "təzəliyini yoxlayır. Bu, istifadəçinin paylaşımı "
            "həqiqətən dayandırdığını sübut etmir."
        )

    except requests.RequestException:
        st.error(
            "Supabase-ə qoşulmaq mümkün olmadı. "
            "İnternet bağlantısını və layihə URL-sini yoxla."
        )

    except ValueError:
        st.error(
            "Supabase cavabını oxumaq mümkün olmadı."
        )


# =====================================================
# TABS
# =====================================================

tab_gps, tab_ip, tab_phone, tab_admin = st.tabs([
    "📍 GPS və xəritə",
    "🌐 IP analizi",
    "📱 Telefon analizi",
    "🔐 İdarəetmə paneli"
])


# =====================================================
# GPS TAB
# =====================================================

with tab_gps:

    st.subheader("📍 GPS və xəritə")

    st.write(
        "İstifadəçilər öz məkanlarını yalnız razılıq verdikdə "
        "ayrıca məkan paylaşımı səhifəsindən göndərə bilərlər."
    )

    st.info(
        "GPS paylaşımı səhifəsi: location_app.py"
    )

    if st.button(
        "🗺️ Nümunə xəritəni göstər",
        key="demo_map"
    ):

        demo_map = folium.Map(
            location=[40.4093, 49.8671],
            zoom_start=11,
            tiles="OpenStreetMap"
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
            "Bu, nümunə nöqtədir. "
            "İstifadəçinin real GPS koordinatları deyil."
        )


# =====================================================
# IP TAB
# =====================================================

with tab_ip:

    st.subheader("🌐 IP Intelligence")

    st.write(
        "Public IP ünvanını daxil et. Sistem IP məlumat "
        "xidmətindən əlavə məlumat əldə etməyə çalışacaq."
    )

    ip_input = st.text_input(
        "IP ünvanı",
        placeholder="Məsələn: 8.8.8.8",
        key="ip_input"
    )

    if "ip_analysis_result" not in st.session_state:
        st.session_state.ip_analysis_result = None

    if st.button(
        "🔎 IP-ni analiz et",
        key="analyze_ip"
    ):

        if not ip_input.strip():

            st.session_state.ip_analysis_result = {
                "error": "Əvvəlcə IP ünvanı daxil et."
            }

        else:

            with st.spinner("IP məlumatları yoxlanılır..."):

                st.session_state.ip_analysis_result = analyze_ip(
                    ip_input
                )

    result = st.session_state.ip_analysis_result

    if result:

        if "error" in result:

            st.error(result["error"])

        else:

            data = result["data"]

            country = (
                data.get("country_name")
                or "Məlumat yoxdur"
            )

            city = (
                data.get("city")
                or "Məlumat yoxdur"
            )

            region = (
                data.get("region")
                or "Məlumat yoxdur"
            )

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

                st.metric(
                    "🌐 IP ünvanı",
                    data.get("ip", ip_input)
                )

                st.metric(
                    "🏢 Provayder / təşkilat",
                    organization
                )

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


# =====================================================
# PHONE TAB
# =====================================================

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

    if st.button(
        "🔎 Nömrəni yoxla",
        key="analyze_phone"
    ):

        if not phone_input.strip():

            st.warning(
                "Əvvəlcə telefon nömrəsi daxil et."
            )

        else:

            try:

                parsed = phonenumbers.parse(
                    phone_input,
                    None
                )

                possible = phonenumbers.is_possible_number(
                    parsed
                )

                valid = phonenumbers.is_valid_number(
                    parsed
                )

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

                st.write(
                    "**Beynəlxalq format:**",
                    formatted
                )

                st.write(
                    "**Ölkə kodu / region:**",
                    country
                )

                st.caption(
                    "Bu yoxlama nömrənin sahibini, canlı yerini "
                    "və ya hazırda aktiv olub-olmadığını müəyyən etmir."
                )

            except phonenumbers.NumberParseException:

                st.error(
                    "Nömrə oxuna bilmədi. Beynəlxalq formatda, "
                    "məsələn +994501234567 kimi daxil et."
                )


# =====================================================
# ADMIN TAB
# =====================================================

with tab_admin:
    render_admin_panel()


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "GeoTrace Pro | Educational Cybersecurity Project | "
    "Nəticələr xarici məlumat xidmətlərinin "
    "əlçatanlığından asılıdır."
)