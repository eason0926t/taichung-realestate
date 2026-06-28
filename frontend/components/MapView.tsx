"use client";
import { useEffect, useRef, useCallback } from "react";
import mapboxgl from "mapbox-gl";

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

const TAICHUNG_CENTER: [number, number] = [120.6736, 24.1477];

interface MapViewProps {
  onBoundsChange: (bbox: [number, number, number, number]) => void;
  onMarkerClick: (id: number) => void;
}

export default function MapView({ onBoundsChange, onMarkerClick }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  const emitBounds = useCallback(
    (map: mapboxgl.Map) => {
      const b = map.getBounds();
      if (!b) return;
      onBoundsChange([
        b.getWest(), b.getSouth(), b.getEast(), b.getNorth(),
      ]);
    },
    [onBoundsChange]
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: TAICHUNG_CENTER,
      zoom: 12,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("load", () => {
      emitBounds(map);

      map.addSource("listings", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50,
      });

      // Cluster circles (zoomed out)
      map.addLayer({
        id: "clusters",
        type: "circle",
        source: "listings",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "rgba(245,158,11,0.2)",
          "circle-stroke-color": "#f59e0b",
          "circle-stroke-width": 2,
          "circle-radius": [
            "step", ["get", "point_count"], 20, 10, 30, 50, 40
          ],
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
          "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
        },
        paint: { "text-color": "#fbbf24" },
      });

      // Individual gold price bubbles (zoomed in)
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
              ["concat",
                ["to-string", ["round", ["/", ["get", "price"], 100000000]]],
                "億"
              ],
              ["concat",
                ["to-string", ["round", ["/", ["get", "price"], 10000]]],
                "萬"
              ]
            ]
          ],
          "text-size": 11,
          "text-font": ["DIN Offc Pro Bold", "Arial Unicode MS Bold"],
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
        const feature = e.features?.[0];
        const id = feature?.properties?.id;
        if (id) onMarkerClick(Number(id));
      });

      // Click cluster → zoom in
      map.on("click", "clusters", (e) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const clusterId = feature.properties?.cluster_id;
        (map.getSource("listings") as mapboxgl.GeoJSONSource)
          .getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err || !zoom) return;
            map.easeTo({
              center: (feature.geometry as GeoJSON.Point).coordinates as [number, number],
              zoom,
            });
          });
      });

      map.on("moveend", () => emitBounds(map));
    });

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, [emitBounds, onMarkerClick]);

  // Expose method to update listings source from outside
  (MapView as any).updateListings = (geojson: GeoJSON.FeatureCollection) => {
    const src = mapRef.current?.getSource("listings") as mapboxgl.GeoJSONSource;
    src?.setData(geojson);
  };

  return (
    <div
      ref={containerRef}
      style={{ position: "fixed", inset: 0, width: "100vw", height: "100vh" }}
    />
  );
}
