import folium
from folium.plugins import HeatMap, TimestampedGeoJson
import tempfile
import os
 
# Color palette for devices
DEVICE_COLORS = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]
 
 
def save_map(m):
    """Save map to a temp file and return the HTML string."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        m.save(f.name)
        return open(f.name).read()
 
 
# --------------------------------------------------
# 1. SINGLE DEVICE MAP
# --------------------------------------------------
 
def create_map(df, device_id):
    """
    Shows movement path of a single device.
    Markers at each tower with popup showing tower ID + timestamp.
    Red polyline connecting the path in order.
    """
    data = df[df["device_id"] == device_id].sort_values("timestamp")
 
    if data.empty:
        return None
 
    m = folium.Map(
        location=[data["lat"].mean(), data["lon"].mean()],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )
 
    coords = []
 
    for i, (_, r) in enumerate(data.iterrows()):
        coords.append((r["lat"], r["lon"]))
 
        # First marker = green, last = red, middle = blue
        if i == 0:
            color = "green"
            icon = "play"
        elif i == len(data) - 1:
            color = "red"
            icon = "stop"
        else:
            color = "blue"
            icon = "info-sign"
 
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(
                f"<b>Tower:</b> {r['tower_id']}<br>"
                f"<b>Time:</b> {r['timestamp']}<br>"
                f"<b>Device:</b> {r['device_id']}",
                max_width=200
            ),
            icon=folium.Icon(color=color, icon=icon, prefix="glyphicon")
        ).add_to(m)
 
    # Draw path
    folium.PolyLine(
        coords,
        color="red",
        weight=3,
        opacity=0.8,
        tooltip=f"Path of {device_id}"
    ).add_to(m)
 
    return m
 
 
# --------------------------------------------------
# 2. MULTI DEVICE MAP
# --------------------------------------------------
 
def create_multi_device_map(df):
    """
    Shows all devices on one map, each with a unique color.
    Includes a legend.
    """
    m = folium.Map(
        location=[df["lat"].mean(), df["lon"].mean()],
        zoom_start=12,
        tiles="CartoDB dark_matter"
    )
 
    devices = df["device_id"].unique()
 
    for i, device in enumerate(devices):
        color = DEVICE_COLORS[i % len(DEVICE_COLORS)]
        data = df[df["device_id"] == device].sort_values("timestamp")
        coords = []
 
        for _, r in data.iterrows():
            coords.append((r["lat"], r["lon"]))
            folium.CircleMarker(
                [r["lat"], r["lon"]],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>Device:</b> {device}<br>"
                    f"<b>Tower:</b> {r['tower_id']}<br>"
                    f"<b>Time:</b> {r['timestamp']}",
                    max_width=200
                )
            ).add_to(m)
 
        if len(coords) > 1:
            folium.PolyLine(
                coords,
                color=color,
                weight=2,
                opacity=0.7,
                tooltip=device
            ).add_to(m)
 
    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(0,0,0,0.8); padding: 12px; border-radius: 8px;
                color: white; font-size: 13px;">
        <b>📱 Devices</b><br>
    """
    for i, device in enumerate(devices):
        color = DEVICE_COLORS[i % len(DEVICE_COLORS)]
        legend_html += f'<span style="color:{color}">●</span> {device}<br>'
    legend_html += "</div>"
 
    m.get_root().html.add_child(folium.Element(legend_html))
 
    return m
 
 
# --------------------------------------------------
# 3. HEATMAP
# --------------------------------------------------
 
def create_heatmap(df):
    """
    Tower activity heatmap — shows hotspots where most signals were recorded.
    """
    m = folium.Map(
        location=[df["lat"].mean(), df["lon"].mean()],
        zoom_start=12,
        tiles="CartoDB dark_matter"
    )
 
    heat_data = df[["lat", "lon"]].values.tolist()
 
    HeatMap(
        heat_data,
        min_opacity=0.4,
        max_zoom=15,
        radius=25,
        blur=15,
        gradient={0.2: "blue", 0.5: "lime", 0.8: "orange", 1.0: "red"}
    ).add_to(m)
 
    return m
 
 
# --------------------------------------------------
# 4. TIMELINE MAP (step-by-step)
# --------------------------------------------------
 
def create_timeline_map(df, device_id):
    """
    Shows cumulative path of a device step by step.
    Each ping is numbered so you can follow the journey.
    """
    data = df[df["device_id"] == device_id].sort_values("timestamp").reset_index(drop=True)
 
    if data.empty:
        return None
 
    m = folium.Map(
        location=[data["lat"].mean(), data["lon"].mean()],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )
 
    coords = []
 
    for i, r in data.iterrows():
        coords.append((r["lat"], r["lon"]))
 
        # Numbered circle marker
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(
                f"<b>Stop #{i+1}</b><br>"
                f"Tower: {r['tower_id']}<br>"
                f"Time: {r['timestamp']}",
                max_width=200
            ),
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background: #e74c3c;
                    color: white;
                    border-radius: 50%;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 12px;
                    border: 2px solid white;
                ">{i+1}</div>
                """,
                icon_size=(24, 24),
                icon_anchor=(12, 12)
            )
        ).add_to(m)
 
        if len(coords) > 1:
            folium.PolyLine(
                coords,
                color="red",
                weight=3,
                opacity=0.8
            ).add_to(m)
 
    return m
 
 
# --------------------------------------------------
# 5. DEVICE COMPARISON MAP
# --------------------------------------------------
 
def compare_devices_map(df, device1, device2):
    """
    Side-by-side comparison of two devices on same map.
    Device 1 = Red, Device 2 = Blue.
    Co-location points highlighted with a yellow ring.
    """
    m = folium.Map(
        location=[df["lat"].mean(), df["lon"].mean()],
        zoom_start=12,
        tiles="CartoDB dark_matter"
    )
 
    colors = {device1: "red", device2: "blue"}
 
    all_coords = {}
 
    for device in [device1, device2]:
        data = df[df["device_id"] == device].sort_values("timestamp")
        coords = []
 
        for _, row in data.iterrows():
            coords.append((row["lat"], row["lon"]))
 
            folium.CircleMarker(
                [row["lat"], row["lon"]],
                radius=7,
                color=colors[device],
                fill=True,
                fill_color=colors[device],
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>{device}</b><br>"
                    f"Tower: {row['tower_id']}<br>"
                    f"Time: {row['timestamp']}",
                    max_width=200
                )
            ).add_to(m)
 
        if len(coords) > 1:
            folium.PolyLine(
                coords,
                color=colors[device],
                weight=4,
                opacity=0.8,
                tooltip=device
            ).add_to(m)
 
        all_coords[device] = set(df[df["device_id"] == device]["tower_id"].tolist())
 
    # Highlight co-location towers (same tower visited by both)
    common_towers = all_coords.get(device1, set()) & all_coords.get(device2, set())
 
    for tower in common_towers:
        tower_data = df[df["tower_id"] == tower].iloc[0]
        folium.CircleMarker(
            [tower_data["lat"], tower_data["lon"]],
            radius=20,
            color="yellow",
            fill=False,
            weight=3,
            tooltip=f"⚠️ Co-location at {tower}"
        ).add_to(m)
 
    # Legend
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(0,0,0,0.85); padding: 12px; border-radius: 8px;
                color: white; font-size: 13px;">
        <b>🔍 Comparison</b><br>
        <span style="color:red">●</span> {device1}<br>
        <span style="color:blue">●</span> {device2}<br>
        <span style="color:yellow">○</span> Co-location point
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
 
    return m
 
 
# --------------------------------------------------
# 6. ANIMATED MAP (Timestamped playback)
# --------------------------------------------------
 
def create_animated_map(df, device_id):
    """
    Animated playback map using TimestampedGeoJson.
    Shows device moving across towers over time with a play button.
    """
    data = df[df["device_id"] == device_id].sort_values("timestamp")
 
    if data.empty:
        return None
 
    features = []
 
    for _, row in data.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]]
            },
            "properties": {
                "time": row["timestamp"].isoformat(),
                "popup": f"<b>{row['device_id']}</b><br>Tower: {row['tower_id']}",
                "icon": "circle",
                "iconstyle": {
                    "fillColor": "#e74c3c",
                    "fillOpacity": 0.9,
                    "stroke": True,
                    "color": "white",
                    "weight": 2,
                    "radius": 10
                }
            }
        })
 
    m = folium.Map(
        location=[data["lat"].mean(), data["lon"].mean()],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )
 
    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT5M",
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=5,
        loop_button=True,
        date_options="YYYY-MM-DD HH:mm",
        time_slider_drag_update=True
    ).add_to(m)
 
    return m
