#!/usr/bin/env python3
"""
setup_kibana.py — Automatically create STREAMSIGHT Kibana dashboard
"""

import json
import urllib.request
import urllib.error
import sys
import time
import os

KIBANA_URL = "http://localhost:5601"
DATA_VIEW_ID = "streamsight-dv"
INDEX_PATTERN = "streamsight-trades"

HEADERS = {
    "Content-Type": "application/json",
    "kbn-xsrf": "true",
}

IDS = {
    "data_view": DATA_VIEW_ID,
    "vwap": "streamsight-vwap",
    "volume": "streamsight-volume",
    "anomaly": "streamsight-anomaly",
    "zscore": "streamsight-zscore",
    "trades": "streamsight-trades-metric",
    "dashboard": "streamsight-dashboard",
}

def kibana_request(method, path, body=None):
    url = f"{KIBANA_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        if e.code == 409:
            print("    [SKIP] Already exists (use --reset to overwrite)")
            return None
        print(f"    [ERROR] HTTP {e.code}: {error_body[:200]}")
        return None
    except urllib.error.URLError as e:
        print(f"    [ERROR] Connection failed: {e}")
        return None

def wait_for_kibana(timeout=60):
    print(f"Checking Kibana at {KIBANA_URL} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{KIBANA_URL}/api/status", headers=HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                level = data.get("status", {}).get("overall", {}).get("level", "")
                if level == "available":
                    print("  Kibana is ready!\n")
                    return True
        except Exception:
            pass
        time.sleep(2)
    print("  [ERROR] Kibana not available. Run: docker compose up -d")
    return False

def create_data_view():
    print("[1/2] Creating data view ...")
    body = {
        "data_view": {
            "id": DATA_VIEW_ID,
            "title": INDEX_PATTERN,
            "timeFieldName": "window_start",
            "name": "STREAMSIGHT Trades",
        },
        "override": True,
    }
    result = kibana_request("POST", "/api/data_views/data_view", body)
    if result:
        print("    OK — Data view created")
    return result

def _vwap_state():
    lid = "vwap-layer"
    return {
        "datasourceStates": {"indexpattern": {"layers": {lid: {
            "columnOrder": ["col-symbol", "col-time", "col-vwap"],
            "columns": {
                "col-time": {"dataType": "date", "isBucketed": True, "label": "Time", "operationType": "date_histogram", "params": {"interval": "auto"}, "scale": "interval", "sourceField": "window_start"},
                "col-vwap": {"dataType": "number", "isBucketed": False, "label": "Average VWAP", "operationType": "average", "scale": "ratio", "sourceField": "vwap"},
                "col-symbol": {"dataType": "string", "isBucketed": True, "label": "Symbol", "operationType": "terms", "scale": "ordinal", "sourceField": "symbol", "params": {"size": 10, "orderBy": {"type": "column", "columnId": "col-vwap"}, "orderDirection": "desc"}},
            }, "incompleteColumns": {}}}}},
        "visualization": {"layers": [{"accessors": ["col-vwap"], "layerId": lid, "layerType": "data", "seriesType": "line", "xAccessor": "col-time", "splitAccessor": "col-symbol"}], "legend": {"isVisible": True, "position": "right"}, "preferredSeriesType": "line", "valueLabels": "hide"},
        "query": {"language": "kuery", "query": ""}, "filters": [],
    }

def _volume_state():
    lid = "volume-layer"
    return {
        "datasourceStates": {"indexpattern": {"layers": {lid: {
            "columnOrder": ["col-symbol", "col-time", "col-volume"],
            "columns": {
                "col-time": {"dataType": "date", "isBucketed": True, "label": "Time", "operationType": "date_histogram", "params": {"interval": "auto"}, "scale": "interval", "sourceField": "window_start"},
                "col-volume": {"dataType": "number", "isBucketed": False, "label": "Total Volume", "operationType": "sum", "scale": "ratio", "sourceField": "total_volume"},
                "col-symbol": {"dataType": "string", "isBucketed": True, "label": "Symbol", "operationType": "terms", "scale": "ordinal", "sourceField": "symbol", "params": {"size": 10, "orderBy": {"type": "column", "columnId": "col-volume"}, "orderDirection": "desc"}},
            }, "incompleteColumns": {}}}}},
        "visualization": {"layers": [{"accessors": ["col-volume"], "layerId": lid, "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-time", "splitAccessor": "col-symbol"}], "legend": {"isVisible": True, "position": "right"}, "preferredSeriesType": "bar_stacked", "valueLabels": "hide"},
        "query": {"language": "kuery", "query": ""}, "filters": [],
    }

def _anomaly_state():
    lid = "anomaly-layer"
    return {
        "datasourceStates": {"indexpattern": {"layers": {lid: {
            "columnOrder": ["col-anomaly-type", "col-time", "col-trades"],
            "columns": {
                "col-time": {"dataType": "date", "isBucketed": True, "label": "Time", "operationType": "date_histogram", "params": {"interval": "auto"}, "scale": "interval", "sourceField": "window_start"},
                "col-anomaly-type": {"dataType": "string", "isBucketed": True, "label": "Anomaly Type", "operationType": "terms", "scale": "ordinal", "sourceField": "anomaly_type", "params": {"size": 5, "orderBy": {"type": "column", "columnId": "col-trades"}, "orderDirection": "desc"}},
                "col-trades": {"dataType": "number", "isBucketed": False, "label": "Anomaly Trades", "operationType": "sum", "scale": "ratio", "sourceField": "trade_count"},
            }, "incompleteColumns": {}}}}},
        "visualization": {"layers": [{"accessors": ["col-trades"], "layerId": lid, "layerType": "data", "seriesType": "bar_stacked", "xAccessor": "col-time", "splitAccessor": "col-anomaly-type"}], "legend": {"isVisible": True, "position": "right"}, "preferredSeriesType": "bar_stacked", "valueLabels": "hide"},
        "query": {"language": "kuery", "query": "is_anomaly : true"}, "filters": [],
    }

def _zscore_state():
    lid = "zscore-layer"
    return {
        "datasourceStates": {"indexpattern": {"layers": {lid: {
            "columnOrder": ["col-symbol", "col-time", "col-zscore"],
            "columns": {
                "col-time": {"dataType": "date", "isBucketed": True, "label": "Time", "operationType": "date_histogram", "params": {"interval": "auto"}, "scale": "interval", "sourceField": "window_start"},
                "col-zscore": {"dataType": "number", "isBucketed": False, "label": "Average Z-Score", "operationType": "average", "scale": "ratio", "sourceField": "zscore"},
                "col-symbol": {"dataType": "string", "isBucketed": True, "label": "Symbol", "operationType": "terms", "scale": "ordinal", "sourceField": "symbol", "params": {"size": 10, "orderBy": {"type": "column", "columnId": "col-zscore"}, "orderDirection": "desc"}},
            }, "incompleteColumns": {}}}}},
        "visualization": {"layers": [{"accessors": ["col-zscore"], "layerId": lid, "layerType": "data", "seriesType": "area", "xAccessor": "col-time", "splitAccessor": "col-symbol"}], "legend": {"isVisible": True, "position": "right"}, "preferredSeriesType": "area", "valueLabels": "hide"},
        "query": {"language": "kuery", "query": ""}, "filters": [],
    }

def _trades_state():
    lid = "trades-layer"
    return {
        "datasourceStates": {"indexpattern": {"layers": {lid: {
            "columnOrder": ["col-trades"],
            "columns": {
                "col-trades": {"dataType": "number", "isBucketed": False, "label": "Total Trades", "operationType": "sum", "scale": "ratio", "sourceField": "trade_count"},
            }, "incompleteColumns": {}}}}},
        "visualization": {"layerId": lid, "layerType": "data", "metricAccessor": "col-trades"},
        "query": {"language": "kuery", "query": ""}, "filters": [],
    }

def create_dashboard():
    print("[2/2] Creating dashboard with inline panels ...")
    vis_configs = [
        ("p1", "VWAP Over Time by Symbol", "lnsXY", _vwap_state(), ["vwap-layer"], {"x": 0, "y": 0, "w": 48, "h": 15}),
        ("p2", "Volume Over Time by Symbol", "lnsXY", _volume_state(), ["volume-layer"], {"x": 0, "y": 15, "w": 24, "h": 15}),
        ("p3", "Anomaly Events", "lnsXY", _anomaly_state(), ["anomaly-layer"], {"x": 24, "y": 15, "w": 24, "h": 15}),
        ("p4", "Z-Score Over Time by Symbol", "lnsXY", _zscore_state(), ["zscore-layer"], {"x": 0, "y": 30, "w": 36, "h": 12}),
        ("p5", "Total Trades", "lnsMetric", _trades_state(), ["trades-layer"], {"x": 36, "y": 30, "w": 12, "h": 12}),
    ]

    panels = []
    for panel_id, title, vis_type, state, layer_ids, grid in vis_configs:
        refs = [{"type": "index-pattern", "id": DATA_VIEW_ID, "name": f"indexpattern-datasource-layer-{lid}"} for lid in layer_ids]
        panels.append({
            "version": "8.11.4",
            "type": "lens",
            "gridData": {**grid, "i": panel_id},
            "panelIndex": panel_id,
            "embeddableConfig": {
                "attributes": {
                    "title": title,
                    "description": "",
                    "visualizationType": vis_type,
                    "state": state,
                    "references": refs,
                },
                "enhancements": {},
            },
            "title": title,
        })

    body = {
        "attributes": {
            "title": "STREAMSIGHT Real-Time Crypto Analytics",
            "description": "Real-time cryptocurrency analytics: VWAP, volume, Z-score anomaly detection.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "syncCursor": True, "syncTooltips": False, "hidePanelTitles": False}),
            "timeRestore": True,
            "timeTo": "now",
            "timeFrom": "now-1h",
            "refreshInterval": {"pause": False, "value": 10000},
            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})},
        },
        "references": [],
    }

    result = kibana_request("POST", f"/api/saved_objects/dashboard/{IDS['dashboard']}?overwrite=true", body)
    if result:
        print("    OK — Dashboard created")
    return result

def generate_ndjson(filepath="kibana_dashboard.ndjson"):
    print(f"\nGenerating {filepath} ...")
    objects = []
    objects.append({
        "id": DATA_VIEW_ID,
        "type": "index-pattern",
        "attributes": {"title": INDEX_PATTERN, "timeFieldName": "window_start", "name": "STREAMSIGHT Trades"},
        "references": [],
        "managed": False,
    })

    vis_configs = [
        (IDS["vwap"], "VWAP Over Time by Symbol", "lnsXY", _vwap_state(), ["vwap-layer"]),
        (IDS["volume"], "Volume Over Time by Symbol", "lnsXY", _volume_state(), ["volume-layer"]),
        (IDS["anomaly"], "Anomaly Events", "lnsXY", _anomaly_state(), ["anomaly-layer"]),
        (IDS["zscore"], "Z-Score Over Time by Symbol", "lnsXY", _zscore_state(), ["zscore-layer"]),
        (IDS["trades"], "Total Trades", "lnsMetric", _trades_state(), ["trades-layer"]),
    ]

    for vis_id, title, vis_type, state, layer_ids in vis_configs:
        refs = [{"type": "index-pattern", "id": DATA_VIEW_ID, "name": f"indexpattern-datasource-layer-{lid}"} for lid in layer_ids]
        objects.append({
            "id": vis_id,
            "type": "lens",
            "typeMigrationVersion": "8.9.0",
            "attributes": {"title": title, "description": "", "visualizationType": vis_type, "state": state, "references": refs},
            "references": refs,
        })

    panels = [
        {"version": "8.11.4", "type": "lens", "gridData": {"x": 0, "y": 0, "w": 48, "h": 15, "i": "p1"}, "panelIndex": "p1", "embeddableConfig": {"enhancements": {}}, "panelRefName": "panel_p1", "title": "VWAP Over Time by Symbol"},
        {"version": "8.11.4", "type": "lens", "gridData": {"x": 0, "y": 15, "w": 24, "h": 15, "i": "p2"}, "panelIndex": "p2", "embeddableConfig": {"enhancements": {}}, "panelRefName": "panel_p2", "title": "Volume Over Time by Symbol"},
        {"version": "8.11.4", "type": "lens", "gridData": {"x": 24, "y": 15, "w": 24, "h": 15, "i": "p3"}, "panelIndex": "p3", "embeddableConfig": {"enhancements": {}}, "panelRefName": "panel_p3", "title": "Anomaly Events"},
        {"version": "8.11.4", "type": "lens", "gridData": {"x": 0, "y": 30, "w": 36, "h": 12, "i": "p4"}, "panelIndex": "p4", "embeddableConfig": {"enhancements": {}}, "panelRefName": "panel_p4", "title": "Z-Score Over Time by Symbol"},
        {"version": "8.11.4", "type": "lens", "gridData": {"x": 36, "y": 30, "w": 12, "h": 12, "i": "p5"}, "panelIndex": "p5", "embeddableConfig": {"enhancements": {}}, "panelRefName": "panel_p5", "title": "Total Trades"},
    ]

    objects.append({
        "id": IDS["dashboard"],
        "type": "dashboard",
        "attributes": {
            "title": "STREAMSIGHT Real-Time Crypto Analytics",
            "description": "Real-time cryptocurrency analytics: VWAP, volume, Z-score anomaly detection.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "syncCursor": True, "syncTooltips": False, "hidePanelTitles": False}),
            "timeRestore": True,
            "timeTo": "now",
            "timeFrom": "now-1h",
            "refreshInterval": {"pause": False, "value": 10000},
            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})},
        },
        "references": [
            {"id": IDS["vwap"], "name": "panel_p1", "type": "lens"},
            {"id": IDS["volume"], "name": "panel_p2", "type": "lens"},
            {"id": IDS["anomaly"], "name": "panel_p3", "type": "lens"},
            {"id": IDS["zscore"], "name": "panel_p4", "type": "lens"},
            {"id": IDS["trades"], "name": "panel_p5", "type": "lens"},
        ],
    })

    with open(filepath, "w", encoding="utf-8") as f:
        for obj in objects:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")

    print(f"    Saved to {filepath}")

def main():
    print("=" * 60)
    print("  STREAMSIGHT — Kibana Dashboard Setup")
    print("=" * 60)

    export_only = "--export-only" in sys.argv
    do_reset = "--reset" in sys.argv

    ndjson_path = os.path.join(os.path.dirname(__file__) or ".", "kibana_dashboard.ndjson")
    generate_ndjson(ndjson_path)

    if export_only:
        print("\n--export-only: NDJSON file generated. Skipping API calls.")
        return

    if not wait_for_kibana():
        sys.exit(1)

    if do_reset:
        kibana_request("DELETE", f"/api/saved_objects/dashboard/{IDS['dashboard']}?force=true")
        kibana_request("DELETE", f"/api/data_views/data_view/{DATA_VIEW_ID}")

    create_data_view()
    create_dashboard()

    print("\nDone.")
    print(f"Open dashboard: {KIBANA_URL}/app/dashboards#/view/{IDS['dashboard']}")

if __name__ == "__main__":
    main()
