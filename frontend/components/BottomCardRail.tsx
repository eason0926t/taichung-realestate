"use client";
import { useRef } from "react";
import type { ListingFeature } from "@/lib/types";
import { formatPrice } from "@/lib/api";

interface BottomCardRailProps {
  listings: ListingFeature[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export default function BottomCardRail({
  listings, selectedId, onSelect,
}: BottomCardRailProps) {
  const railRef = useRef<HTMLDivElement>(null);

  if (!listings.length) return null;

  return (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 20,
      background: "rgba(20,17,16,0.95)",
      backdropFilter: "blur(12px)",
      borderTop: "1px solid var(--border-gold)",
      padding: "10px 12px 16px",
    }}>
      <p style={{ color: "var(--text-secondary)", fontSize: 12, margin: "0 0 8px" }}>
        {listings.length} 筆物件 — 左右滑動
      </p>
      <div
        ref={railRef}
        style={{
          display: "flex", gap: 10, overflowX: "auto",
          scrollSnapType: "x mandatory", paddingBottom: 4,
        }}
      >
        {listings.map(f => {
          const p = f.properties;
          const isSelected = p.id === selectedId;
          return (
            <div
              key={p.id}
              onClick={() => onSelect(p.id)}
              style={{
                minWidth: 140, maxWidth: 140, scrollSnapAlign: "start",
                background: isSelected ? "rgba(245,158,11,0.1)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${isSelected ? "var(--gold)" : "rgba(255,255,255,0.08)"}`,
                borderTop: isSelected ? "2px solid var(--gold)" : "2px solid transparent",
                borderRadius: 10, padding: "8px 10px", cursor: "pointer",
                transition: "border 0.15s",
              }}
            >
              {p.photo && (
                <img
                  src={p.photo}
                  alt=""
                  style={{ width: "100%", height: 60, objectFit: "cover",
                    borderRadius: 6, marginBottom: 6 }}
                  onError={e => (e.currentTarget.style.display = "none")}
                />
              )}
              <div style={{ color: "var(--text-secondary)", fontSize: 10, marginBottom: 2 }}>
                {p.district} {p.rooms ? `${p.rooms}房` : ""} {p.area_ping ? `${p.area_ping}坪` : ""}
              </div>
              <div style={{ color: "var(--gold)", fontSize: 14, fontWeight: 700 }}>
                {formatPrice(p.price)}
              </div>
              <div style={{ color: "#6b7280", fontSize: 10, marginTop: 2 }}>
                {p.source}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
