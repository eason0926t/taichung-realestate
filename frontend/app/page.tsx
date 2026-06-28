"use client";
import { useState, useCallback } from "react";
import dynamic from "next/dynamic";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function HomePage() {
  const [bbox, setBbox] = useState<[number, number, number, number] | null>(null);

  const handleBoundsChange = useCallback((b: [number, number, number, number]) => {
    setBbox(b);
  }, []);

  const handleMarkerClick = useCallback((id: number) => {
    console.log("clicked listing", id);
  }, []);

  return (
    <main>
      <MapView onBoundsChange={handleBoundsChange} onMarkerClick={handleMarkerClick} />
      {bbox && (
        <div style={{
          position: "fixed", top: 8, left: 8,
          background: "rgba(28,25,23,0.8)", color: "#a8a29e",
          padding: "4px 8px", borderRadius: 4, fontSize: 11, zIndex: 10
        }}>
          bbox: {bbox.map(n => n.toFixed(3)).join(", ")}
        </div>
      )}
    </main>
  );
}
