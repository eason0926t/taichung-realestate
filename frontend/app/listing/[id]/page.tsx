import { fetchListing } from "@/lib/api";
import ListingDetail from "@/components/ListingDetail";

export default async function ListingPage({ params }: { params: { id: string } }) {
  const listing = await fetchListing(Number(params.id));
  return <ListingDetail listing={listing} />;
}
