"use client"

import { ResponsiveSankey } from "@nivo/sankey"
import { useTheme } from "next-themes"
import { useSankeyData } from "./use-sankey-data"
import { formatUrl, getFullDecodedUrl } from "@/components/runs/run-utils"
import type { SankeyData } from "@/types/api"
import { Info } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

// Custom colors excluding red/orange/magenta to reserve for friction indicators
const LIGHT_MODE_COLORS = [
  '#1f77b4', // blue
  '#2ca02c', // green
  '#9467bd', // purple
  '#8c564b', // brown
  '#17becf', // cyan
  '#bcbd22', // yellow-green
  '#7f7f7f', // gray
  '#e377c2', // pink
]

const DARK_MODE_COLORS = [
  '#1b9e77', // teal
  '#7570b3', // purple
  '#66a61e', // green
  '#e6ab02', // yellow
  '#a6761d', // brown
  '#17becf', // cyan
  '#666666', // gray
]

interface JourneySankeyProps {
  data?: SankeyData
  onNodeClick?: (node: any) => void
}

function JourneySankeyLegend({ isDark }: { isDark: boolean }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="h-5 w-5 text-muted-foreground hover:text-foreground"
          aria-label="Show legend"
        >
          <Info className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80" side="top" sideOffset={8}>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-sm mb-1">Journey Flow Legend</h4>
            <p className="text-xs text-muted-foreground">Understanding the visualization</p>
          </div>

          <div className="space-y-3 pt-2 border-t">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Node Types
            </p>

            <div className="flex items-start gap-3">
              <div
                className="mt-0.5 h-4 w-4 rounded border-2 shrink-0"
                style={{ borderColor: '#ff0055', boxShadow: '0 0 8px rgba(255, 0, 85, 0.5)' }}
              />
              <div className="space-y-0.5">
                <p className="text-sm font-medium" style={{ color: '#ff0055' }}>High</p>
                <p className="text-xs text-muted-foreground">Friction detected at this step</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div
                className="mt-0.5 h-4 w-4 rounded border-2 shrink-0"
                style={{ borderColor: isDark ? '#ffffff' : '#000000' }}
              />
              <div className="space-y-0.5">
                <p className="text-sm font-medium">Normal</p>
                <p className="text-xs text-muted-foreground">No friction detected at this step</p>
              </div>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Interaction</p>
            <ul className="text-xs text-muted-foreground space-y-1.5">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Hover over nodes to see detailed metrics</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Click friction nodes to view example runs</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Node width represents traffic volume</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Link thickness shows transition frequency</span>
              </li>
            </ul>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

export function JourneySankey({ data, onNodeClick }: JourneySankeyProps) {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"

  // Use provided data or fall back to mock data
  const sankeyData = data || useSankeyData()

  if (!sankeyData || !sankeyData.nodes || sankeyData.nodes.length === 0) {
    return (
      <div className="h-[500px] w-full flex items-center justify-center text-muted-foreground">
        <p>No journey data available</p>
      </div>
    )
  }

  // Transform backend data to match Nivo format
  // Backend: nodes with 'name', links with numeric source/target
  // Nivo expects: nodes with 'id', links with string source/target matching node IDs
  // Note: Filter out self-loops (circular links) as Nivo Sankey doesn't support them

  // Calculate self-loop counts (interactions on same page)
  const selfLoopCounts = new Map<number, number>()
  sankeyData.links.forEach(link => {
    if (link.source === link.target) {
      selfLoopCounts.set(link.source, (selfLoopCounts.get(link.source) || 0) + link.value)
    }
  })

  const transformedData = {
    nodes: sankeyData.nodes.map((node, index) => {
      const selfLoops = selfLoopCounts.get(index) || 0
      const nodeId = node.name || `node-${index}`

      // Use formatUrl to decode URLs properly (handles UTF-8 characters like Hebrew)
      const displayName = formatUrl(nodeId)

      const frictionCount = (node.friction_count ?? 0)
      const hasFriction = frictionCount > 0

      return {
        id: nodeId,
        displayName, // For tooltip display
        decodedId: getFullDecodedUrl(nodeId), // Full decoded URL
        nodeLabel: selfLoops > 0
          ? `${displayName}\n(${selfLoops} interactions)`
          : displayName,
        ...node,
        selfLoops,
        // Friction metadata - simplified to binary: high (any friction) or none
        hasFriction,
        frictionSeverity: hasFriction ? 'high' : 'none'
      }
    }),
    links: sankeyData.links
      .filter(link => link.source !== link.target) // Remove self-loops
      .map(link => {
        const sourceIndex = typeof link.source === 'number' ? link.source : 0
        const targetIndex = typeof link.target === 'number' ? link.target : 0
        const sourceNode = sankeyData.nodes[sourceIndex]
        const targetNode = sankeyData.nodes[targetIndex]

        return {
          ...link,
          source: sourceNode?.name ?? `node-${link.source}`,
          target: targetNode?.name ?? `node-${link.target}`,
          // Dim links FROM nodes with friction
          hasFrictionSource: (sourceNode?.friction_count ?? 0) > 0
        }
      })
  }

  // Theme-aware colors
  const tooltipBg = isDark ? "#1f1f1f" : "#ffffff"
  const tooltipBorder = isDark ? "#404040" : "#e0e0e0"
  const tooltipText = isDark ? "#e0e0e0" : "#333333"
  const tooltipMuted = isDark ? "#888888" : "#666666"
  const labelColor = isDark ? "#d0d0d0" : "#333333"

  return (
    <div className="w-full">
      {/* Header with title, subheading, and legend */}
      <div className="mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">User Journey Flow</h3>
          <JourneySankeyLegend isDark={isDark} />
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          See how personas navigate through your site. Hover for details, click friction points to investigate.
        </p>
      </div>

      <div className="h-[500px] w-full relative">
        <style jsx global>{`
          /* Enhanced friction node styling with multi-layer glow */
          @keyframes pulse-glow {
            0%, 100% {
              filter:
                drop-shadow(0 0 3px rgba(255, 0, 85, 0.3))
                drop-shadow(0 0 2px rgba(255, 0, 85, 0.4));
            }
            50% {
              filter:
                drop-shadow(0 0 10px rgba(255, 0, 85, 0.5))
                drop-shadow(0 0 6px rgba(255, 0, 85, 0.4))
                drop-shadow(0 0 15px rgba(255, 0, 85, 0.2));
            }
          }

          /* Apply glow to friction nodes via SVG elements */
          [data-testid="sankey.node"] rect[fill="#ff0055"],
          [stroke="#ff0055"] {
            animation: pulse-glow 1.5s ease-in-out infinite;
          }

          .sankey-friction-link {
            opacity: 0.2 !important;
          }
        `}</style>

      <ResponsiveSankey
        data={transformedData}
        margin={{ top: 60, right: 60, bottom: 40, left: 50 }}
        align="justify"
        colors={isDark ? DARK_MODE_COLORS : LIGHT_MODE_COLORS}
        nodeOpacity={1}
        nodeHoverOthersOpacity={0.35}
        nodeThickness={18}
        nodeSpacing={24}
        nodeBorderWidth={3}
        nodeBorderColor={(node: any) => {
          if (node.hasFriction) {
            return '#ff0055'
          }
          return isDark ? "#ffffff" : "#000000"
        }}
        nodeBorderRadius={3}
        linkOpacity={isDark ? 0.7 : 0.5}
        linkHoverOthersOpacity={0.2}
        linkContract={3}
        enableLinkGradient={!isDark}
        linkBlendMode={isDark ? "screen" : "multiply"}
        labelPosition="outside"
        labelOrientation="horizontal"
        labelPadding={16}
        labelTextColor={labelColor}
        label={(node: any) => node.nodeLabel || node.id}
        nodeTooltip={({ node }: any) => (
          <div
            style={{
              background: tooltipBg,
              padding: "16px 20px",
              border: `2px solid ${tooltipBorder}`,
              borderRadius: "8px",
              boxShadow: isDark
                ? "0 8px 24px rgba(0,0,0,0.6)"
                : "0 4px 16px rgba(0,0,0,0.2)",
              minWidth: "420px",
              maxWidth: "520px",
              color: tooltipText,
              position: "relative",
            }}
          >
            <strong style={{
              fontSize: "14px",
              wordBreak: "break-word",
              display: "block",
              lineHeight: "1.4"
            }}>
              {node.displayName || node.id}
            </strong>
            <div style={{
              marginTop: "10px",
              fontSize: "11px",
              color: tooltipMuted,
              wordBreak: "break-all",
              lineHeight: "1.4"
            }}>
              {node.decodedId}
            </div>
            <div style={{
              marginTop: "12px",
              fontSize: "13px",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "8px"
            }}>
              <div>
                <span style={{ color: tooltipMuted, fontSize: "11px" }}>Total events:</span>
                <div style={{ fontWeight: 600, marginTop: "2px" }}>{node.event_count || node.visits}</div>
              </div>
              <div>
                <span style={{ color: tooltipMuted, fontSize: "11px" }}>Visits:</span>
                <div style={{ fontWeight: 600, marginTop: "2px" }}>{node.visits}</div>
              </div>
            </div>

            {/* Friction Information */}
            {node.hasFriction && node.friction_count && (
              <div style={{
                marginTop: "14px",
                paddingTop: "14px",
                borderTop: `2px solid ${tooltipBorder}`,
              }}>
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  color: '#ff0055',
                  fontWeight: 700,
                  marginBottom: "10px",
                  fontSize: "13px"
                }}>
                  <span style={{ fontSize: "16px" }}>⚠</span>
                  <span>{node.friction_count} failure{node.friction_count !== 1 ? 's' : ''} at this location</span>
                </div>

                {node.friction_reasons && node.friction_reasons.length > 0 && (
                  <div style={{
                    fontSize: "12px",
                    color: tooltipText,
                    marginBottom: "10px"
                  }}>
                    <div style={{
                      marginBottom: "6px",
                      fontWeight: 600,
                      color: tooltipMuted,
                      fontSize: "11px",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px"
                    }}>
                      Top reasons
                    </div>
                    {node.friction_reasons.slice(0, 2).map((fr: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          marginBottom: "6px",
                          paddingLeft: "12px",
                          lineHeight: "1.5",
                          position: "relative"
                        }}
                      >
                        <span style={{
                          position: "absolute",
                          left: "0",
                          color: '#ff0055',
                          fontWeight: 700
                        }}>•</span>
                        <span>{fr.reason}</span>
                        <span style={{
                          marginLeft: "6px",
                          padding: "2px 6px",
                          background: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)",
                          borderRadius: "4px",
                          fontSize: "11px",
                          fontWeight: 600
                        }}>
                          {fr.count}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {node.friction_impact && (
                  <div style={{
                    fontSize: "12px",
                    color: tooltipMuted,
                    marginTop: "10px",
                    padding: "8px 10px",
                    background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.03)",
                    borderRadius: "6px",
                    fontWeight: 500
                  }}>
                    <span style={{ fontWeight: 700, color: '#ff0055' }}>
                      {(node.friction_impact * 100).toFixed(0)}%
                    </span> of all failures
                  </div>
                )}

                <div style={{
                  marginTop: "12px",
                  fontSize: "12px",
                  color: "#3b82f6",
                  fontWeight: 600,
                  textAlign: "center",
                  padding: "8px",
                  background: isDark ? "rgba(59, 130, 246, 0.1)" : "rgba(59, 130, 246, 0.05)",
                  borderRadius: "6px",
                  cursor: "pointer"
                }}>
                  Click node to view example runs →
                </div>
              </div>
            )}
          </div>
        )}
        onClick={(node: any) => {
          if (node.hasFriction && onNodeClick) {
            onNodeClick(node)
          }
        }}
      />
      </div>
    </div>
  )
}

