import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatModelName = (modelId: string) => {
  if (!modelId) return ""

  // 1. Remove date suffixes like -20241022 or -20250929
  // Also handles -latest, -exp, -preview-DATE
  let name = modelId.replace(/-(20\d{6}|latest|exp|preview(-\d+)?)$/, "")

  // 2. Handle specific version formatting (4-5 -> 4.5, 3-5 -> 3.5, 2-5 -> 2.5)
  name = name.replace(/(\d)-(\d)/g, "$1.$2")

  // 3. Handle model segments capitalization
  if (name.includes("/")) {
    name = name.split("/").pop() || name
  }

  return name.split("-").map(s => {
    if (s.match(/^\d/) || ["pro", "mini", "nano", "flash", "lite", "search", "audio", "it"].includes(s)) {
      return s
    }
    return s.charAt(0).toUpperCase() + s.slice(1)
  }).join(" ")
}
