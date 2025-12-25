"use client"

import { createContext, useContext, useState, ReactNode } from "react"

interface WebsiteContextType {
  selectedWebsite: string
  setSelectedWebsite: (website: string) => void
}

const WebsiteContext = createContext<WebsiteContextType | undefined>(undefined)

export function WebsiteProvider({ children }: { children: ReactNode }) {
  const [selectedWebsite, setSelectedWebsite] = useState<string>("www.test.com")

  return (
    <WebsiteContext.Provider value={{ selectedWebsite, setSelectedWebsite }}>
      {children}
    </WebsiteContext.Provider>
  )
}

export function useWebsite() {
  const context = useContext(WebsiteContext)
  if (context === undefined) {
    throw new Error("useWebsite must be used within a WebsiteProvider")
  }
  return context
}
