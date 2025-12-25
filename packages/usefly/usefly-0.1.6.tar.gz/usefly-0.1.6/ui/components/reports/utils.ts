import type { PersonaRun } from "@/types/api"

export interface JourneyAggregation {
  segment: string
  platform?: string
  persona?: string
  totalRuns: number
  goalsAchievedPercent: number
  errorsPercent: number
  frictionPercent: number
}

/**
 * Aggregate runs by segment (platform and/or persona) for journey table
 */
export function aggregateBySegment(
  runs: PersonaRun[],
  groupByPlatform: boolean,
  groupByPersona: boolean
): JourneyAggregation[] {
  if (runs.length === 0) {
    return []
  }

  // Create grouping key based on what we're grouping by
  const groupMap = new Map<string, PersonaRun[]>()

  runs.forEach((run) => {
    let key = ""
    let platform: string | undefined
    let persona: string | undefined

    if (groupByPlatform && groupByPersona) {
      key = `${run.platform}-${run.persona_type}`
      platform = run.platform
      persona = run.persona_type
    } else if (groupByPlatform) {
      key = run.platform
      platform = run.platform
    } else if (groupByPersona) {
      key = run.persona_type
      persona = run.persona_type
    } else {
      // No grouping, treat all as one segment
      key = "all"
    }

    if (!groupMap.has(key)) {
      groupMap.set(key, [])
    }
    groupMap.get(key)!.push(run)
  })

  // Calculate aggregations for each segment
  const aggregations: JourneyAggregation[] = Array.from(groupMap.entries()).map(([key, segmentRuns]) => {
    const totalRuns = segmentRuns.length

    // Calculate goals achieved percentage
    // A run achieves goals only if is_done is true AND verdict is true (SUCCESS status)
    const runsWithGoals = segmentRuns.filter((r) => {
      const verdict = r.judgement_data?.verdict
      const failureReason = r.judgement_data?.failure_reason
      return r.is_done && verdict === true && !failureReason
    }).length
    const goalsAchievedPercent = (runsWithGoals / totalRuns) * 100

    // Calculate errors percentage
    const runsWithErrors = segmentRuns.filter((r) => r.error_type && r.error_type !== "").length
    const errorsPercent = (runsWithErrors / totalRuns) * 100

    // Calculate friction percentage
    // Friction is when steps_completed < total_steps
    const runsWithFriction = segmentRuns.filter((r) => r.total_steps > 0 && r.steps_completed < r.total_steps).length
    const frictionPercent = (runsWithFriction / totalRuns) * 100

    // Build segment label
    let segment = ""
    const platform = groupByPlatform ? segmentRuns[0].platform : undefined
    const persona = groupByPersona ? segmentRuns[0].persona_type : undefined

    if (platform && persona) {
      segment = `${platform} - ${formatPersona(persona)}`
    } else if (platform) {
      segment = platform
    } else if (persona) {
      segment = formatPersona(persona)
    } else {
      segment = "All Runs"
    }

    return {
      segment,
      platform,
      persona,
      totalRuns,
      goalsAchievedPercent: Number(goalsAchievedPercent.toFixed(1)),
      errorsPercent: Number(errorsPercent.toFixed(1)),
      frictionPercent: Number(frictionPercent.toFixed(1)),
    }
  })

  // Sort by segment name
  return aggregations.sort((a, b) => a.segment.localeCompare(b.segment))
}

/**
 * Format persona type for display
 */
function formatPersona(persona: string): string {
  return persona
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

/**
 * Get color class based on percentage value
 * For goals: green (>80%), yellow (40-80%), red (<40%)
 * For errors/friction: green (<20%), yellow (20-40%), red (>40%)
 */
export function getPercentageColor(value: number, higherIsBetter: boolean): string {
  if (higherIsBetter) {
    if (value >= 80) return "text-emerald-600 dark:text-emerald-400"
    if (value >= 40) return "text-amber-600 dark:text-amber-400"
    return "text-red-600 dark:text-red-400"
  } else {
    if (value < 20) return "text-emerald-600 dark:text-emerald-400"
    if (value < 40) return "text-amber-600 dark:text-amber-400"
    return "text-red-600 dark:text-red-400"
  }
}
