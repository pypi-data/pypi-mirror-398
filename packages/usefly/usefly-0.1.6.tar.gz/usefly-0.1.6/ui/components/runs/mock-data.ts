// Persona label mapping
const personaLabels: Record<string, string> = {
  "new-shopper": "New Shopper",
  "returning-user": "Returning User",
  "admin-user": "Admin User",
  "premium-user": "Premium User",
  guest: "Guest User",
}

// Helper function to get persona label
export function getPersonaLabel(personaType: string): string {
  return personaLabels[personaType] || personaType
}

// Persona aggregation interface for reports
export interface PersonaAggregation {
  personaType: string
  personaLabel: string
  totalRuns: number
  successCount: number
  errorCount: number
  avgProgress: number
  avgDuration: number
  successRate: number
}