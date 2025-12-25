"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Loader } from "lucide-react"
import { reportApi, scenarioApi } from "@/lib/api-client"
import { FrictionHotspots } from "@/components/runs/friction-hotspots"
import { ReportListItem, ReportAggregate, Scenario, FrictionHotspotItem } from "@/types/api"
import { JourneySankey } from "./journey-sankey"
import { RunFilters } from "@/components/runs/run-filters"
import { useFilterContext } from "@/contexts/filter-context"
import { FrictionDetailModal } from "./friction-detail-modal"
import { EmptyState } from "@/components/ui/empty-state"

export function ReportsDashboard() {
  const router = useRouter()
  const {
    scenarioFilter,
    reportFilter,
    statusFilter,
    personaFilter,
    platformFilter
  } = useFilterContext()

  // State for data fetching
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [reportList, setReportList] = useState<ReportListItem[]>([])
  const [selectedReportData, setSelectedReportData] = useState<ReportAggregate | null>(null)

  const [friction, setFriction] = useState<FrictionHotspotItem[]>([])
  const [availablePersonas, setAvailablePersonas] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingAggregate, setLoadingAggregate] = useState(false)
  const [frictionLoading, setFrictionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFrictionNode, setSelectedFrictionNode] = useState<any>(null)

  // Fetch report list, scenarios and personas on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [reportsData, scenariosData, personasData] = await Promise.all([
          reportApi.list(),
          scenarioApi.list(),
          scenarioApi.getPersonas(),
        ])
        setReportList(reportsData)
        setScenarios(scenariosData)
        setAvailablePersonas(personasData.personas.sort())
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch reports")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Fetch aggregated data (SERVER SIDE FILTERED) and runs when report or filters change
  useEffect(() => {
    // If "all reports" selected but no scenario selected, we can't show aggregation
    if ((!reportFilter || reportFilter === "all") && scenarioFilter === "all") {
      setSelectedReportData(null)
      return
    }

    // If no report selected at all, return
    if (!reportFilter) {
      setSelectedReportData(null)
      return
    }

    const fetchReportData = async () => {
      try {
        setLoadingAggregate(true)

        // Prepare filters for API
        const filters = {
          persona: personaFilter,
          status: statusFilter,
          platform: platformFilter,
          scenario: scenarioFilter
        }

        setFrictionLoading(true)
        // Fetch aggregated data and friction in parallel
        const [aggregateData, frictionData] = await Promise.all([
          reportApi.getAggregate(reportFilter, "compact", filters),
          reportApi.getFriction(reportFilter !== "all" ? reportFilter : undefined, scenarioFilter !== "all" ? scenarioFilter : undefined)
        ])

        setSelectedReportData(aggregateData)
        setFriction(frictionData)

      } catch (err) {
        // Handle 404 gracefully - likely stale filter, don't show error
        // Just clear the report data which will show "no data" message
        console.warn('[ReportsDashboard] Error fetching report data:', err)
        setSelectedReportData(null)
        setFriction([])
        // Don't set global error for aggregate failures - the filter validation will handle it
      } finally {
        setLoadingAggregate(false)
        setFrictionLoading(false)
      }
    }

    fetchReportData()
  }, [reportFilter, scenarioFilter, personaFilter, statusFilter, platformFilter])

  // Determine empty state content based on context
  const getEmptyStateContent = () => {
    // No scenarios exist at all - user needs to create one first
    if (scenarios.length === 0) {
      return {
        title: "No scenarios yet",
        description: "Create a scenario to start testing personas on your website",
        variant: "no-data" as const,
        action: {
          label: "Create Scenario",
          onClick: () => router.push('/scenarios/new')
        }
      }
    }

    // Scenarios exist but no reports yet
    if (reportList.length === 0) {
      return {
        title: "No reports yet",
        description: "Run some persona tests to generate reports",
        variant: "no-data" as const
      }
    }

    // Reports exist but no scenario selected
    if ((!reportFilter || reportFilter === "all") && scenarioFilter === "all") {
      return {
        title: "Select a scenario to view journey analysis",
        description: `${scenarios.length} scenario${scenarios.length !== 1 ? 's' : ''} available`,
        variant: "default" as const
      }
    }

    // Scenario/report selected but no data returned
    return {
      title: "No data available",
      description: "No data matches your current filters. Try selecting a different scenario or report.",
      variant: "no-results" as const
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading reports...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-200">Error: {error}</p>
      </div>
    )
  }

  // Always show filters, even when no reports exist
  return (
    <div className="space-y-6">

      {/* Unified Filters - ALWAYS visible */}
      <RunFilters
        scenarios={scenarios}
        reports={reportList}
        availablePersonas={availablePersonas}
        showPlatformFilter={true}
        showDateFilter={false}
      />

      {/* Main Content - conditional based on state */}
      {loadingAggregate ? (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading analysis...</span>
        </div>
      ) : selectedReportData ? (
        <>
          {/* Report Header */}
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-foreground">{selectedReportData.scenario_name}</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {selectedReportData.report_id && selectedReportData.report_id !== "all" ? (
                <>Report ID: {selectedReportData.report_id.substring(0, 8)}... • </>
              ) : (
                <>All Reports • </>
              )}
              Analysis based on {selectedReportData.run_count} filtered runs
            </p>
          </div>

          {/* Metrics Summary */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Metrics Summary</h3>
            {selectedReportData.run_count === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No data matches the selected filters</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Runs</p>
                  <p className="text-2xl font-bold text-foreground">{selectedReportData.metrics_summary.total_runs}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold text-green-600">{selectedReportData.metrics_summary.sucessfull_runs}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Goal Not Met</p>
                  <p className="text-2xl font-bold text-amber-600">{selectedReportData.metrics_summary.failed_runs}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Error</p>
                  <p className="text-2xl font-bold text-red-600">{selectedReportData.metrics_summary.error_runs}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-bold text-foreground">
                    {(selectedReportData.metrics_summary.success_rate * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            )}
          </Card>

          {/* Journey Sankey Diagram */}
          {selectedReportData.run_count > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Journey Flow</h3>
              <JourneySankey
                data={selectedReportData.journey_sankey}
                onNodeClick={(node) => setSelectedFrictionNode(node)}
              />
            </Card>
          )}

          {/* Friction Hotspots */}
          <FrictionHotspots hotspots={friction} loading={frictionLoading} />
        </>
      ) : (
        // Show appropriate empty state based on context
        <EmptyState {...getEmptyStateContent()} />
      )}

      {/* Friction Detail Modal */}
      <FrictionDetailModal
        node={selectedFrictionNode}
        onClose={() => setSelectedFrictionNode(null)}
      />
    </div>
  )
}


