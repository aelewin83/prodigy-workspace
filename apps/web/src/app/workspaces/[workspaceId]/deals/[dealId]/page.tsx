import { DealWorkspaceClient } from '@/components/deal/deal-workspace-client';

type PageProps = {
  params: { workspaceId: string; dealId: string };
};

export default function WorkspaceDealPage({ params }: PageProps) {
  return <DealWorkspaceClient workspaceId={params.workspaceId} dealId={params.dealId} />;
}
