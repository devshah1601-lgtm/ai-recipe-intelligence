import { useState, type ChangeEvent } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type VideoIngredient = {
  name: string
  quantity: string | number | null
  unit: string | null
  ocr_confirmed: boolean
  ocr_first_seen_seconds: number | null
  verification_status: string
}

type VideoInstruction = {
  step_number: number
  description: string
  timestamp_seconds: number | null
}

type VideoRecipe = {
  title: string
  ingredients: VideoIngredient[]
  instructions: VideoInstruction[]
  uncertain_details: string[]
  verification_summary: {
    ocr_corroborated: number
    needs_visual_review: number
  }
}

export default function VideoExtractor() {
  const [video, setVideo] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [recipe, setRecipe] = useState<VideoRecipe | null>(null)

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null

    setError("")

    if (!selectedFile) {
      setVideo(null)
      return
    }

    if (!selectedFile.name.toLowerCase().endsWith(".mp4")) {
      setVideo(null)
      setError("Please select an MP4 video.")
      return
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setVideo(null)
      setError("Video must be smaller than 50 MB.")
      return
    }

    setVideo(selectedFile)
  }


async function analyzeVideo() {
  if (!video || loading) return

  setLoading(true)
  setError("")
  setRecipe(null)

  const formData = new FormData()
  formData.append("file", video)

  try {
    const response = await fetch("/api/videos/analyze-recipe", {
      method: "POST",
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Video analysis failed."
      )
    }

    setRecipe(data as VideoRecipe)
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Something went wrong during video analysis."
    )
  } finally {
    setLoading(false)
  }
}


  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>AI Video Recipe Extractor</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <p className="text-sm text-gray-600">
            Upload a cooking video to extract ingredients and
            cooking instructions using AI.
          </p>

          <input
            type="file"
            accept=".mp4,video/mp4"
            onChange={handleFileChange}
            className="block w-full rounded-md border p-3"
          />

          {video && (
            <p className="text-sm text-emerald-700">
              Selected: {video.name}
            </p>
          )}

          <Button
            type="button"
            onClick={analyzeVideo}
            disabled={!video || loading}
          >
            {loading ? "Analyzing video..." : "Analyze Video"}
          </Button>

          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {recipe && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">
              {recipe.title || "Extracted Video Recipe"}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-6">
            <section>
              <h3 className="mb-3 text-lg font-semibold">
                Ingredients ({recipe.ingredients?.length ?? 0})
              </h3>

              <ul className="space-y-3">
                {recipe.ingredients?.map((ingredient, index) => (
                  <li
                    key={index}
                    className="rounded-lg border bg-white p-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span>
                        {[
                          ingredient.quantity,
                          ingredient.unit,
                          ingredient.name,
                        ]
                          .filter(
                            (value) =>
                              value !== null &&
                              value !== undefined &&
                              value !== ""
                          )
                          .join(" ")}
                      </span>

                      <span
                        className={
                          ingredient.ocr_confirmed
                            ? "text-sm text-emerald-700"
                            : "text-sm text-amber-700"
                        }
                      >
                        {ingredient.verification_status === "not_verified_in_preview"
                            ? "Not verified in preview"
                            : ingredient.ocr_confirmed
                                ? "OCR text corroborated"
                                : "Needs visual review"}
                      </span>
                    </div>

                    {ingredient.ocr_first_seen_seconds != null && (
                      <p className="mt-1 text-xs text-gray-500">
                        First seen in text at{" "}
                        {ingredient.ocr_first_seen_seconds}s
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="mb-3 text-lg font-semibold">
                Cooking Instructions
              </h3>

              <ol className="space-y-3">
                {recipe.instructions?.map((step, index) => (
                  <li
                    key={index}
                    className="rounded-lg border bg-white p-3"
                  >
                    <p className="font-medium">
                      Step {step.step_number}: {step.description}
                    </p>

                    {step.timestamp_seconds != null && (
                      <p className="mt-1 text-xs text-gray-500">
                        Video timestamp: {step.timestamp_seconds}s
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </section>

            {recipe.uncertain_details?.length > 0 && (
              <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h3 className="mb-2 font-semibold text-amber-900">
                  Details to Review
                </h3>

                <ul className="list-disc space-y-2 pl-5 text-sm text-amber-800">
                  {recipe.uncertain_details.map((detail, index) => (
                    <li key={index}>{detail}</li>
                  ))}
                </ul>
              </section>
            )}

            <p className="text-xs text-gray-500">
              OCR text corroboration does not guarantee ingredient
              accuracy. Review the original video before cooking.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
