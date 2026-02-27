import { notFound } from 'next/navigation';

import { DealDetailClient } from '@/components/deal/deal-detail-client';
import { getDeal } from '@/lib/mock-data';

type PageProps = {
  params: { id: string };
  searchParams: { tab?: string };
};

export default function DealDetailPage({ params, searchParams }: PageProps) {
  const deal = getDeal(params.id);
  if (!deal) notFound();

  return <DealDetailClient deal={deal} initialTab={searchParams.tab ?? 'overview'} />;
}
