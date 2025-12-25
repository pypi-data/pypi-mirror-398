"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader, Plus, Trash2, RefreshCw } from "lucide-react"
import { toast } from "sonner"
import { scenarioApi, crawlerApi } from "@/lib/api-client"
import { Scenario } from "@/types/api"
import { ScenarioPersonasModal } from "@/components/scenarios/scenario-personas-modal"
import { useExecutions } from "@/contexts/execution-context"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export default function ScenariosPage() {
  const router = useRouter()
  const { activeExecutions, startExecution, refreshExecutions, onExecutionComplete } = useExecutions()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)
  const [showTasksModal, setShowTasksModal] = useState(false)
  const [reindexingScenarioIds, setReindexingScenarioIds] = useState<Set<string>>(new Set())

  // Get status for a specific scenario
  const getScenarioStatus = (scenarioId: string) => {
    return activeExecutions.find(e => e.scenario_id === scenarioId && e.status === "in_progress")
  }

  // Fetch scenarios function (used on mount and after execution completes)
  const fetchScenarios = useCallback(async () => {
    try {
      const data = await scenarioApi.list()
      setScenarios(data)
      return data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to fetch scenarios"
      toast.error(errorMessage)
      return []
    }
  }, [])

  // Fetch scenarios on mount
  useEffect(() => {
    const loadScenarios = async () => {
      setLoading(true)
      const data = await fetchScenarios()

      // Auto-redirect to new scenario page if empty
      if (data.length === 0) {
        router.push("/scenarios/new")
      }
      setLoading(false)
    }

    loadScenarios()
  }, [router, fetchScenarios])

  // Auto-refresh scenarios when executions complete (e.g., reindexing finishes)
  useEffect(() => {
    const unsubscribe = onExecutionComplete(() => {
      // Refresh scenarios to get updated task data after reindexing or execution completes
      fetchScenarios()
    })

    return unsubscribe
  }, [onExecutionComplete, fetchScenarios])

  const handleViewDetails = async (scenario: Scenario) => {
    console.log("handleViewDetails called with scenario:", scenario)
    try {
      console.log("Fetching scenario with ID:", scenario.id)
      const fullScenario = await scenarioApi.get(scenario.id)
      console.log("Received full scenario:", fullScenario)
      setEditingScenario(fullScenario)
      setShowTasksModal(true)
      console.log("Modal should now be open")
    } catch (error) {
      console.error("Error in handleViewDetails:", error)
      const errorMessage = error instanceof Error ? error.message : "Failed to load scenario"
      toast.error(errorMessage)
    }
  }

  const handleScenarioUpdate = async () => {
    try {
      const data = await scenarioApi.list()
      setScenarios(data)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to refresh scenarios"
      toast.error(errorMessage)
    }
  }

  const handleScenarioDelete = (scenarioId: string) => {
    setScenarios(scenarios.filter((s) => s.id !== scenarioId))
  }

  const handleDelete = async (id: string) => {
    setDeleting(id)
    try {
      await scenarioApi.delete(id)
      setScenarios(scenarios.filter((s) => s.id !== id))
      toast.success("Scenario deleted successfully")
      setDeleteId(null)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to delete scenario"
      toast.error(errorMessage)
    } finally {
      setDeleting(null)
    }
  }

  const handleRunScenario = async (scenario: Scenario) => {
    try {
      await startExecution(scenario.id)
    } catch (error) {
      // Error handling is done in the context
    }
  }

  const handleReindex = async (scenario: Scenario) => {
    try {
      setReindexingScenarioIds(prev => new Set(prev).add(scenario.id))

      await crawlerApi.analyze({
        scenario_id: scenario.id,
        website_url: scenario.website_url,
        description: scenario.description || "",
        name: scenario.name,
        metrics: scenario.metrics || [],
        email: scenario.email || "",
      })

      toast.success("Reindexing started", {
        description: "Check the status bar below for progress"
      })

      await refreshExecutions()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to start reindexing"
      toast.error("Failed to start reindexing", {
        description: errorMessage,
      })
    } finally {
      setReindexingScenarioIds(prev => {
        const next = new Set(prev)
        next.delete(scenario.id)
        return next
      })
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="p-6">
          <div className="flex items-center justify-center py-12">
            <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading scenarios...</span>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="p-6">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Scenarios</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Manage your scenarios and create new ones
              </p>
            </div>
            <Button onClick={() => router.push("/scenarios/new")} className="gap-2">
              <Plus className="w-4 h-4" />
              Create New Scenario
            </Button>
          </div>
        </div>


        {scenarios.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">No scenarios yet</p>
              <Button onClick={() => router.push("/scenarios/new")}>
                Create Your First Scenario
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scenarios.map((scenario) => (
              <Card key={scenario.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-lg text-foreground truncate">
                        {scenario.name}
                      </h3>
                      <p className="text-sm text-muted-foreground truncate mt-1">
                        {scenario.website_url}
                      </p>
                    </div>

                    {!scenario.tasks?.length && (
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Loader className="w-3 h-3 animate-spin" />
                        Reindexing...
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                      Created {new Date(scenario.created_at).toLocaleDateString()}
                    </p>

                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReindex(scenario)}
                        disabled={reindexingScenarioIds.has(scenario.id)}
                      >
                        {reindexingScenarioIds.has(scenario.id) ? (
                          <>
                            <Loader className="w-4 h-4 mr-2 animate-spin" />
                            Reindexing...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Reindex
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleViewDetails(scenario)}
                      >
                        View Details
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteId(scenario.id)}
                        disabled={deleting === scenario.id}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        {deleting === scenario.id ? (
                          <Loader className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </Button>
                    </div>

                    {(() => {
                      const status = getScenarioStatus(scenario.id)
                      if (!status) return null
                      return (
                        <div className="mt-2 text-xs text-muted-foreground">
                          Progress: {status.completed_tasks + status.failed_tasks}/{status.total_tasks} tasks
                        </div>
                      )
                    })()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Scenario</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this scenario? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex gap-3 justify-end">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteId && handleDelete(deleteId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Scenario Modal */}
      <ScenarioPersonasModal
        open={showTasksModal}
        onOpenChange={(open) => {
          setShowTasksModal(open)
          if (!open) {
            setEditingScenario(null)
          }
        }}
        mode="edit"
        scenario={editingScenario || undefined}
        onUpdate={handleScenarioUpdate}
        onDelete={handleScenarioDelete}
        onRun={handleRunScenario}
      />
    </AppLayout>
  )
}
