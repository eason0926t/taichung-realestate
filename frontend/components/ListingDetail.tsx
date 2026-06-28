"use client";
import { useRouter } from "next/navigation";
import type { ListingFeature } from "@/lib/types";
import { formatPrice } from "@/lib/api";

interface ListingDetailProps {
  listing: ListingFeature;
}

export default function ListingDetail({ listing }: ListingDetailProps) {
  const router = useRouter();
  const p = listing.properties;

  const stats = [
    { label: "坪數", value: p.area_ping ? `${p.area_ping}坪` : "—" },
    { label: "格局", value: p.rooms ? `${p.rooms}房` : "—" },
    { label: "樓層", value: p.floor ? `${p.floor}F` : "—" },
    { label: "單價", value: p.unit_price ? `${p.unit_price}萬/坪` : "—" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)", padding: "0 0 40px" }}>
      <div style={{
        position: "sticky", top: 0, zIndex: 10,
        display: "flex", alignItems: "center",
        padding: "12px 16px", gap: 12,
        background: "rgba(20,17,16,0.95)", backdropFilter: "blur(8px)",
        borderBottom: "1px solid var(--border-gold)",
      }}>
        <button
          onClick={() => router.back()}
          style={{ background: "none", border: "none", color: "var(--gold)", fontSize: 14, cursor: "pointer", padding: 0 }}
        >
          ← 返回地圖
        </button>
        <span style={{ flex: 1 }} />
        <a href={p.url} target="_blank" rel="noopener noreferrer"
          style={{ color: "var(--text-secondary)", fontSize: 12 }}>
          原始頁面 ↗
        </a>
      </div>

      <div style={{
        width: "100%", height: 240,
        background: "var(--bg-secondary)",
        display: "flex", alignItems: "center", justifyContent: "center",
        overflow: "hidden",
      }}>
        {p.photo
          ? <img src={p.photo} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : <span style={{ fontSize: 48 }}>🏠</span>
        }
      </div>

      <div style={{ padding: "20px 16px" }}>
        <div style={{ color: "var(--gold)", fontSize: 28, fontWeight: 700, marginBottom: 6 }}>
          {formatPrice(p.price)}
        </div>
        <div style={{ color: "var(--text-primary)", fontSize: 14, marginBottom: 16 }}>
          {p.district} · {p.title ?? ""}
        </div>

        <div style={{ marginBottom: 20 }}>
          <span style={{
            background: "rgba(245,158,11,0.1)", border: "1px solid var(--border-gold)",
            borderRadius: 8, padding: "4px 12px", fontSize: 12, color: "var(--gold-dark)",
          }}>
            來源：{p.source}
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 24 }}>
          {stats.map(s => (
            <div key={s.label} style={{
              background: "rgba(245,158,11,0.06)",
              border: "1px solid rgba(245,158,11,0.2)",
              borderRadius: 10, padding: "12px 14px",
            }}>
              <div style={{ color: "var(--gold)", fontSize: 16, fontWeight: 700 }}>{s.value}</div>
              <div style={{ color: "var(--text-secondary)", fontSize: 11, marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>

        <a
          href={p.url}
          target="_blank"
          rel="noopener noreferrer"
          className="gold-btn"
          style={{ display: "block", textAlign: "center", textDecoration: "none", fontSize: 15 }}
        >
          前往房仲網站聯絡
        </a>
      </div>
    </div>
  );
}
