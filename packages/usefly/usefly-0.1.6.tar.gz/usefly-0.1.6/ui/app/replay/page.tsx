import { AppLayout } from "@/components/layout/app-layout"
import { ReplayPlayer } from "@/components/replay/player"

export default function ReplayPage() {
  return (
    <AppLayout>
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Agent Replay</h1>
          <p className="text-sm text-muted-foreground mt-1">Watch how agents interact with your app</p>
        </div>
        <ReplayPlayer />
      </div>
    </AppLayout>
  )
}
