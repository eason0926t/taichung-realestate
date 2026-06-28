"use client";
import { useEffect, useRef, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const TAICHUNG_CENTER: [number, number] = [120.6736, 24.1477];

interface MapViewProps {
  onBoundsChange: (bbox: [number, number, number, number]) => void;
  onMarkerClick: (id: number) => void;
  listings: GeoJSON.FeatureCollection;
}

export default function MapView({ onBoundsChange, onMarkerClick, listings }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const mapReadyRef = useRef(false);

  const emitBounds = useCallback(
    (map: maplibregl.Map) => {
      const b = map.getBounds();
      if (!b) return;
      onBoundsChange([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
    },
    [onBoundsChange]
  );

  // Update map source whenever listings prop changes
  useEffect(() => {
    if (!mapReadyRef.current || !mapRef.current) return;
    const src = mapRef.current.getSource("listings") as maplibregl.GeoJSONSource | undefined;
    src?.setData(listings);
  }, [listings]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: TAICHUNG_CENTER,
      zoom: 12,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      // Switch all place-name layers to Traditional Chinese
      map.getStyle().layers.forEach((layer) => {
        if (layer.type === "symbol") {
          const tf = (layer as maplibregl.SymbolLayerSpecification).layout?.["text-field"];
          if (tf) {
            map.setLayoutProperty(layer.id, "text-field", [
              "coalesce",
              ["get", "name:zh-Hant"],
              ["get", "name:zh"],
              ["get", "name"],
            ]);
          }
        }
      });

      map.addSource("listings", {
        type: "geojson",
        data: listings,
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      // Cluster circles
      map.addLayer({
        id: "clusters",
        type: "circle",
        source: "listings",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "rgba(245,158,11,0.2)",
          "circle-stroke-color": "#f59e0b",
          "circle-stroke-width": 2,
          "circle-radius": ["step", ["get", "point_count"], 20, 10, 30, 50, 40],
        },
      });

      // Cluster count labels
      map.addLayer({
        id: "cluster-count",
        type: "symbol",
        source: "listings",
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-size": 13,
          "text-font": ["Noto Sans Bold", "Arial Unicode MS Bold"],
        },
        paint: { "text-color": "#fbbf24" },
      });

      // Individual gold price bubbles
      map.addLayer({
        id: "unclustered-point",
        type: "symbol",
        source: "listings",
        filter: ["!", ["has", "point_count"]],
        layout: {
          "text-field": [
            "concat",
            ["case",
              [">=", ["get", "price"], 100000000],
              ["concat", ["to-string", ["round", ["/", ["get", "price"], 100000000]]], "億"],
              ["concat", ["to-string", ["round", ["/", ["get", "price"], 10000]]], "萬"],
            ],
          ],
          "text-size": 12,
          "text-font": ["Noto Sans Bold", "Arial Unicode MS Bold"],
          "text-padding": 4,
        },
        paint: {
          "text-color": "#ffffff",
          "text-halo-color": "#d97706",
          "text-halo-width": 8,
        },
      });

      // Click individual marker
      map.on("click", "unclustered-point", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (id) onMarkerClick(Number(id));
      });

      // Click cluster → zoom in
      map.on("click", "clusters", (e) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const clusterId = feature.properties?.cluster_id;
        (map.getSource("listings") as maplibregl.GeoJSONSource).getClusterExpansionZoom(
          clusterId,
          (err, zoom) => {
            if (err || !zoom) return;
            map.easeTo({
              center: (feature.geometry as GeoJSON.Point).coordinates as [number, number],
              zoom,
            });
          }
        );
      });

      map.on("moveend", () => emitBounds(map));

      mapReadyRef.current = true;
      emitBounds(map);
    });

    mapRef.current = map;
    return () => {
      mapReadyRef.current = false;
      map.remove();
      mapRef.current = null;
    };
  }, [emitBounds, onMarkerClick]); // listings intentionally excluded — handled by the other useEffect

  return (
    <div
      ref={containerRef}
      style={{ position: "fixed", inset: 0, width: "100vw", height: "100vh" }}
    />
  );
}
