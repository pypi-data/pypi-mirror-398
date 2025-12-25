import { Suspense } from "react"
import { AppLayout } from "@/components/layout/app-layout"
import { RunsDashboard } from "@/components/runs/dashboard"

export default function RunsPage() {
  return (
    <AppLayout>
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Runs</h1>
          <p className="text-sm text-muted-foreground mt-1">Monitor and analyze simulated persona interactions</p>
        </div>
        <Suspense fallback={<div className="text-muted-foreground">Loading...</div>}>
          <RunsDashboard />
        </Suspense>
      </div>
    </AppLayout>
  )
}

