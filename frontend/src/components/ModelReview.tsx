
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"

type Feedback = {
  id: number
  recipe_title: string
  original_meal_type: string | null
  corrected_meal_type: string
  original_confidence: number | null
  created_at: string
}

export default function ModelReview() {
  const [feedback, setFeedback] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    async function loadFeedback() {
      try {
        const response = await fetch("/api/feedback/recipes")

        if (!response.ok) {
          throw new Error("Failed to load recipe feedback.")
        }

        const data = await response.json()
        setFeedback(data.feedback ?? [])
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Something went wrong."
        )
      } finally {
        setLoading(false)
      }
    }

    loadFeedback()
  }, [])

  async function deleteFeedback(id: number) {
  const confirmed = window.confirm(
    "Are you sure you want to delete this correction?"
  )

  if (!confirmed) return

  setDeletingId(id)
  setError("")

  try {
    const response = await fetch(`/api/feedback/recipe/${id}`, {
      method: "DELETE",
    })

    if (!response.ok) {
      throw new Error("Failed to delete correction.")
    }

    setFeedback((previous) =>
      previous.filter((item) => item.id !== id)
    )
  } catch (err) {
    setError(
      err instanceof Error ? err.message : "Something went wrong."
    )
  } finally {
    setDeletingId(null)
  }
}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-emerald-800">
          Model Review
        </h1>
        <p className="mt-2 text-gray-600">
          Review saved corrections to improve future model training.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Saved Corrections ({feedback.length})
          </CardTitle>
        </CardHeader>

        <CardContent>
          {loading && <p>Loading feedback...</p>}

          {error && <p className="text-red-600">{error}</p>}

          {!loading && !error && feedback.length === 0 && (
            <p className="text-gray-500">
              No corrections saved yet.
            </p>
          )}

          {!loading && !error && feedback.length > 0 && (
            <div className="space-y-4">
              {feedback.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border p-4"
                >
                  <h3 className="font-semibold">
                    {item.recipe_title}
                  </h3>

                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary">
                      AI: {item.original_meal_type ?? "Unknown"}
                    </Badge>

                    <span>→</span>

                    <Badge>
                      Corrected: {item.corrected_meal_type}
                    </Badge>
                  </div>

                  <p className="mt-3 text-sm text-gray-500">
                    Original confidence:{" "}
                    {item.original_confidence != null
                      ? `${(item.original_confidence * 100).toFixed(1)}%`
                      : "N/A"}
                  </p>

                  <p className="mt-1 text-xs text-gray-400">
                    Saved: {new Date(item.created_at).toLocaleString()}
                  </p>

                  <div className="mt-4">
  <Button
    type="button"
    variant="outline"
    size="sm"
    onClick={() => deleteFeedback(item.id)}
    disabled={deletingId === item.id}
    className="text-red-600 hover:text-red-700"
  >
    <Trash2 className="mr-2 h-4 w-4" />
    {deletingId === item.id ? "Deleting..." : "Delete Correction"}
  </Button>
</div>

                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
