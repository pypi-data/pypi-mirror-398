"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { AlertTriangle } from "lucide-react"
import { useState } from "react"
import { personaRecordsApi } from "@/lib/api-client"
import { PersonaRun } from "@/types/api"
import { RunDetailsModal } from "@/components/runs/run-details-modal"

interface FrictionDetailModalProps {
  node: any | null
  onClose: () => void
}

export function FrictionDetailModal({ node, onClose }: FrictionDetailModalProps) {
  const [selectedRun, setSelectedRun] = useState<PersonaRun | null>(null)
  const [loadingRun, setLoadingRun] = useState(false)

  if (!node || !node.hasFriction) {
    return null
  }

  const handleViewRun = async (runId: string) => {
    try {
      setLoadingRun(true)
      const run = await personaRecordsApi.get(runId)
      setSelectedRun(run)
    } catch (error) {
      console.error("Failed to load run details:", error)
    } finally {
      setLoadingRun(false)
    }
  }

  return (
    <>
      <Dialog open={!!node} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold flex items-center gap-2">
              <AlertTriangle className={`h-5 w-5 ${
                node.frictionSeverity === 'high' ? 'text-red-600' : 'text-amber-600'
              }`} />
              Friction Details
            </DialogTitle>
            <p className="text-sm text-muted-foreground mt-2 break-all">
              {node.decodedId || node.displayName || node.id}
            </p>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            {/* Summary */}
            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-amber-900 dark:text-amber-200">
                  {node.friction_count} failure{node.friction_count !== 1 ? 's' : ''} at this location
                </h3>
                <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                  {node.friction_impact ? `${(node.friction_impact * 100).toFixed(0)}%` : '—'} of all failures
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Users encountered issues at this step in their journey, preventing them from completing their goal.
              </p>
            </div>

            {/* Failure Reasons */}
            {node.friction_reasons && node.friction_reasons.length > 0 && (
              <div>
                <h3 className="font-semibold text-foreground mb-3">Failure Reasons</h3>
                <div className="space-y-2">
                  {node.friction_reasons.map((reason: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-start justify-between p-3 bg-card border rounded-lg hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">{reason.reason}</p>
                      </div>
                      <div className="ml-4 text-right">
                        <span className="text-lg font-bold text-amber-600 dark:text-amber-500">
                          {reason.count}
                        </span>
                        <p className="text-xs text-muted-foreground">
                          occurrence{reason.count !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Example Runs */}
            {node.example_run_ids && node.example_run_ids.length > 0 && (
              <div>
                <h3 className="font-semibold text-foreground mb-3">Example Runs</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Click to view detailed run information, including events and timeline.
                </p>
                <div className="space-y-2">
                  {node.example_run_ids.map((runId: string, idx: number) => (
                    <button
                      key={idx}
                      onClick={() => handleViewRun(runId)}
                      disabled={loadingRun}
                      className="w-full flex items-center justify-between p-3 bg-card border rounded-lg hover:border-primary hover:bg-accent/50 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div>
                        <p className="text-sm font-medium text-foreground">Run #{idx + 1}</p>
                        <p className="text-xs text-muted-foreground font-mono">
                          {runId.substring(0, 12)}...
                        </p>
                      </div>
                      <span className="text-xs text-primary">View details →</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                💡 Recommendations
              </h3>
              <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
                <li>Review the example runs to understand user behavior patterns</li>
                <li>Check if UI elements are clearly visible and accessible</li>
                <li>Consider adding clearer instructions or visual cues</li>
                <li>Test with different user personas to identify specific pain points</li>
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Run Details Modal */}
      {selectedRun && (
        <RunDetailsModal
          run={selectedRun}
          onClose={() => setSelectedRun(null)}
        />
      )}

      {/* Loading overlay */}
      {loadingRun && (
        <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
          <div className="bg-background p-4 rounded-lg shadow-lg">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">Loading run details...</span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
