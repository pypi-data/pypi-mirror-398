"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"

type RunStatus = "success" | "failed" | "error" | "all"

interface FilterState {
    scenarioFilter: string
    reportFilter: string
    statusFilter: RunStatus | "all"
    personaFilter: string
    platformFilter: string
    dateFrom: string
    dateTo: string
}

interface FilterContextType extends FilterState {
    setScenarioFilter: (value: string) => void
    setReportFilter: (value: string) => void
    setStatusFilter: (value: RunStatus | "all") => void
    setPersonaFilter: (value: string) => void
    setPlatformFilter: (value: string) => void
    setDateFrom: (value: string) => void
    setDateTo: (value: string) => void
    resetFilters: () => void
}

const FilterContext = createContext<FilterContextType | undefined>(undefined)

const STORAGE_KEY = "usefly_filter_state"

const defaultState: FilterState = {
    scenarioFilter: "all",
    reportFilter: "all",
    statusFilter: "all",
    personaFilter: "all",
    platformFilter: "all",
    dateFrom: "",
    dateTo: "",
}

export function FilterProvider({ children }: { children: ReactNode }) {
    const router = useRouter()
    const pathname = usePathname()
    const searchParams = useSearchParams()

    // Initialize state
    const [state, setState] = useState<FilterState>(defaultState)
    const [isInitialized, setIsInitialized] = useState(false)

    // Load from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem(STORAGE_KEY)
        if (saved) {
            try {
                const parsed = JSON.parse(saved)
                setState((prev) => ({ ...prev, ...parsed }))
            } catch (e) {
                console.error("Failed to parse saved filters", e)
            }
        }
        setIsInitialized(true)
    }, [])

    // Sync state to localStorage whenever it changes
    useEffect(() => {
        if (isInitialized) {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
        }
    }, [state, isInitialized])

    // Optional: Sync state to URL params (and read from them)
    // For now, let's prioritize localStorage persistence as requested for moving between pages.
    // URL params are useful for deep linking. 
    // If URL params exist on load, they should override localStorage?
    // Let's implement a simple override on mount if params exist.
    useEffect(() => {
        if (!isInitialized) return

        const newParams = new URLSearchParams(searchParams.toString())
        let hasUpdates = false
        const updates: Partial<FilterState> = {}

        // Check if URL has params that differ from current state
        if (searchParams.get("scenario") && searchParams.get("scenario") !== state.scenarioFilter) {
            updates.scenarioFilter = searchParams.get("scenario")!
            hasUpdates = true
        }
        // ... repeat for others if we want full URL sync

        if (hasUpdates) {
            setState(prev => ({ ...prev, ...updates }))
        }

    }, [isInitialized, searchParams]) // Caveat: Circular dependency if we update URL from state

    // Context setters
    const setScenarioFilter = (value: string) => setState(prev => ({ ...prev, scenarioFilter: value }))
    const setReportFilter = (value: string) => setState(prev => ({ ...prev, reportFilter: value }))
    const setStatusFilter = (value: RunStatus | "all") => setState(prev => ({ ...prev, statusFilter: value }))
    const setPersonaFilter = (value: string) => setState(prev => ({ ...prev, personaFilter: value }))
    const setPlatformFilter = (value: string) => setState(prev => ({ ...prev, platformFilter: value }))
    const setDateFrom = (value: string) => setState(prev => ({ ...prev, dateFrom: value }))
    const setDateTo = (value: string) => setState(prev => ({ ...prev, dateTo: value }))

    const resetFilters = () => setState(defaultState)

    return (
        <FilterContext.Provider
            value={{
                ...state,
                setScenarioFilter,
                setReportFilter,
                setStatusFilter,
                setPersonaFilter,
                setPlatformFilter,
                setDateFrom,
                setDateTo,
                resetFilters
            }}
        >
            {children}
        </FilterContext.Provider>
    )
}

export function useFilterContext() {
    const context = useContext(FilterContext)
    if (context === undefined) {
        throw new Error("useFilterContext must be used within a FilterProvider")
    }
    return context
}
