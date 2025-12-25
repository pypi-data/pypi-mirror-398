import sankeyDataJson from "./sankey-data.json"
import type { SankeyData } from "@/types/api"

export function useSankeyData(): SankeyData {
  return sankeyDataJson as SankeyData
}
