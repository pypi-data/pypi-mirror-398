import { Suspense } from "react"
import { AppLayout } from "@/components/layout/app-layout"
import { ReportsDashboard } from "@/components/reports/dashboard"

export default function ReportsPage() {
  return (
    <AppLayout>
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Reports</h1>
          <p className="text-sm text-muted-foreground mt-1">
            View and analyze your completed reports
          </p>
        </div>
        <Suspense fallback={<div className="text-muted-foreground">Loading...</div>}>
          <ReportsDashboard />
        </Suspense>
      </div>
    </AppLayout>
  )
}
