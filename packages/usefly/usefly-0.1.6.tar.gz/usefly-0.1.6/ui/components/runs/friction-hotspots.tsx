"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { FrictionHotspotItem, PersonaRun } from "@/types/api"
import { AlertTriangle, MapPin } from "lucide-react"
import { useState } from "react"
import { RunDetailsModal } from "./run-details-modal"
import { personaRecordsApi } from "@/lib/api-client"
import { formatUrl, getFullDecodedUrl } from "@/components/runs/run-utils"

interface FrictionHotspotsProps {
    hotspots: FrictionHotspotItem[]
    loading?: boolean
}

export function FrictionHotspots({ hotspots, loading }: FrictionHotspotsProps) {
    const [selectedRun, setSelectedRun] = useState<PersonaRun | null>(null)
    const [loadingRunDetails, setLoadingRunDetails] = useState(false)
    const [showAll, setShowAll] = useState(false)

    const ITEMS_PER_PAGE = 5
    const displayedHotspots = showAll ? hotspots : hotspots.slice(0, ITEMS_PER_PAGE)

    const handleHotspotClick = async (runId: string) => {
        try {
            setLoadingRunDetails(true)
            const run = await personaRecordsApi.get(runId)
            setSelectedRun(run)
        } catch (error) {
            console.error("Failed to load run details:", error)
        } finally {
            setLoadingRunDetails(false)
        }
    }

    if (loading) {
        return <div className="h-32 animate-pulse bg-muted rounded-md" />
    }

    if (!hotspots || hotspots.length === 0) {
        return null
    }

    return (
        <>
            <Card>
                <CardHeader className="border-b bg-amber-50 dark:bg-amber-950/20">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-500" />
                        <CardTitle className="text-base font-semibold text-amber-900 dark:text-amber-200">
                            Goal Not Met - Top Issues
                        </CardTitle>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                        Common patterns where runs completed but didn't achieve the goal. Click to view example runs.
                    </p>
                </CardHeader>
                <CardContent className="p-6">
                    <div className="space-y-3">
                        {displayedHotspots.map((item, index) => (
                            <div
                                key={index}
                                onClick={() => item.example_run_ids.length > 0 && handleHotspotClick(item.example_run_ids[0])}
                                className={`group relative p-4 rounded-lg border bg-card transition-all ${item.example_run_ids.length > 0
                                    ? "cursor-pointer hover:border-amber-300 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 hover:shadow-sm"
                                    : ""
                                    }`}
                            >
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex-1 min-w-0">
                                        {/* Location */}
                                        <div className="flex items-start gap-2 mb-2">
                                            <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                                            <span className="text-sm font-medium text-foreground truncate" title={item.location ? getFullDecodedUrl(item.location) : ''}>
                                                {item.location ? formatUrl(item.location) : "Unknown Location"}
                                            </span>
                                        </div>

                                        {/* Reason */}
                                        <p className="text-sm text-muted-foreground pl-6 line-clamp-2">
                                            {item.reason}
                                        </p>
                                    </div>

                                    {/* Stats */}
                                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                                        <span className="text-lg font-bold text-amber-600 dark:text-amber-500">
                                            {item.count}
                                        </span>
                                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                                            {(item.impact_percentage * 100).toFixed(0)}% of failures
                                        </span>
                                    </div>
                                </div>

                                {/* Progress bar */}
                                <div className="mt-3 pl-6">
                                    <Progress
                                        value={item.impact_percentage * 100}
                                        className="h-1.5 bg-muted [&>div]:bg-amber-500"
                                    />
                                </div>

                                {/* Example count indicator */}
                                <div className="mt-2 pl-6 flex items-center gap-2 text-xs text-muted-foreground">
                                    <span>{item.example_run_ids.length} example{item.example_run_ids.length !== 1 ? 's' : ''}</span>
                                    {item.example_run_ids.length > 0 && (
                                        <span className="text-primary group-hover:underline">Click to view →</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {hotspots.length > ITEMS_PER_PAGE && (
                        <div className="mt-4 pt-4 border-t">
                            <button
                                onClick={() => setShowAll(!showAll)}
                                className="w-full text-center text-sm text-primary hover:text-primary/80 font-medium transition-colors py-2 hover:bg-accent rounded-md"
                            >
                                {showAll ? (
                                    <>Show Less</>
                                ) : (
                                    <>Show {hotspots.length - ITEMS_PER_PAGE} More Issue{hotspots.length - ITEMS_PER_PAGE !== 1 ? 's' : ''}</>
                                )}
                            </button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Run Details Modal */}
            {selectedRun && (
                <RunDetailsModal
                    run={selectedRun}
                    onClose={() => setSelectedRun(null)}
                />
            )}

            {/* Loading overlay when fetching run details */}
            {loadingRunDetails && (
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
