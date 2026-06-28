// frontend/lib/types.ts
export interface ListingFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] } | null;
  properties: {
    id: number;
    source: string;
    url: string;
    title: string | null;
    price: number | null;
    unit_price: number | null;
    area_ping: number | null;
    rooms: number | null;
    floor: number | null;
    district: string | null;
    photo: string | null;
  };
}

export interface PriceFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: number;
    district: string | null;
    price: number | null;
    unit_price: number | null;
    area_ping: number | null;
    building_type: string | null;
    transaction_date: string | null;
  };
}

export interface FeatureCollection<T> {
  type: "FeatureCollection";
  features: T[];
}
