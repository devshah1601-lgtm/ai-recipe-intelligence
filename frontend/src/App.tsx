
import { useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import Sidebar, { type Page } from "@/components/Sidebar"
import Dashboard from "@/components/Dashboard"
import BulkCSV from "@/components/BulkCSV"
import ModelReview from "@/components/ModelReview"
import VideoExtractor from "@/components/VideoExtractor"


type Ingredient = string | {
  name?: string
  quantity?: string | number | null
  unit?: string | null
  notes?: string | null
  raw?: string | null
  ocr_confirmed?: boolean
ocr_first_seen_seconds?: number | null
verification_status?: string
match_type?: string | null
ocr_source_status?: string | null
}


type MLPrediction = {
  meal_type?: string
  confidence?: number
  needs_review?: boolean
  message?: string
}


type Recipe = {
  title?: string
  description?: string
  ingredients?: Ingredient[]
  instructions?: (
  | string
  | {
      text?: string
      description?: string
      step_number?: number
      timestamp_seconds?: number | null
    }
)[]
  prep_time?: unknown
  cook_time?: unknown
  total_time?: unknown
  servings?: unknown
  meal_type?: string
  confidence?: number
  needs_review?: boolean
  message?: string
  source_url?: string
  ml_prediction?: MLPrediction
  source_type?: string
video_platform?: string

storage?: {
  status?: string
  id?: number
}

uncertain_details?: string[]

verification_summary?: {
  ocr_corroborated?: number
  needs_visual_review?: number
}
}


function ingredientText(ingredient: Ingredient): string {
  if (typeof ingredient === "string") {
    return ingredient
  }

  const quantity = ingredient.quantity

  if (ingredient.raw) {
    return ingredient.raw
  }

  return [
    typeof quantity === "object" ? "" : quantity,
    ingredient.unit,
    ingredient.name,
    ingredient.notes,
  ]
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map(String)
    .join(" ")
}



function displayValue(value: unknown): string {
  if (value == null) return ""

  if (typeof value === "string" || typeof value === "number") {
    return String(value)
  }

  if (typeof value === "object" && !Array.isArray(value)) {
    const data = value as Record<string, unknown>

    if (typeof data.raw === "string" && data.raw.trim()) {
      return data.raw
    }

    const amount =
      typeof data.value === "string" || typeof data.value === "number"
        ? String(data.value)
        : ""

    const unit = typeof data.unit === "string" ? data.unit : ""

    return [amount, unit].filter(Boolean).join(" ")
  }

  return ""
}


function App() {
  const [activePage, setActivePage] = useState<Page>("dashboard")
  const [url, setUrl] = useState("")
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [correctedMealType, setCorrectedMealType] = useState("")
  const [savingFeedback, setSavingFeedback] = useState(false)
  const [feedbackMessage, setFeedbackMessage] = useState("")

  async function extractRecipe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError("")
    setRecipe(null)
    setCorrectedMealType("")
    setFeedbackMessage("")

    try {
      const response = await fetch("/api/extract-recipe-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Recipe extraction failed."
        )
      }

      // Some backends return the recipe directly,
      // while others wrap it in a "recipe" field.
      const extractedRecipe: Recipe = data.recipe ?? data

setRecipe(extractedRecipe)

    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }

  async function saveCorrection() {
  if (!recipe || !correctedMealType) return

  setSavingFeedback(true)
  setFeedbackMessage("")

  try {
    const response = await fetch("/api/feedback/recipe", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        recipe_title: recipe.title,
        source_url: recipe.source_url,
        original_meal_type: recipe.ml_prediction?.meal_type,
        corrected_meal_type: correctedMealType,
        original_confidence: recipe.ml_prediction?.confidence,
        ingredients: recipe.ingredients ?? [],
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Failed to save correction."
      )
    }

    setFeedbackMessage("Correction saved successfully!")
  } catch (err) {
    setFeedbackMessage(
      err instanceof Error ? err.message : "Something went wrong."
    )
  } finally {
    setSavingFeedback(false)
  }
}

  return (
  <div className="min-h-screen bg-emerald-50 md:flex">
    <Sidebar
      activePage={activePage}
      onNavigate={setActivePage}
    />

    <main className="min-w-0 flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-4xl space-y-8">
        {activePage === "dashboard" && (
  <Dashboard
  onOpenExtractor={() => setActivePage("extractor")}
/>
)}

{activePage === "csv" && <BulkCSV />}

{activePage === "review" && <ModelReview />}

{activePage === "video" && <VideoExtractor />}

{activePage === "extractor" && (
  <>
        <header className="text-center">
          <h1 className="text-4xl font-bold text-emerald-800">
            AI Recipe Intelligence
          </h1>
          <p className="mt-3 text-gray-600">
            Turn recipe URLs into structured cooking information.
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Extract a Recipe</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={extractRecipe} className="flex flex-col gap-3 sm:flex-row">
              <Input
                type="url"
                placeholder="Paste a recipe URL..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                required
                className="flex-1"
              />

              <Button type="submit" disabled={loading}>
                {loading ? "Extracting..." : "Extract Recipe"}
              </Button>
            </form>

            {error && (
              <p role="alert" className="mt-4 text-sm text-red-600">
                {error}
              </p>
            )}
          </CardContent>
        </Card>

        {recipe && (
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">
                {recipe.title || "Extracted Recipe"}
              </CardTitle>

              {recipe.description && (
                <p className="text-gray-600">{recipe.description}</p>
              )}
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="flex flex-wrap gap-2">
                {recipe.source_type === "video" && (
  <>
    <Badge className="bg-purple-600 text-white">
      🎥 Video Recipe
    </Badge>

    {recipe.video_platform && (
      <Badge variant="secondary">
        {recipe.video_platform === "instagram"
          ? "Instagram Reel"
          : recipe.video_platform === "youtube"
          ? "YouTube Video"
          : recipe.video_platform}
      </Badge>
    )}

    {recipe.storage?.status === "cached" && (
      <Badge className="bg-blue-600 text-white">
        ⚡ Loaded from Cache
      </Badge>
    )}

    {recipe.storage?.status === "saved" && (
      <Badge className="bg-emerald-600 text-white">
        ✓ Recipe Saved
      </Badge>
    )}
  </>
)}
                
              {recipe.prep_time != null && (
                <Badge variant="secondary">
                  Prep: {displayValue(recipe.prep_time)}
                </Badge>
              )}

              {recipe.cook_time != null && (
                <Badge variant="secondary">
                  Cook: {displayValue(recipe.cook_time)}
                </Badge>
              )}

              {recipe.total_time != null && (
                <Badge variant="secondary">
                  Total: {displayValue(recipe.total_time)}
                </Badge>
              )}

              {recipe.servings != null && (
                <Badge variant="secondary">
                  Servings: {displayValue(recipe.servings)}
                </Badge>
              )}

              </div>

              
            {recipe.ml_prediction && (
              <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
                <h2 className="mb-3 text-lg font-semibold text-emerald-900">
                  AI Meal Classification
                </h2>

                <div className="flex flex-wrap items-center gap-3">
                  <Badge variant="secondary">
                    {recipe.ml_prediction.meal_type ?? "Unknown"}
                  </Badge>

                  {typeof recipe.ml_prediction.confidence === "number" && (
                    <span className="text-sm text-gray-700">
                      Confidence:{" "}
                      <strong>
                        {(recipe.ml_prediction.confidence * 100).toFixed(1)}%
                      </strong>
                    </span>
                  )}
                </div>

                {recipe.ml_prediction.needs_review && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
                    <p className="font-medium text-amber-800">
                      ⚠️ Manual Review Recommended
                    </p>
                    <p className="mt-1 text-sm text-amber-700">
                      {recipe.ml_prediction.message ||
                        "The model is uncertain about this prediction."}
                    </p>
                  </div>
                )}
                <div className="mt-4 space-y-3 border-t pt-4">
  <h3 className="font-semibold">Correct Meal Classification</h3>

  <select
    value={correctedMealType}
    onChange={(event) => setCorrectedMealType(event.target.value)}
    className="w-full rounded-md border bg-white px-3 py-2"
  >
    <option value="">Select correct meal type</option>
    <option value="Breakfast">Breakfast</option>
    <option value="Lunch">Lunch</option>
    <option value="Dinner">Dinner</option>
    <option value="Snack">Snack</option>
    <option value="Dessert">Dessert</option>
  </select>

  <Button
    onClick={saveCorrection}
    disabled={!correctedMealType || savingFeedback}
  >
    {savingFeedback ? "Saving..." : "Save Correction"}
  </Button>

  {feedbackMessage && (
    <p className="text-sm text-emerald-700">
      {feedbackMessage}
    </p>
  )}
</div>
              </section>
            )}


              {recipe.uncertain_details &&
  recipe.uncertain_details.length > 0 && (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-4">
      <h2 className="mb-2 font-semibold text-amber-900">
        ⚠️ Recipe Details to Review
      </h2>

      <ul className="list-disc space-y-1 pl-5 text-sm text-amber-800">
        {recipe.uncertain_details.map((detail, index) => (
          <li key={index}>{detail}</li>
        ))}
      </ul>
    </section>
  )}
              <section>
                <h2 className="mb-3 text-xl font-semibold">
                  Ingredients
                </h2>

                {recipe.ingredients?.length ? (
                  <ul className="space-y-2">
                    {recipe.ingredients.map((ingredient, index) => {
  const details =
    typeof ingredient === "string" ? null : ingredient

  return (
    <li
      key={index}
      className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-100 p-2"
    >
      <input
        type="checkbox"
        className="accent-emerald-600"
      />

      <span className="flex-1">
        {ingredientText(ingredient)}
      </span>

      {recipe.source_type === "video" && details && (
        <>
          {details.verification_status === "text_corroborated" ? (
            <Badge className="bg-emerald-600 text-white">
              ✓ OCR Match
            </Badge>
          ) : details.verification_status === "possible_text_match" ? (
            <Badge className="bg-amber-500 text-white">
              ~ Possible Match
            </Badge>
          ) : (
            <Badge variant="outline">
              Needs Review
            </Badge>
          )}

          {typeof details.ocr_first_seen_seconds === "number" && (
            <span className="text-xs text-gray-500">
              ⏱ {details.ocr_first_seen_seconds}s
            </span>
          )}
        </>
      )}
    </li>
  )
})}
                  </ul>
                ) : (
                  <p className="text-gray-500">No ingredients found.</p>
                )}
              </section>

              <section>
                <h2 className="mb-3 text-xl font-semibold">
                  Cooking Instructions
                </h2>

                {recipe.instructions?.length ? (
                  <ol className="list-decimal space-y-3 pl-5">
                    {recipe.instructions.map((step, index) => (
                      <li key={index}>
                        <div className="flex flex-col gap-1">
                          <span>
                            {typeof step === "string"
                              ? step
                              : step.description ?? step.text ?? ""}
                          </span>

                          {typeof step !== "string" &&
                            typeof step.timestamp_seconds === "number" && (
                              <span className="text-xs text-emerald-700">
                                ⏱ Video timestamp: {step.timestamp_seconds}s
                              </span>
                            )}
                        </div>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-gray-500">
                    No cooking instructions found.
                  </p>
                )}
              </section>
            </CardContent>
          </Card>
        )}
          </>
)}
      </div>
    </main>
  </div>
  )
}

export default App
