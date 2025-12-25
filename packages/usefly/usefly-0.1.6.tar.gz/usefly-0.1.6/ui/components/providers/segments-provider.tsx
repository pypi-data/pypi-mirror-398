"use client"

import { createContext, useContext, useState, type ReactNode } from "react"

type SegmentOption = {
  type: "location" | "platform" | "status"
  value: string
  label: string
}

type SegmentsContextType = {
  selectedSegments: SegmentOption[]
  setSelectedSegments: (segments: SegmentOption[]) => void
  toggleSegment: (option: SegmentOption) => void
  isSegmentSelected: (option: SegmentOption) => boolean
  removeSegment: (option: SegmentOption) => void
  clearAllSegments: () => void
}

const SegmentsContext = createContext<SegmentsContextType | null>(null)

export function SegmentsProvider({ children }: { children: ReactNode }) {
  const [selectedSegments, setSelectedSegments] = useState<SegmentOption[]>([])

  const toggleSegment = (option: SegmentOption) => {
    setSelectedSegments((prev) => {
      const exists = prev.find((s) => s.type === option.type && s.value === option.value)
      if (exists) {
        return prev.filter((s) => !(s.type === option.type && s.value === option.value))
      } else {
        return [...prev, option]
      }
    })
  }

  const isSegmentSelected = (option: SegmentOption) => {
    return selectedSegments.some((s) => s.type === option.type && s.value === option.value)
  }

  const removeSegment = (option: SegmentOption) => {
    setSelectedSegments((prev) =>
      prev.filter((s) => !(s.type === option.type && s.value === option.value))
    )
  }

  const clearAllSegments = () => {
    setSelectedSegments([])
  }

  return (
    <SegmentsContext.Provider
      value={{
        selectedSegments,
        setSelectedSegments,
        toggleSegment,
        isSegmentSelected,
        removeSegment,
        clearAllSegments
      }}
    >
      {children}
    </SegmentsContext.Provider>
  )
}

export function useSegments() {
  const context = useContext(SegmentsContext)
  if (!context) {
    throw new Error("useSegments must be used within a SegmentsProvider")
  }
  return context
}

export type { SegmentOption }
