import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">404</h1>
        <p className="text-lg text-muted-foreground">Page not found</p>
        <Link href="/">
          <Button>Go Home</Button>
        </Link>
      </div>
    </div>
  )
}
