"use client";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { ListingFeature } from "@/lib/types";
import { formatPrice } from "@/lib/api";

interface BottomSheetProps {
  listing: ListingFeature | null;
  onClose: () => void;
}

export default function BottomSheet({ listing, onClose }: BottomSheetProps) {
  const router = useRouter();
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!listing) return;
    const handler = (e: MouseEvent) => {
      if (sheetRef.current && !sheetRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    setTimeout(() => document.addEventListener("mousedown", handler), 0);
    return () => document.removeEventListener("mousedown", handler);
  }, [listing, onClose]);

  if (!listing) return null;
  const p = listing.properties;

  return (
    <div
      ref={sheetRef}
      style={{
        position: "fixed", bottom: 110, left: 12, right: 12, zIndex: 30,
        background: "rgba(20,17,16,0.98)",
        border: "1px solid var(--border-gold)",
        borderRadius: 16, padding: 16,
        boxShadow: "0 -8px 40px rgba(0,0,0,0.5)",
        animation: "slideUp 0.2s ease",
      }}
    >
      <style>{`@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`}</style>

      <div style={{ width: 40, height: 3, background: "#44403c", borderRadius: 2, margin: "0 auto 14px" }} />

      <div style={{ display: "flex", gap: 12 }}>
        <div style={{
          width: 90, height: 90, flexShrink: 0,
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-gold)",
          borderRadius: 10, overflow: "hidden",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {p.photo
            ? <img src={p.photo} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            : <span style={{ fontSize: 28 }}>🏠</span>
          }
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ color: "var(--gold)", fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
            {formatPrice(p.price)}
            {p.unit_price && (
              <span style={{ color: "var(--text-secondary)", fontSize: 11, fontWeight: 400, marginLeft: 6 }}>
                {p.unit_price}萬/坪
              </span>
            )}
          </div>
          <div style={{ color: "var(--text-primary)", fontSize: 12, marginBottom: 8 }}>
            {p.district} {p.rooms ? `${p.rooms}房` : ""} {p.area_ping ? `${p.area_ping}坪` : ""}
            {p.floor ? ` · ${p.floor}F` : ""}
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <span style={{
              background: "rgba(245,158,11,0.1)", border: "1px solid var(--border-gold)",
              borderRadius: 6, padding: "2px 8px", fontSize: 10, color: "var(--gold-dark)"
            }}>
              {p.source}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button
          onClick={() => router.push(`/listing/${p.id}`)}
          className="gold-btn"
          style={{ flex: 1, border: "none", fontSize: 13 }}
        >
          查看詳情
        </button>
        <button
          onClick={onClose}
          style={{
            flex: 1, background: "rgba(255,255,255,0.06)",
            border: "1px solid var(--border-gold)",
            color: "var(--text-secondary)", borderRadius: 8,
            padding: "8px 16px", fontSize: 13, cursor: "pointer",
          }}
        >
          關閉
        </button>
      </div>
    </div>
  );
}
