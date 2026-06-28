import { fetchListing } from "@/lib/api";
import ListingDetail from "@/components/ListingDetail";

export default async function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const listing = await fetchListing(Number(id));
  return <ListingDetail listing={listing} />;
}
