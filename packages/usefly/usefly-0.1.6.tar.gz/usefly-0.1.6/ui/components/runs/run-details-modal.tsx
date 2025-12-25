"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import type { PersonaRun } from "@/types/api"
import { calculateDerivedMetrics, formatDate } from "./run-utils"
import { RunOverviewTab } from "./run-overview-tab"
import { RunTimelineTab } from "./run-timeline-tab"
import { RunJourneyTab } from "./run-journey-tab"
import { getPersonaLabel } from "./mock-data"

interface RunDetailsModalProps {
  run: PersonaRun
  onClose: () => void
}

export function RunDetailsModal({ run, onClose }: RunDetailsModalProps) {
  const metrics = calculateDerivedMetrics(run)

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Run Details</DialogTitle>
          <DialogDescription>
            {getPersonaLabel(run.persona_type)} • {formatDate(run.timestamp)}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="flex-shrink-0 w-full justify-start border-b rounded-none bg-transparent px-0">
            <TabsTrigger value="overview" className="rounded-none">
              Overview
            </TabsTrigger>
            <TabsTrigger value="timeline" className="rounded-none">
              Timeline
            </TabsTrigger>
            <TabsTrigger value="journey" className="rounded-none">
              Journey
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto mt-4 pr-4">
            <TabsContent value="overview" className="mt-0">
              <RunOverviewTab run={run} metrics={metrics} />
            </TabsContent>

            <TabsContent value="timeline" className="mt-0">
              <RunTimelineTab events={run.events || []} />
            </TabsContent>

            <TabsContent value="journey" className="mt-0">
              <RunJourneyTab
                journeyPath={run.journey_path || []}
                events={run.events || []}
                metrics={metrics}
              />
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
