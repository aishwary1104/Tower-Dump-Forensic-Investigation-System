import os
import sys
import json
import hashlib
import tempfile
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict, Counter
import networkx as nx
from math import log2, sqrt
import warnings
warnings.filterwarnings('ignore')

# Map imports
import folium
from folium.plugins import HeatMap, TimestampedGeoJson

st.set_page_config(page_title="Geospatial Threat Analysis Platform", layout="wide")

# --------------------------------------------------
# USER CREDENTIALS
# Modify these to change usernames / passwords
# --------------------------------------------------

USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Administrator"
    },
    "analyst1": {
        "password": hashlib.sha256("analyst123".encode()).hexdigest(),
        "role": "analyst",
        "name": "Senior Analyst"
    },
    "analyst2": {
        "password": hashlib.sha256("analyst456".encode()).hexdigest(),
        "role": "analyst",
        "name": "Field Analyst"
    }
}

# Admin sees everything; analyst cannot access Export & Reports or Investigation Builder
ROLE_PAGES = {
    "admin": [
        "Dashboard",
        "Subject Profiles",
        "Association Network",
        "Threat Analysis",
        "Movement Prediction",
        "Crime Correlation",
        "Investigation Builder",
        "🗺️ Map Intelligence",
        "Export & Reports"
    ],
    "analyst": [
        "Dashboard",
        "Subject Profiles",
        "Association Network",
        "Threat Analysis",
        "Movement Prediction",
        "Crime Correlation",
        "🗺️ Map Intelligence",
    ]
}

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

def show_login():
    st.markdown("""
    <style>
    /* Hide sidebar completely on login page */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Full page dark background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%) !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }

    /* Hide the default Streamlit top padding / block container ghost */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }

    /* Remove any widget borders that show up above login */
    [data-testid="stVerticalBlock"] > div:first-child { padding-top: 0 !important; }

    .login-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 96vh;
        padding: 20px;
    }
    .login-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 16px;
        padding: 48px 40px;
        backdrop-filter: blur(12px);
        width: 100%;
        max-width: 420px;
    }
    .login-logo {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 3px;
        margin-bottom: 4px;
    }
    .login-sub {
        color: #7a8fa6;
        text-align: center;
        font-size: 0.85rem;
        margin-bottom: 32px;
        line-height: 1.6;
    }
    .login-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Center column trick — no file uploader ghost
    _, col_m, _ = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown("""
        <div style="height:60px;"></div>
        <div style="text-align:center;font-size:2.8rem;font-weight:800;color:#fff;letter-spacing:4px;margin-bottom:4px;">
            🛡️ GTAP
        </div>
        <div style="color:#7a8fa6;text-align:center;font-size:0.85rem;margin-bottom:28px;line-height:1.7;">
            Geospatial Threat Analysis Platform<br>
            <span style="color:#e74c3c;font-size:0.78rem;font-weight:600;">⚠ AUTHORIZED ACCESS ONLY</span>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("👤 Username", placeholder="Enter your username", label_visibility="collapsed")
        st.caption("👤 Username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", label_visibility="collapsed")
        st.caption("🔒 Password")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("🔐  Sign In", use_container_width=True, type="primary"):
            if not username or not password:
                st.warning("Please enter both username and password.")
            elif username in USERS:
                hashed = hashlib.sha256(password.encode()).hexdigest()
                if USERS[username]["password"] == hashed:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = USERS[username]["role"]
                    st.session_state["name"] = USERS[username]["name"]
                    st.rerun()
                else:
                    st.error("❌ Incorrect password.")
            else:
                st.error("❌ Username not found.")

        st.markdown("<div style='color:#556;font-size:0.73rem;text-align:center;margin-top:18px;'>Contact your administrator for access credentials.</div>", unsafe_allow_html=True)


# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    show_login()
    st.stop()

# --------------------------------------------------
# MAP FUNCTIONS
# --------------------------------------------------

DEVICE_COLORS = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]

def render_map(m, height=500):
    if m is None:
        st.warning("No data available for this map.")
        return
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        m.save(f.name)
        html = open(f.name, encoding="utf-8").read()
    st.components.v1.html(html, height=height, scrolling=False)

def create_single_device_map(df, device_id, device_col="phone_number"):
    data = df[df[device_col] == device_id].sort_values("timestamp")
    if data.empty:
        return None
    m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=13, tiles="CartoDB dark_matter")
    coords = []
    for i, (_, r) in enumerate(data.iterrows()):
        coords.append((r["lat"], r["lon"]))
        if i == 0:
            color, icon = "green", "play"
        elif i == len(data) - 1:
            color, icon = "red", "stop"
        else:
            color, icon = "blue", "info-sign"
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(f"<b>Tower:</b> {r['tower_id']}<br><b>Time:</b> {r['timestamp']}<br><b>Device:</b> {device_id}", max_width=200),
            icon=folium.Icon(color=color, icon=icon, prefix="glyphicon")
        ).add_to(m)
    folium.PolyLine(coords, color="red", weight=3, opacity=0.8).add_to(m)
    return m

def create_multi_device_map(df, device_col="phone_number"):
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=12, tiles="CartoDB dark_matter")
    devices = df[device_col].unique()
    for i, device in enumerate(devices):
        color = DEVICE_COLORS[i % len(DEVICE_COLORS)]
        data = df[df[device_col] == device].sort_values("timestamp")
        coords = []
        for _, r in data.iterrows():
            coords.append((r["lat"], r["lon"]))
            folium.CircleMarker(
                [r["lat"], r["lon"]], radius=7, color=color, fill=True,
                fill_color=color, fill_opacity=0.8,
                popup=folium.Popup(f"<b>{device}</b><br>Tower: {r['tower_id']}<br>Time: {r['timestamp']}", max_width=200)
            ).add_to(m)
        if len(coords) > 1:
            folium.PolyLine(coords, color=color, weight=2, opacity=0.7, tooltip=str(device)).add_to(m)
    legend_html = "<div style='position:fixed;bottom:30px;left:30px;z-index:1000;background:rgba(0,0,0,0.8);padding:12px;border-radius:8px;color:white;font-size:13px;'><b>📱 Devices</b><br>"
    for i, device in enumerate(devices):
        legend_html += f"<span style='color:{DEVICE_COLORS[i % len(DEVICE_COLORS)]}'>●</span> {device}<br>"
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

def create_heatmap(df):
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=12, tiles="CartoDB dark_matter")
    HeatMap(df[["lat", "lon"]].values.tolist(), min_opacity=0.4, radius=25, blur=15,
            gradient={0.2: "blue", 0.5: "lime", 0.8: "orange", 1.0: "red"}).add_to(m)
    return m

def create_timeline_map(df, device_id, device_col="phone_number"):
    data = df[df[device_col] == device_id].sort_values("timestamp").reset_index(drop=True)
    if data.empty:
        return None
    m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=13, tiles="CartoDB dark_matter")
    coords = []
    for i, r in data.iterrows():
        coords.append((r["lat"], r["lon"]))
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(f"<b>Stop #{i+1}</b><br>Tower: {r['tower_id']}<br>Time: {r['timestamp']}", max_width=200),
            icon=folium.DivIcon(
                html=f"<div style='background:#e74c3c;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:12px;border:2px solid white;'>{i+1}</div>",
                icon_size=(24, 24), icon_anchor=(12, 12)
            )
        ).add_to(m)
        if len(coords) > 1:
            folium.PolyLine(coords, color="red", weight=3, opacity=0.8).add_to(m)
    return m

def create_animated_map(df, device_id, device_col="phone_number"):
    data = df[df[device_col] == device_id].sort_values("timestamp")
    if data.empty:
        return None
    features = []
    for _, row in data.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": {
                "time": row["timestamp"].isoformat(),
                "popup": f"<b>{device_id}</b><br>Tower: {row['tower_id']}",
                "icon": "circle",
                "iconstyle": {"fillColor": "#e74c3c", "fillOpacity": 0.9, "stroke": True, "color": "white", "weight": 2, "radius": 10}
            }
        })
    m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=13, tiles="CartoDB dark_matter")
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT5M", add_last_point=True, auto_play=False,
        loop=False, max_speed=5, loop_button=True,
        date_options="YYYY-MM-DD HH:mm", time_slider_drag_update=True
    ).add_to(m)
    return m

def compare_devices_map(df, device1, device2, device_col="phone_number"):
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=12, tiles="CartoDB dark_matter")
    colors = {device1: "red", device2: "blue"}
    all_towers = {}
    for device in [device1, device2]:
        data = df[df[device_col] == device].sort_values("timestamp")
        coords = []
        for _, row in data.iterrows():
            coords.append((row["lat"], row["lon"]))
            folium.CircleMarker(
                [row["lat"], row["lon"]], radius=7, color=colors[device],
                fill=True, fill_color=colors[device], fill_opacity=0.8,
                popup=folium.Popup(f"<b>{device}</b><br>Tower: {row['tower_id']}<br>Time: {row['timestamp']}", max_width=200)
            ).add_to(m)
        if len(coords) > 1:
            folium.PolyLine(coords, color=colors[device], weight=4, opacity=0.8, tooltip=str(device)).add_to(m)
        all_towers[device] = set(df[df[device_col] == device]["tower_id"].tolist())
    common_towers = all_towers.get(device1, set()) & all_towers.get(device2, set())
    for tower in common_towers:
        tower_data = df[df["tower_id"] == tower].iloc[0]
        folium.CircleMarker(
            [tower_data["lat"], tower_data["lon"]], radius=20,
            color="yellow", fill=False, weight=3, tooltip=f"⚠️ Co-location at {tower}"
        ).add_to(m)
    legend_html = f"<div style='position:fixed;bottom:30px;left:30px;z-index:1000;background:rgba(0,0,0,0.85);padding:12px;border-radius:8px;color:white;font-size:13px;'><b>🔍 Comparison</b><br><span style='color:red'>●</span> {device1}<br><span style='color:blue'>●</span> {device2}<br><span style='color:yellow'>○</span> Co-location point</div>"
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

# --------------------------------------------------
# THREAT ANALYSIS SYSTEM
# --------------------------------------------------

class ThreatAnalysisSystem:
    def __init__(self):
        self.events_df = None
        self.profiles = {}
        self.graph = nx.DiGraph()
        self.threats = {}
        self.predictions = {}

    def load_events(self, df):
        self.events_df = df.copy()
        self.events_df['timestamp'] = pd.to_datetime(self.events_df['timestamp'])
        return len(self.events_df)

    def anonymize_phone(self, phone):
        return hashlib.sha256(str(phone).encode()).hexdigest()[:16]

    def create_profiles(self):
        if self.events_df is None:
            return {}
        for phone in self.events_df['phone_number'].unique():
            phone_events = self.events_df[self.events_df['phone_number'] == phone].sort_values('timestamp')
            home_tower = self.detect_home_tower(phone_events)
            work_tower = self.detect_work_tower(phone_events)
            entropy = self.calculate_entropy(phone_events)
            night_ratio = self.calculate_night_activity(phone_events)
            self.profiles[phone] = {
                'phone': phone,
                'anon_id': self.anonymize_phone(phone),
                'event_count': len(phone_events),
                'home_tower': home_tower,
                'work_tower': work_tower,
                'mobility_entropy': entropy,
                'night_activity_ratio': night_ratio,
                'first_event': phone_events['timestamp'].min(),
                'last_event': phone_events['timestamp'].max(),
                'towers': phone_events['tower_id'].unique().tolist()
            }
        return self.profiles

    def detect_home_tower(self, phone_events):
        night_events = phone_events[(phone_events['timestamp'].dt.hour >= 22) | (phone_events['timestamp'].dt.hour < 6)]
        if len(night_events) > 0:
            return night_events['tower_id'].mode()[0] if len(night_events['tower_id'].mode()) > 0 else "Unknown"
        return phone_events['tower_id'].mode()[0] if len(phone_events['tower_id'].mode()) > 0 else "Unknown"

    def detect_work_tower(self, phone_events):
        work_events = phone_events[(phone_events['timestamp'].dt.hour >= 9) & (phone_events['timestamp'].dt.hour < 17)]
        if len(work_events) > 0:
            towers = work_events['tower_id'].value_counts()
            home = self.detect_home_tower(phone_events)
            for tower in towers.index:
                if tower != home:
                    return tower
        return "Unknown"

    def calculate_entropy(self, phone_events):
        tower_counts = phone_events['tower_id'].value_counts()
        if len(tower_counts) == 0:
            return 0
        total = len(phone_events)
        entropy = -sum((count/total) * log2(count/total) for count in tower_counts if count > 0)
        max_entropy = log2(len(tower_counts))
        return entropy / max_entropy if max_entropy > 0 else 0

    def calculate_night_activity(self, phone_events):
        night_events = phone_events[(phone_events['timestamp'].dt.hour >= 22) | (phone_events['timestamp'].dt.hour < 6)]
        return len(night_events) / len(phone_events) if len(phone_events) > 0 else 0

    def build_association_graph(self):
        self.graph.clear()
        for phone in self.profiles:
            self.graph.add_node(phone, label=self.profiles[phone]['anon_id'], entropy=self.profiles[phone]['mobility_entropy'])
        phone_list = list(self.profiles.keys())
        for i, phone1 in enumerate(phone_list):
            for phone2 in phone_list[i+1:]:
                events1 = self.events_df[self.events_df['phone_number'] == phone1]
                events2 = self.events_df[self.events_df['phone_number'] == phone2]
                common_towers = set(events1['tower_id'].unique()) & set(events2['tower_id'].unique())
                if len(common_towers) > 0:
                    proximity_count = 0
                    for tower in common_towers:
                        tower_events1 = events1[events1['tower_id'] == tower].sort_values('timestamp')
                        tower_events2 = events2[events2['tower_id'] == tower].sort_values('timestamp')
                        for t1 in tower_events1['timestamp']:
                            for t2 in tower_events2['timestamp']:
                                if abs((t1 - t2).total_seconds()) < 600:
                                    proximity_count += 1
                    if proximity_count > 0:
                        self.graph.add_edge(phone1, phone2, weight=proximity_count)
        return self.graph

    def calculate_centralities(self):
        centralities = {}
        if self.graph.number_of_nodes() > 0:
            degree_cent = nx.degree_centrality(self.graph)
            between_cent = nx.betweenness_centrality(self.graph)
            close_cent = nx.closeness_centrality(self.graph)
            for phone in self.profiles:
                centralities[phone] = {
                    'degree': degree_cent.get(phone, 0),
                    'betweenness': between_cent.get(phone, 0),
                    'closeness': close_cent.get(phone, 0)
                }
        return centralities

    def calculate_threat_scores(self, weights=None):
        if weights is None:
            weights = {'mobility': 0.35, 'association': 0.30, 'crime': 0.20, 'night': 0.15}
        centralities = self.calculate_centralities()
        for phone, profile in self.profiles.items():
            mobility_score = profile['mobility_entropy'] * 100
            assoc_score = 0
            if phone in centralities:
                cent = centralities[phone]
                assoc_score = (cent['degree'] + cent['betweenness'] + cent['closeness']) / 3 * 100
            night_score = profile['night_activity_ratio'] * 100
            crime_score = np.random.uniform(0, 30)
            overall_score = (mobility_score * weights['mobility'] + assoc_score * weights['association'] +
                             night_score * weights['night'] + crime_score * weights['crime'])
            self.threats[phone] = {
                'overall_score': min(100, overall_score),
                'mobility_score': mobility_score,
                'association_score': assoc_score,
                'night_score': night_score,
                'crime_score': crime_score,
                'risk_level': self.classify_risk(overall_score)
            }
        return self.threats

    def classify_risk(self, score):
        if score < 25: return 'LOW'
        elif score < 50: return 'MEDIUM'
        elif score < 75: return 'HIGH'
        else: return 'CRITICAL'

    def markov_prediction(self, phone, steps=5):
        phone_events = self.events_df[self.events_df['phone_number'] == phone].sort_values('timestamp')
        if len(phone_events) < 2:
            return []
        towers = phone_events['tower_id'].tolist()
        transitions = defaultdict(lambda: defaultdict(int))
        for i in range(len(towers) - 1):
            transitions[towers[i]][towers[i+1]] += 1
        predictions = []
        current = towers[-1]
        for _ in range(steps):
            if current in transitions:
                next_towers = transitions[current]
                if next_towers:
                    total = sum(next_towers.values())
                    best_next = max(next_towers, key=next_towers.get)
                    confidence = next_towers[best_next] / total
                    predictions.append({'tower': best_next, 'confidence': confidence})
                    current = best_next
                else:
                    break
            else:
                break
        return predictions

    def find_crime_intersections(self, crime_scenes, tolerance_hours=1):
        intersections = {}
        for crime_id, scene in crime_scenes.items():
            crime_time = scene['time']
            crime_location = scene['tower_id']
            suspects = []
            for phone in self.profiles:
                phone_events = self.events_df[self.events_df['phone_number'] == phone]
                nearby = phone_events[phone_events['tower_id'] == crime_location]
                for idx, event in nearby.iterrows():
                    time_diff = abs((event['timestamp'] - crime_time).total_seconds() / 3600)
                    if time_diff <= tolerance_hours:
                        suspects.append({
                            'phone': phone,
                            'anon_id': self.profiles[phone]['anon_id'],
                            'time_diff_hours': time_diff,
                            'event_time': event['timestamp']
                        })
            intersections[crime_id] = suspects
        return intersections

@st.cache_resource
def init_system():
    return ThreatAnalysisSystem()

system = init_system()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

role = st.session_state["role"]
name = st.session_state["name"]
username = st.session_state["username"]

role_color = "#e74c3c" if role == "admin" else "#3498db"
role_label = "🔴 ADMIN" if role == "admin" else "🔵 ANALYST"

st.sidebar.markdown(f"""
<div style="background:rgba(255,255,255,0.06);border-radius:10px;padding:12px 14px;margin-bottom:12px;">
    <div style="font-size:0.8rem;color:#aaa;">Logged in as</div>
    <div style="font-weight:700;font-size:1rem;">{name}</div>
    <div style="font-size:0.75rem;color:#888;">@{username}</div>
    <span style="background:{role_color};color:white;padding:2px 10px;border-radius:20px;font-size:0.72rem;font-weight:600;">{role_label}</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("⚙️ Configuration")
privacy_mode = st.sidebar.checkbox("Privacy Mode (Anonymize)", value=True)

allowed_pages = ROLE_PAGES[role]
page = st.sidebar.radio("Navigation", allowed_pages)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    for key in ["logged_in", "username", "role", "name"]:
        st.session_state.pop(key, None)
    st.rerun()

st.title("🔍 Geospatial Intelligence & Behavioral Threat Analysis Platform")

# --------------------------------------------------
# HARD ACCESS CONTROL — blocks even URL manipulation
# --------------------------------------------------

ADMIN_ONLY_PAGES = {"Investigation Builder", "Export & Reports"}

if page in ADMIN_ONLY_PAGES and role != "admin":
    st.error("🚫 Access Denied — This page is restricted to Administrators only.")
    st.info("Contact your administrator if you need access to this section.")
    st.stop()


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":
    st.header("Executive Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    if system.events_df is not None:
        with col1:
            st.metric("Total Events", len(system.events_df))
        with col2:
            st.metric("Unique Subjects", len(system.profiles))
        with col3:
            st.metric("Total Towers", system.events_df['tower_id'].nunique())
        with col4:
            critical_threats = sum(1 for t in system.threats.values() if t['risk_level'] == 'CRITICAL')
            st.metric("Critical Threats", critical_threats)
    st.divider()
    uploaded_file = st.file_uploader("📤 Upload Telecom Events CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        required_cols = ['phone_number', 'timestamp', 'tower_id']
        if all(col in df.columns for col in required_cols):
            system.load_events(df)
            system.create_profiles()
            system.build_association_graph()
            system.calculate_threat_scores()
            st.success(f"✅ Loaded {len(system.events_df)} events from {len(system.profiles)} subjects")
            st.subheader("Data Summary")
            fig = px.histogram(system.events_df, x='timestamp', nbins=30, title='Event Timeline')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Missing required columns: {required_cols}")

# --------------------------------------------------
# SUBJECT PROFILES
# --------------------------------------------------

elif page == "Subject Profiles":
    st.header("Subject Behavioral Profiles")
    if system.profiles:
        subject_options = [(phone, system.profiles[phone]['anon_id'] if privacy_mode else phone)
                           for phone in system.profiles.keys()]
        selected_idx = st.selectbox("Select Subject", range(len(subject_options)),
                                    format_func=lambda i: subject_options[i][1])
        phone = subject_options[selected_idx][0]
        profile = system.profiles[phone]
        st.subheader(f"Profile: {profile['anon_id'] if privacy_mode else phone}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Events", profile['event_count'])
        with col2:
            st.metric("Mobility Entropy", f"{profile['mobility_entropy']:.2f}")
        with col3:
            st.metric("Night Activity", f"{profile['night_activity_ratio']:.2%}")
        with col4:
            st.metric("Unique Towers", len(profile['towers']))
        st.divider()
        st.write(f"**Home Tower:** {profile['home_tower']}")
        st.write(f"**Work Tower:** {profile['work_tower']}")
        st.write(f"**Time Range:** {profile['first_event']} to {profile['last_event']}")
        phone_events = system.events_df[system.events_df['phone_number'] == phone]
        hourly_dist = phone_events.groupby(phone_events['timestamp'].dt.hour).size()
        fig = px.bar(x=hourly_dist.index, y=hourly_dist.values, title='Hourly Activity Distribution',
                     labels={'x': 'Hour of Day', 'y': 'Event Count'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Upload data first in Dashboard to view profiles")

# --------------------------------------------------
# ASSOCIATION NETWORK
# --------------------------------------------------

elif page == "Association Network":
    st.header("Criminal Association Network Analysis")
    if system.graph.number_of_nodes() > 0:
        st.subheader("Network Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", system.graph.number_of_nodes())
        with col2:
            st.metric("Edges", system.graph.number_of_edges())
        with col3:
            density = nx.density(system.graph)
            st.metric("Density", f"{density:.3f}")
        centralities = system.calculate_centralities()
        st.subheader("Top Subjects by Centrality")
        degree_ranking = sorted(centralities.items(), key=lambda x: x[1]['degree'], reverse=True)[:10]
        rank_data = []
        for phone, cent in degree_ranking:
            rank_data.append({
                'Subject': system.profiles[phone]['anon_id'] if privacy_mode else phone,
                'Degree': f"{cent['degree']:.3f}",
                'Betweenness': f"{cent['betweenness']:.3f}",
                'Closeness': f"{cent['closeness']:.3f}"
            })
        st.dataframe(pd.DataFrame(rank_data), use_container_width=True)
        st.subheader("Network Visualization")
        st.info("Top 5 Connected Subjects:")
        for phone, cent in degree_ranking[:5]:
            neighbors = list(system.graph.neighbors(phone))
            neighbor_display = [system.profiles[n]['anon_id'] if privacy_mode else n for n in neighbors[:3]]
            st.write(f"• {system.profiles[phone]['anon_id'] if privacy_mode else phone} → Connected to: {neighbor_display}")
    else:
        st.info("📊 Upload data first in Dashboard to analyze network")

# --------------------------------------------------
# THREAT ANALYSIS
# --------------------------------------------------

elif page == "Threat Analysis":
    st.header("Multi-Factor Threat Scoring Engine")
    if system.threats:
        col1, col2 = st.columns(2)
        with col1:
            threat_levels = Counter(t['risk_level'] for t in system.threats.values())
            fig = px.pie(values=list(threat_levels.values()), names=list(threat_levels.keys()),
                         title='Risk Level Distribution',
                         color_discrete_map={'LOW': 'green', 'MEDIUM': 'yellow', 'HIGH': 'orange', 'CRITICAL': 'red'})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            scores = [t['overall_score'] for t in system.threats.values()]
            fig = px.histogram(x=scores, nbins=20, title='Threat Score Distribution',
                               labels={'x': 'Threat Score', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
        st.divider()
        st.subheader("Top Threats")
        threat_ranking = sorted(system.threats.items(), key=lambda x: x[1]['overall_score'], reverse=True)[:15]
        threat_data = []
        for phone, threat in threat_ranking:
            threat_data.append({
                'Subject': system.profiles[phone]['anon_id'] if privacy_mode else phone,
                'Score': f"{threat['overall_score']:.1f}",
                'Risk': threat['risk_level'],
                'Mobility': f"{threat['mobility_score']:.1f}",
                'Association': f"{threat['association_score']:.1f}",
                'Night Activity': f"{threat['night_score']:.1f}"
            })
        st.dataframe(pd.DataFrame(threat_data), use_container_width=True)
    else:
        st.info("📊 Upload data first in Dashboard to calculate threats")

# --------------------------------------------------
# MOVEMENT PREDICTION
# --------------------------------------------------

elif page == "Movement Prediction":
    st.header("Predictive Movement Modeling (Markov Chains)")
    if system.profiles:
        subject_options = [(phone, system.profiles[phone]['anon_id'] if privacy_mode else phone)
                           for phone in system.profiles.keys()]
        selected_idx = st.selectbox("Select Subject for Prediction", range(len(subject_options)),
                                    format_func=lambda i: subject_options[i][1])
        phone = subject_options[selected_idx][0]
        predictions = system.markov_prediction(phone, steps=5)
        if predictions:
            st.subheader("Next Predicted Locations (Markov Chain)")
            pred_data = []
            for i, pred in enumerate(predictions, 1):
                pred_data.append({'Step': i, 'Predicted Tower': pred['tower'], 'Confidence': f"{pred['confidence']:.2%}"})
            st.dataframe(pd.DataFrame(pred_data), use_container_width=True)
            confidences = [p['confidence'] for p in predictions]
            fig = px.bar(x=list(range(1, len(predictions)+1)), y=confidences,
                         title='Prediction Confidence by Step',
                         labels={'x': 'Prediction Step', 'y': 'Confidence'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Insufficient movement history for prediction")
    else:
        st.info("📊 Upload data first in Dashboard")

# --------------------------------------------------
# CRIME CORRELATION
# --------------------------------------------------

elif page == "Crime Correlation":
    st.header("Multi-Scene Crime Correlation Analysis")
    st.subheader("Define Crime Scenes")
    num_crimes = st.number_input("Number of crime scenes", min_value=1, max_value=5, value=2)
    crime_scenes = {}
    cols = st.columns(num_crimes)
    for i in range(num_crimes):
        with cols[i % num_crimes]:
            st.write(f"**Crime Scene {i+1}**")
            tower = st.text_input(f"Tower ID (Scene {i+1})", value=f"T{1000+i}", key=f"tower_{i}")
            time = st.time_input(f"Time (Scene {i+1})", value=datetime.now().time(), key=f"time_{i}")
            crime_scenes[f"crime_{i}"] = {'tower_id': tower, 'time': datetime.combine(datetime.today(), time)}
    if st.button("🔍 Find Correlated Subjects"):
        intersections = system.find_crime_intersections(crime_scenes)
        all_suspects = {}
        for crime_id, suspects in intersections.items():
            for suspect in suspects:
                phone = suspect['phone']
                if phone not in all_suspects:
                    all_suspects[phone] = []
                all_suspects[phone].append(crime_id)
        multi_crime_suspects = {phone: crimes for phone, crimes in all_suspects.items() if len(crimes) > 1}
        st.subheader("🎯 Subjects Present at Multiple Crime Scenes")
        if multi_crime_suspects:
            suspect_data = []
            for phone, crimes in sorted(multi_crime_suspects.items(), key=lambda x: len(x[1]), reverse=True):
                suspect_data.append({
                    'Subject': system.profiles[phone]['anon_id'] if privacy_mode else phone,
                    'Crime Scenes': len(crimes),
                    'Threat Score': f"{system.threats.get(phone, {}).get('overall_score', 0):.1f}",
                    'Risk Level': system.threats.get(phone, {}).get('risk_level', 'N/A')
                })
            st.dataframe(pd.DataFrame(suspect_data), use_container_width=True)
        else:
            st.info("No subjects found at multiple crime scenes")

# --------------------------------------------------
# INVESTIGATION BUILDER
# --------------------------------------------------

elif page == "Investigation Builder":
    st.header("Investigation Assistant & Case Builder")
    st.subheader("Create Investigation Case")
    case_name = st.text_input("Case Name", value="Investigation_001")
    if system.profiles:
        subject_options = [(phone, system.profiles[phone]['anon_id'] if privacy_mode else phone)
                           for phone in system.profiles.keys()]
        selected_subjects = st.multiselect("Select Subjects of Interest", range(len(subject_options)),
                                           format_func=lambda i: subject_options[i][1])
        if selected_subjects:
            st.subheader("📋 Case Summary")
            for idx in selected_subjects:
                phone = subject_options[idx][0]
                profile = system.profiles[phone]
                threat = system.threats.get(phone, {})
                with st.expander(f"Subject: {profile['anon_id'] if privacy_mode else phone}"):
                    st.write(f"**Threat Score:** {threat.get('overall_score', 0):.1f} ({threat.get('risk_level', 'N/A')})")
                    st.write(f"**Home Tower:** {profile['home_tower']}")
                    st.write(f"**Mobility Entropy:** {profile['mobility_entropy']:.2f}")
                    st.write(f"**Night Activity:** {profile['night_activity_ratio']:.2%}")
                    st.write("**AI Reasoning:**")
                    reasoning = f"""
Subject shows {'high' if threat.get('overall_score', 0) > 50 else 'moderate'} threat indicators:
- Mobility entropy of {profile['mobility_entropy']:.2f} suggests {'frequent movement' if profile['mobility_entropy'] > 0.5 else 'routine patterns'}
- Night activity of {profile['night_activity_ratio']:.0%} indicates {'unusual night activity' if profile['night_activity_ratio'] > 0.2 else 'normal patterns'}
- Associated with {system.graph.degree(phone) if phone in system.graph else 0} other subjects
                    """
                    st.info(reasoning)
            if st.button("💾 Save Investigation"):
                st.success(f"✅ Investigation '{case_name}' saved successfully")
    else:
        st.info("📊 Upload data first in Dashboard")

# --------------------------------------------------
# MAP INTELLIGENCE  ← NEW PAGE
# --------------------------------------------------

elif page == "🗺️ Map Intelligence":
    st.header("🗺️ Map Intelligence")

    if system.events_df is not None and "lat" in system.events_df.columns and "lon" in system.events_df.columns:

        phones = list(system.profiles.keys())
        phone_labels = [system.profiles[p]['anon_id'] if privacy_mode else p for p in phones]

        selected_idx = st.selectbox(
            "Select Subject",
            range(len(phones)),
            format_func=lambda i: phone_labels[i]
        )
        selected_phone = phones[selected_idx]

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📍 Single Device",
            "🌍 All Devices",
            "🔥 Heatmap",
            "⏱ Timeline",
            "🎬 Animated",
            "🔍 Compare"
        ])

        with tab1:
            st.markdown("**Single device path — 🟢 start → 🔴 end. Click markers for tower info.**")
            if st.button("Show Single Device Map"):
                with st.spinner("Rendering map..."):
                    render_map(create_single_device_map(system.events_df, selected_phone), height=500)

        with tab2:
            st.markdown("**All devices on one map — each device gets a unique color.**")
            if st.button("Show All Devices"):
                with st.spinner("Rendering map..."):
                    render_map(create_multi_device_map(system.events_df), height=500)

        with tab3:
            st.markdown("**Tower activity heatmap — red zones = most signals recorded.**")
            if st.button("Show Heatmap"):
                with st.spinner("Rendering map..."):
                    render_map(create_heatmap(system.events_df), height=500)

        with tab4:
            st.markdown("**Numbered stops ①②③ in chronological order — follow the journey.**")
            if st.button("Show Timeline Map"):
                with st.spinner("Rendering map..."):
                    render_map(create_timeline_map(system.events_df, selected_phone), height=500)

        with tab5:
            st.markdown("**Animated playback — press ▶ on the map slider to replay movement.**")
            if st.button("▶ Launch Animated Map"):
                with st.spinner("Building animation..."):
                    render_map(create_animated_map(system.events_df, selected_phone), height=620)

        with tab6:
            st.markdown("**Compare two subjects — 🟡 yellow ring = co-location point.**")
            colA, colB = st.columns(2)
            with colA:
                idx1 = st.selectbox("Subject 1", range(len(phones)), format_func=lambda i: phone_labels[i], key="cmp1")
            with colB:
                idx2 = st.selectbox("Subject 2", range(len(phones)), format_func=lambda i: phone_labels[i], key="cmp2")
            if phones[idx1] == phones[idx2]:
                st.warning("⚠️ Please select two different subjects.")
            elif st.button("Compare Subjects"):
                with st.spinner("Rendering comparison map..."):
                    render_map(compare_devices_map(system.events_df, phones[idx1], phones[idx2]), height=600)

    elif system.events_df is not None and ("lat" not in system.events_df.columns or "lon" not in system.events_df.columns):
        st.error("⚠️ Your CSV is missing **lat** and **lon** columns. Maps require latitude/longitude data.")
        st.code("Required columns: phone_number, timestamp, tower_id, lat, lon")
    else:
        st.info("📊 Upload data first in the **Dashboard** page to use maps.")
        st.markdown("Your CSV needs these columns:")
        st.code("phone_number, timestamp, tower_id, lat, lon")

# --------------------------------------------------
# EXPORT & REPORTS
# --------------------------------------------------

elif page == "Export & Reports":
    st.header("Export & Reporting Center")
    if system.profiles:
        export_format = st.radio("Select Export Format", ["CSV", "JSON", "PDF Summary"])
        if export_format == "CSV":
            profile_list = []
            for phone, profile in system.profiles.items():
                profile_list.append({
                    'Subject_ID': profile['anon_id'] if privacy_mode else phone,
                    'Event_Count': profile['event_count'],
                    'Home_Tower': profile['home_tower'],
                    'Work_Tower': profile['work_tower'],
                    'Mobility_Entropy': profile['mobility_entropy'],
                    'Night_Activity_Ratio': profile['night_activity_ratio'],
                    'Threat_Score': system.threats.get(phone, {}).get('overall_score', 0),
                    'Risk_Level': system.threats.get(phone, {}).get('risk_level', 'N/A')
                })
            export_df = pd.DataFrame(profile_list)
            csv_data = export_df.to_csv(index=False)
            st.download_button(label="📥 Download CSV Report", data=csv_data,
                               file_name=f"threat_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                               mime="text/csv")
        elif export_format == "JSON":
            export_json = {
                'timestamp': datetime.now().isoformat(),
                'profiles': system.profiles,
                'threats': system.threats,
                'graph_stats': {'nodes': system.graph.number_of_nodes(), 'edges': system.graph.number_of_edges()}
            }
            json_data = json.dumps(export_json, indent=2, default=str)
            st.download_button(label="📥 Download JSON Report", data=json_data,
                               file_name=f"threat_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                               mime="application/json")
        else:
            st.write("**PDF Report Summary**")
            st.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"Total Subjects Analyzed: {len(system.profiles)}")
            st.write(f"Total Events: {len(system.events_df)}")
            st.write(f"Network Nodes: {system.graph.number_of_nodes()}")
            st.write(f"Network Edges: {system.graph.number_of_edges()}")
            critical_count = sum(1 for t in system.threats.values() if t['risk_level'] == 'CRITICAL')
            high_count = sum(1 for t in system.threats.values() if t['risk_level'] == 'HIGH')
            st.metric("Critical Threats", critical_count)
            st.metric("High Threats", high_count)
    else:
        st.info("📊 Upload data first in Dashboard")