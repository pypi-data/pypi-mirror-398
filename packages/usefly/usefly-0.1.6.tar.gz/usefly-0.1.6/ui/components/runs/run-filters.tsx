"use client"

import { useEffect } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"
import { getPersonaLabel } from "./mock-data"
import { Scenario, ReportListItem } from "@/types/api"
import { useFilterContext } from "@/contexts/filter-context"

export type RunStatus = "success" | "failed" | "error" | "all"

interface RunFiltersProps {
    // Available Data
    scenarios: Scenario[]
    reports?: ReportListItem[] // Optional if not using report filter or filtering reports externally
    availablePersonas: string[]

    // Configuration
    showScenarioFilter?: boolean
    showReportFilter?: boolean
    showDateFilter?: boolean
    showPlatformFilter?: boolean
}

export function RunFilters({
    scenarios,
    reports = [],
    availablePersonas,
    showScenarioFilter = true,
    showReportFilter = true,
    showDateFilter = true,
    showPlatformFilter = false,
}: RunFiltersProps) {
    const {
        scenarioFilter,
        reportFilter,
        statusFilter,
        personaFilter,
        dateFrom,
        dateTo,
        platformFilter,
        setScenarioFilter,
        setReportFilter,
        setStatusFilter,
        setPersonaFilter,
        setDateFrom,
        setDateTo,
        setPlatformFilter,
        resetFilters
    } = useFilterContext()

    const platforms = ["web", "mobile", "desktop"]

    // Validate and auto-reset stale filters
    // This runs when scenarios/reports are loaded and checks if cached filter values are valid
    useEffect(() => {
        // Check if scenario filter is stale (not "all" and not in available scenarios)
        if (showScenarioFilter && scenarioFilter !== "all" && scenarios.length > 0) {
            const scenarioExists = scenarios.some(s => s.id === scenarioFilter)
            if (!scenarioExists) {
                console.log('[RunFilters] Resetting stale scenarioFilter:', scenarioFilter)
                setScenarioFilter("all")
            }
        }
    }, [scenarios, scenarioFilter, showScenarioFilter, setScenarioFilter])

    useEffect(() => {
        // Check if report filter is stale
        if (showReportFilter && reportFilter !== "all" && reports.length > 0) {
            const reportExists = reports.some(r => r.report_id === reportFilter)
            if (!reportExists) {
                console.log('[RunFilters] Resetting stale reportFilter:', reportFilter)
                setReportFilter("all")
            }
        }
    }, [reports, reportFilter, showReportFilter, setReportFilter])

    // Compute effective filter values (use "all" if current value is invalid)
    // This ensures the Select never shows blank even before useEffect runs
    const effectiveScenarioFilter = scenarioFilter === "all" || scenarios.some(s => s.id === scenarioFilter)
        ? scenarioFilter
        : "all"

    const effectiveReportFilter = reportFilter === "all" || reports.some(r => r.report_id === reportFilter)
        ? reportFilter
        : "all"

    // Derived state to check if any relevant filter is active for Reset button
    const hasActiveFilters =
        (showScenarioFilter && effectiveScenarioFilter !== "all") ||
        (showReportFilter && effectiveReportFilter !== "all") ||
        statusFilter !== "all" ||
        personaFilter !== "all" ||
        (showDateFilter && (dateFrom || dateTo)) ||
        (showPlatformFilter && platformFilter !== "all")


    // Prepare reports options if filtered by scenario
    const filteredReports = showReportFilter
        ? (effectiveScenarioFilter === "all" ? reports : reports.filter(r => r.scenario_id === effectiveScenarioFilter))
        : []

    const handleScenarioChange = (val: string) => {
        setScenarioFilter(val)
        if (showReportFilter) {
            setReportFilter("all") // Reset report when scenario changes
        }
    }


    return (
        <div className="flex flex-col gap-4 p-4 bg-muted/30 rounded-lg border">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-foreground">Filters</h3>
                {hasActiveFilters && (
                    <Button variant="ghost" size="sm" onClick={resetFilters} className="h-8 px-2 text-xs">
                        <X className="w-3 h-3 mr-1" />
                        Clear all
                    </Button>
                )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">

                {/* Scenario Filter */}
                {showScenarioFilter && (
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Scenario</label>
                        <Select value={effectiveScenarioFilter} onValueChange={handleScenarioChange}>
                            <SelectTrigger className="w-full h-9">
                                <SelectValue placeholder="All" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Scenarios</SelectItem>
                                {scenarios.map((scenario) => (
                                    <SelectItem key={scenario.id} value={scenario.id}>
                                        {scenario.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                )}

                {/* Report Filter */}
                {showReportFilter && (
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Report</label>
                        <Select value={effectiveReportFilter} onValueChange={setReportFilter}>
                            <SelectTrigger className="w-full h-9">
                                <SelectValue placeholder="All" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Reports</SelectItem>
                                {filteredReports
                                    .sort((a, b) => new Date(b.first_run).getTime() - new Date(a.first_run).getTime())
                                    .map((report) => (
                                        <SelectItem key={report.report_id} value={report.report_id}>
                                            {new Date(report.first_run).toLocaleString()} ({report.run_count} runs)
                                        </SelectItem>
                                    ))}
                            </SelectContent>
                        </Select>
                    </div>
                )}

                {/* Status Filter */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Status</label>
                    <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as RunStatus)}>
                        <SelectTrigger className="w-full h-9">
                            <SelectValue placeholder="All" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Statuses</SelectItem>
                            <SelectItem value="success">✓ Success</SelectItem>
                            <SelectItem value="failed">✗ Goal Not Met</SelectItem>
                            <SelectItem value="error">⚠ Error</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Platform Filter (Optional) */}
                {showPlatformFilter && (
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Platform</label>
                        <Select value={platformFilter} onValueChange={setPlatformFilter}>
                            <SelectTrigger className="w-full h-9">
                                <SelectValue placeholder="All" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Platforms</SelectItem>
                                {platforms.map((p) => (
                                    <SelectItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                )}

                {/* Persona Filter */}
                <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Persona</label>
                    <Select value={personaFilter} onValueChange={setPersonaFilter}>
                        <SelectTrigger className="w-full h-9">
                            <SelectValue placeholder="All" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Personas</SelectItem>
                            {availablePersonas.map((persona) => (
                                <SelectItem key={persona} value={persona}>
                                    {getPersonaLabel(persona)}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {/* Date From */}
                {showDateFilter && (
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">From Date</label>
                        <Input
                            type="date"
                            value={dateFrom}
                            onChange={(e) => setDateFrom(e.target.value)}
                            className="h-9"
                        />
                    </div>
                )}

                {/* Date To */}
                {showDateFilter && (
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">To Date</label>
                        <Input
                            type="date"
                            value={dateTo}
                            onChange={(e) => setDateTo(e.target.value)}
                            className="h-9"
                        />
                    </div>
                )}
            </div>
        </div>
    )
}
