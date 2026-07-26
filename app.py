import pandas as pd
import requests
import streamlit as st
import google.generativeai as genai

# Konfigurácia stránky
st.set_page_config(page_title="Slovakia Lead Finder", page_icon="🎯", layout="wide")

st.title("🎯 Vyhľadávač firiem bez webu na Slovensku")
st.write("Aplikácia prejde Google Maps, vyfiltruje firmy bez vlastného webu a pomocou AI (Gemini) vygeneruje oslovovací skript.")

# Sidebar pre API Kľúče
with st.sidebar:
    st.header("⚙️ API Nastavenia")
    google_key = st.text_input("Google Places API Key", type="password", help="Kľúč z Google Cloud Console")
    gemini_key = st.text_input("Gemini API Key", type="password", help="Kľúč z Google AI Studio")
    st.info("💡 **Tip:** Pre testovanie zadaj jedno konkrétne mesto (napr. Žilina, Nitra) a kategóriu (napr. reštaurácia, stolárstvo).")

# Vstupné polia
col1, col2 = st.columns(2)
with col1:
    city = st.text_input("📍 Mesto / Región", value="Žilina")
with col2:
    business_type = st.text_input("🔧 Typ firmy", value="autoservis")

# Funkcia pre hľadanie v Google Maps
def get_businesses(location, query, api_key):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': f"{query} {location} Slovensko",
        'key': api_key
    }
    
    response = requests.get(url, params=params).json()
    results = response.get('results', [])
    
    data = []
    for place in results:
        place_id = place.get('place_id')
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            'place_id': place_id,
            'fields': 'name,formatted_phone_number,website,formatted_address',
            'key': api_key
        }
        details = requests.get(details_url, params=details_params).json().get('result', {})
        
        # Filtrujeme LEN firmy bez webovej stránky
        if not details.get('website'):
            data.append({
                'Názov firmy': details.get('name', 'Neznámy názov'),
                'Telefón': details.get('formatted_phone_number', 'Neuvedený'),
                'Adresa': details.get('formatted_address', 'Neuvedená')
            })
    return data

# Funkcia pre Gemini prompt
def generate_pitch(company_name, b_type, c_city):
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Si špičkový B2B obchodník. Vygeneruj krátku a údernú správy (SMS alebo oslovenie cez cold-call) pre majiteľa firmy:
    - Název firmy: {company_name}
    - Odvetvie: {b_type}
    - Mesto: {c_city}

    Firma nemá vlastný web. Povedz im 1 hlavný dôvod, prečo kvôli tomu prichádzajú o lokálnych zákazníkov a navrhni rýchly 5-minútový hovor. Buď priamy, profesionálny a priateľský.
    """
    res = model.generate_content(prompt)
    return res.text

# Vyhľadávanie
if st.button("🔎 Spustiť vyhľadávanie firiem"):
    if not google_key or not gemini_key:
        st.warning("⚠️ Zadať oba API kľúče v ľavom paneli je povinné.")
    else:
        with st.spinner("Prehľadávam Google Maps a overujem webstránky..."):
            found_businesses = get_businesses(city, business_type, google_key)
            st.session_state['data'] = found_businesses

# Zobrazenie výsledkov
if 'data' in st.session_state:
    data = st.session_state['data']
    st.write("---")
    st.subheader(f"Nájdené firmy bez webu: {len(data)}")
    
    if data:
        # Možnosť stiahnuť ako CSV
        df = pd.DataFrame(data)
        st.download_button(
            label="📥 Stiahnuť zoznam do Excelu (CSV)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f'firmy_bez_webu_{city}.csv',
            mime='text/csv',
        )
        
        # Zobrazenie jednotlivých firiem
        for i, item in enumerate(data):
            with st.container():
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"### 🏬 {item['Názov firmy']}")
                    st.write(f"📞 **Telefón:** `{item['Telefón']}` | 📍 **Adresa:** {item['Adresa']}")
                with c2:
                    if st.button("✨ Vygenerovať prompt", key=f"btn_{i}"):
                        with st.spinner("Gemini vytvára ponuku..."):
                            pitch = generate_pitch(item['Názov firmy'], business_type, city)
                            st.session_state[f"pitch_{i}"] = pitch
                
                # Ak bol prompt vygenerovaný, zobrazí sa tu
                if f"pitch_{i}" in st.session_state:
                    st.info(st.session_state[f"pitch_{i}"])
                st.write("---")
    else:
        st.info("Pre zadanú kombináciu mesta a kategórie sa nenašli žiadne firmy bez webu.")
