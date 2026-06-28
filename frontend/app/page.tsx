"use client";
import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import SearchBar from "@/components/SearchBar";
import BottomCardRail from "@/components/BottomCardRail";
import BottomSheet from "@/components/BottomSheet";
import { fetchListings, fetchListing } from "@/lib/api";
import type { ListingFeature, FeatureCollection } from "@/lib/types";

const EMPTY_FC: FeatureCollection<ListingFeature> = { type: "FeatureCollection", features: [] };

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function HomePage() {
  const [listingsFC, setListingsFC] = useState<FeatureCollection<ListingFeature>>(EMPTY_FC);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [sheetListing, setSheetListing] = useState<ListingFeature | null>(null);

  const openSheet = useCallback(async (id: number) => {
    setSelectedId(id);
    try {
      const listing = await fetchListing(id);
      setSheetListing(listing);
    } catch (e) {
      console.error("listing fetch error", e);
    }
  }, []);

  const handleBoundsChange = useCallback(async (b: [number, number, number, number]) => {
    try {
      const data = await fetchListings(b);
      setListingsFC(data);
    } catch (e) {
      console.error("listings fetch error", e);
    }
  }, []);

  return (
    <main>
      <MapView
        listings={listingsFC}
        onBoundsChange={handleBoundsChange}
        onMarkerClick={openSheet}
      />
      <SearchBar onSearch={() => {}} onFilterOpen={() => {}} />
      <BottomCardRail
        listings={listingsFC.features}
        selectedId={selectedId}
        onSelect={openSheet}
      />
      <BottomSheet
        listing={sheetListing}
        onClose={() => setSheetListing(null)}
      />
    </main>
  );
}
