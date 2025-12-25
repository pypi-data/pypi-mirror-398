import { AppLayout } from "@/components/layout/app-layout"
import { AnalyticsDashboard } from "@/components/analytics/dashboard"

export default function AnalyticsPage() {
  return (
    <AppLayout>
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">Key metrics from your agent simulations</p>
        </div>
        <AnalyticsDashboard />
      </div>
    </AppLayout>
  )
}
