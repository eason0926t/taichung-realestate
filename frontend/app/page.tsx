"use client";
import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import SearchBar from "@/components/SearchBar";
import BottomCardRail from "@/components/BottomCardRail";
import BottomSheet from "@/components/BottomSheet";
import { fetchListings, fetchListing } from "@/lib/api";
import type { ListingFeature } from "@/lib/types";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function HomePage() {
  const [listings, setListings] = useState<ListingFeature[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [sheetListing, setSheetListing] = useState<ListingFeature | null>(null);

  const loadListings = useCallback(async (b: [number, number, number, number]) => {
    try {
      const data = await fetchListings(b);
      setListings(data.features);
      const MapViewModule = await import("@/components/MapView");
      (MapViewModule.default as any).updateListings?.(data);
    } catch (e) {
      console.error("listings fetch error", e);
    }
  }, []);

  const handleBoundsChange = useCallback((b: [number, number, number, number]) => {
    loadListings(b);
  }, [loadListings]);

  const handleMarkerClick = useCallback(async (id: number) => {
    setSelectedId(id);
    try {
      const listing = await fetchListing(id);
      setSheetListing(listing);
    } catch (e) {
      console.error("listing fetch error", e);
    }
  }, []);

  return (
    <main>
      <MapView
        onBoundsChange={handleBoundsChange}
        onMarkerClick={handleMarkerClick}
      />
      <SearchBar
        onSearch={() => {}}
        onFilterOpen={() => {}}
      />
      <BottomCardRail
        listings={listings}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />
      <BottomSheet
        listing={sheetListing}
        onClose={() => setSheetListing(null)}
      />
    </main>
  );
}
