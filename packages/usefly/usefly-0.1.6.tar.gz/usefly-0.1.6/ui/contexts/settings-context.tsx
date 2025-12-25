"use client"

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react"
import { systemConfigApi } from "@/lib/api-client"
import { SystemConfigStatus } from "@/types/api"

interface SettingsContextType {
  isConfigured: boolean
  isLoading: boolean
  missingFields: string[]
  refreshStatus: () => Promise<void>
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<SystemConfigStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await systemConfigApi.getStatus()
      setStatus(data)
    } catch {
      // If endpoint fails, assume not configured
      setStatus({
        configured: false,
        missing_fields: ["api_key"],
      })
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch on mount
  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Refresh status periodically (every 30 seconds) when not configured
  useEffect(() => {
    if (status?.configured) return

    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [status?.configured, fetchStatus])

  return (
    <SettingsContext.Provider
      value={{
        isConfigured: status?.configured ?? false,
        isLoading,
        missingFields: status?.missing_fields ?? [],
        refreshStatus: fetchStatus,
      }}
    >
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider")
  }
  return context
}
