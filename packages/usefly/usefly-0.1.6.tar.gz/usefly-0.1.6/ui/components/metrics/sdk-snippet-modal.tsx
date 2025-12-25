"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Check, Copy, ExternalLink } from "lucide-react"
import { toast } from "sonner"

interface SdkSnippetModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedChartIds: string[]
}

export function SdkSnippetModal({ open, onOpenChange, selectedChartIds }: SdkSnippetModalProps) {
  const [copied, setCopied] = useState(false)

  const generateSnippet = () => {
    return `<!-- Add this snippet to your HTML -->
<script>
  (function() {
    window.usefly = window.usefly || [];
    usefly.push(['init', {
      apiKey: 'YOUR_API_KEY',
      trackPageViews: true,
      metrics: ${JSON.stringify(selectedChartIds, null, 6)}
    }]);

    var script = document.createElement('script');
    script.src = 'https://cdn.usefly.ai/v1/usefly.js';
    script.async = true;
    document.head.appendChild(script);
  })();
</script>`
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generateSnippet())
    setCopied(true)
    toast.success("Snippet copied to clipboard!")
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Start Monitoring in Production</DialogTitle>
          <DialogDescription>
            Add this lightweight snippet to your application to start tracking these metrics in real-time.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4 pb-2">
          {/* Selected Charts */}
          <div>
            <h3 className="text-sm font-semibold mb-3">Selected Metrics ({selectedChartIds.length})</h3>
            <div className="flex flex-wrap gap-2">
              {selectedChartIds.map((id) => (
                <div
                  key={id}
                  className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-md border border-primary/20"
                >
                  {id.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </div>
              ))}
            </div>
          </div>

          {/* Code Snippet */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold">Installation Snippet</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className="gap-2"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Code
                  </>
                )}
              </Button>
            </div>
            <Card className="bg-muted/50">
              <CardContent className="p-4">
                <pre className="text-xs font-mono overflow-x-auto">
                  <code>{generateSnippet()}</code>
                </pre>
              </CardContent>
            </Card>
          </div>

          {/* Instructions */}
          <div>
            <h3 className="text-sm font-semibold mb-3">Quick Setup</h3>
            <div className="space-y-3">
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
                  1
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Copy the snippet</p>
                  <p className="text-sm text-muted-foreground">
                    Click the "Copy Code" button above to copy the integration snippet.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
                  2
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Add to your application</p>
                  <p className="text-sm text-muted-foreground">
                    Paste the snippet in your HTML <code className="bg-muted px-1 rounded">&lt;head&gt;</code> section,
                    just before the closing tag.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
                  3
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Replace YOUR_API_KEY</p>
                  <p className="text-sm text-muted-foreground">
                    Get your API key from the dashboard settings and replace the placeholder.
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-semibold">
                  4
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Deploy and verify</p>
                  <p className="text-sm text-muted-foreground">
                    Deploy your changes and check the dashboard to verify data is flowing.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Features */}
          <Card className="bg-muted/30 border-muted">
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="font-semibold mb-1">Lightweight</p>
                  <p className="text-muted-foreground text-xs">
                    &lt; 10KB gzipped, async loading
                  </p>
                </div>
                <div>
                  <p className="font-semibold mb-1">Privacy-First</p>
                  <p className="text-muted-foreground text-xs">
                    GDPR compliant, no PII collected
                  </p>
                </div>
                <div>
                  <p className="font-semibold mb-1">Real-Time</p>
                  <p className="text-muted-foreground text-xs">
                    See data in dashboard instantly
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="outline" className="flex-1" asChild>
              <a href="#" className="gap-2">
                <ExternalLink className="w-4 h-4" />
                View Documentation
              </a>
            </Button>
            <Button className="flex-1" onClick={() => onOpenChange(false)}>
              Done
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
