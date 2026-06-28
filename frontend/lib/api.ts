// frontend/lib/api.ts
import type { ListingFeature, PriceFeature, FeatureCollection } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchListings(
  bbox: [number, number, number, number],
  params: Record<string, string | number> = {}
): Promise<FeatureCollection<ListingFeature>> {
  const qs = new URLSearchParams({
    bbox: bbox.join(","),
    ...Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)])),
  });
  const res = await fetch(`${API}/api/listings?${qs}`);
  if (!res.ok) throw new Error(`listings fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchListing(id: number): Promise<ListingFeature> {
  const res = await fetch(`${API}/api/listings/${id}`);
  if (!res.ok) throw new Error(`listing ${id} not found`);
  return res.json();
}

export async function fetchPrices(
  bbox: [number, number, number, number]
): Promise<FeatureCollection<PriceFeature>> {
  const qs = new URLSearchParams({ bbox: bbox.join(",") });
  const res = await fetch(`${API}/api/prices?${qs}`);
  if (!res.ok) throw new Error(`prices fetch failed: ${res.status}`);
  return res.json();
}

export function formatPrice(price: number | null): string {
  if (!price) return "—";
  const wan = Math.round(price / 10000);
  return wan >= 10000
    ? `${(wan / 10000).toFixed(1)}億`
    : `${wan.toLocaleString()}萬`;
}
