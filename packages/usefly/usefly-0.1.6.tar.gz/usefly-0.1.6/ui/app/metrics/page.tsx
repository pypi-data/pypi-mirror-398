import { AppLayout } from "@/components/layout/app-layout"
import { StarterPackCatalog } from "@/components/metrics/starter-pack-catalog"

export default function MetricsPage() {
  return (
    <AppLayout>
      <div className="p-6">
        <StarterPackCatalog />
      </div>
    </AppLayout>
  )
}
