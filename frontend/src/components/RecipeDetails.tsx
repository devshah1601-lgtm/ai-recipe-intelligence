
import { useEffect, useState } from "react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

type Ingredient = string | {
  name?: string
  quantity?: string | number | null
  unit?: string | null
  raw?: string | null
}

type Recipe = {
  title?: string
  description?: string
  ingredients?: Ingredient[]
  instructions?: (string | { text?: string })[]
  prep_time_minutes?: number | null
  cook_time_minutes?: number | null
  total_time_minutes?: number | null
  servings?: string | number | null
  cuisine?: string | null
  course?: string | null
  ml_prediction?: {
    meal_type?: string
    confidence?: number
    needs_review?: boolean
  }
}

type RecipeDetailsResponse = {
  id: number
  recipe: Recipe
}

type RecipeDetailsProps = {
  recipeId: number
  onClose: () => void
}


function ingredientText(item: Ingredient): string {
  if (typeof item === "string") {
    return item.trim()
  }

  const quantity =
    item.quantity != null
      ? String(item.quantity).trim()
      : ""

  const unit = item.unit?.trim() ?? ""
  const name = item.name?.trim() ?? ""

  const formatted = [quantity, unit, name]
    .filter(Boolean)
    .join(" ")

  return formatted || item.raw?.trim() || "Unknown ingredient"
}


export default function RecipeDetails({
  recipeId,
  onClose,
}: RecipeDetailsProps) {
  const [data, setData] = useState<RecipeDetailsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const controller = new AbortController()

    async function loadRecipe() {
      setLoading(true)
      setData(null)
      setError("")

      try {
        const response = await fetch(
          `/api/recipes/dataset/saved/${recipeId}`,
          { signal: controller.signal }
        )

        if (!response.ok) {
          throw new Error("Failed to load recipe details.")
        }

        const result: RecipeDetailsResponse =
          await response.json()

        if (!controller.signal.aborted) {
          setData(result)
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Something went wrong."
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadRecipe()

    return () => controller.abort()
  }, [recipeId])

  const recipe = data?.recipe

  return (
    <Card className="border-emerald-200">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-xl">
              {recipe?.title ?? "Recipe Details"}
            </CardTitle>
            <p className="mt-1 text-sm text-gray-500">
              Recipe ID: {recipeId}
            </p>
          </div>

          <Button
            variant="outline"
            size="icon"
            onClick={onClose}
            aria-label="Close recipe details"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 px-6 pb-6">
        {loading && (
          <p className="text-gray-500">
            Loading recipe details...
          </p>
        )}

        {error && (
          <p role="alert" className="text-red-600">
            {error}
          </p>
        )}

        {recipe && (
          <>
            {recipe.description && (
              <p className="text-gray-600">
                {recipe.description}
              </p>
            )}

            <div className="flex flex-wrap gap-2">
              {recipe.ml_prediction?.meal_type && (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-800">
                  {recipe.ml_prediction.meal_type}
                </span>
              )}

              {typeof recipe.ml_prediction?.confidence === "number" && (
                <span className="rounded-full bg-gray-100 px-3 py-1 text-sm">
                  Confidence:{" "}
                  {(recipe.ml_prediction.confidence * 100).toFixed(1)}%
                </span>
              )}

              {recipe.ml_prediction?.needs_review && (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-sm text-amber-800">
                  Needs Review
                </span>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <p className="text-xs text-gray-500">Prep Time</p>
                <p className="font-medium">
                  {recipe.prep_time_minutes != null
                    ? `${recipe.prep_time_minutes} min`
                    : "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-500">Cook Time</p>
                <p className="font-medium">
                  {recipe.cook_time_minutes != null
                    ? `${recipe.cook_time_minutes} min`
                    : "—"}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-500">Servings</p>
                <p className="font-medium">
                  {recipe.servings ?? "—"}
                </p>
              </div>
            </div>

            
{(recipe.cuisine ||
  recipe.course ||
  recipe.total_time_minutes != null) && (
  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
    <h3 className="mb-3 text-sm font-semibold text-gray-800">
      Additional Recipe Information
    </h3>

    <div className="grid gap-4 sm:grid-cols-3">
      {recipe.cuisine && (
        <div>
          <p className="text-xs text-gray-500">Cuisine</p>
          <p className="font-medium text-gray-800">
            {recipe.cuisine}
          </p>
        </div>
      )}

      {recipe.course && (
        <div>
          <p className="text-xs text-gray-500">Course</p>
          <p className="font-medium text-gray-800">
            {recipe.course}
          </p>
        </div>
      )}

      {recipe.total_time_minutes != null && (
        <div>
          <p className="text-xs text-gray-500">Total Time</p>
          <p className="font-medium text-gray-800">
            {recipe.total_time_minutes} min
          </p>
        </div>
      )}
    </div>
  </div>
)}


            
<section className="space-y-4">
  <div className="flex items-center justify-between">
    <h3 className="text-lg font-semibold text-emerald-900">
      Ingredients
    </h3>

    <span className="text-sm text-gray-500">
      {recipe.ingredients?.length ?? 0} items
    </span>
  </div>

  {recipe.ingredients?.length ? (
    <div className="overflow-hidden rounded-xl border border-emerald-100 bg-white">
      {recipe.ingredients.map((item, index) => (
        <label
          key={index}
          className="flex cursor-pointer items-start gap-3 border-b border-gray-100 px-4 py-3 last:border-b-0 hover:bg-emerald-50"
        >
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 accent-emerald-600"
          />

          <span className="text-sm leading-6 text-gray-700">
            {ingredientText(item)}
          </span>
        </label>
      ))}
    </div>
  ) : (
    <p className="text-sm text-gray-500">
      No ingredients available.
    </p>
  )}
</section>


            
<section className="space-y-4">
  <div className="flex items-center justify-between">
    <h3 className="text-lg font-semibold text-emerald-900">
      Cooking Instructions
    </h3>

    <span className="text-sm text-gray-500">
      {recipe.instructions?.length ?? 0} steps
    </span>
  </div>

  {recipe.instructions?.length ? (
    <div className="space-y-3">
      {recipe.instructions.map((step, index) => (
        <div
          key={index}
          className="flex items-start gap-4 rounded-xl border border-gray-200 bg-white p-4"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 font-bold text-emerald-800">
            {index + 1}
          </div>

          <p className="pt-1 text-sm leading-7 text-gray-700">
            {typeof step === "string"
              ? step
              : step.text ?? ""}
          </p>
        </div>
      ))}
    </div>
  ) : (
    <p className="text-sm text-gray-500">
      No instructions available.
    </p>
  )}
</section>

          </>
        )}
      </CardContent>
    </Card>
  )
}
