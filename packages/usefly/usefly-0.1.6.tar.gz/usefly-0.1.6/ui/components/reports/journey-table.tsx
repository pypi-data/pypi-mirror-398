"use client"

import { useMemo } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { PersonaRun } from "@/types/api"
import { aggregateBySegment, getPercentageColor } from "./utils"

interface JourneyTableProps {
  runs: PersonaRun[]
  groupByPlatform: boolean
  groupByPersona: boolean
}

export function JourneyTable({ runs, groupByPlatform, groupByPersona }: JourneyTableProps) {
  const aggregations = useMemo(
    () => aggregateBySegment(runs, groupByPlatform, groupByPersona),
    [runs, groupByPlatform, groupByPersona]
  )

  if (runs.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p>No journey data available for the selected filters</p>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="font-semibold">Segment</TableHead>
            <TableHead className="text-center font-semibold">Goals Achieved</TableHead>
            <TableHead className="text-center font-semibold">Errors</TableHead>
            <TableHead className="text-center font-semibold">Friction Detected</TableHead>
            <TableHead className="text-center font-semibold">Sample Size</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {aggregations.map((agg, index) => (
            <TableRow key={index}>
              <TableCell className="font-medium">{agg.segment}</TableCell>
              <TableCell className="text-center">
                <span className={`font-semibold ${getPercentageColor(agg.goalsAchievedPercent, true)}`}>
                  {agg.goalsAchievedPercent}%
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-semibold ${getPercentageColor(agg.errorsPercent, false)}`}>
                  {agg.errorsPercent}%
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-semibold ${getPercentageColor(agg.frictionPercent, false)}`}>
                  {agg.frictionPercent}%
                </span>
              </TableCell>
              <TableCell className="text-center text-muted-foreground">
                {agg.totalRuns} runs
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Legend */}
      <div className="border-t border-border bg-muted/30 px-4 py-3">
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="font-medium">Color Guide:</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-emerald-500 rounded"></span>
            <span>Good (Goals: &gt;80%, Errors/Friction: &lt;20%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-amber-500 rounded"></span>
            <span>Warning (Goals: 40-80%, Errors/Friction: 20-40%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-red-500 rounded"></span>
            <span>Critical (Goals: &lt;40%, Errors/Friction: &gt;40%)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
