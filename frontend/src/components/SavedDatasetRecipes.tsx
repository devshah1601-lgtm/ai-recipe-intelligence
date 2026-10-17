
import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import RecipeDetails from "@/components/RecipeDetails"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type DatasetRecipe = {
  id: number
  title: string
  source_record_id?: string | null
  meal_type: string | null
  confidence: number | null
  needs_review: boolean
}

type SavedDatasetResponse = {
  count: number
  recipes: DatasetRecipe[]
}

export default function SavedDatasetRecipes() {
  const [recipes, setRecipes] = useState<DatasetRecipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const [selectedRecipeId, setSelectedRecipeId] =
  useState<number | null>(null)
  
const [search, setSearch] = useState("")
const [reviewOnly, setReviewOnly] = useState(false)

const filteredRecipes = recipes.filter((recipe) => {
  const matchesSearch = recipe.title
    .toLowerCase()
    .includes(search.toLowerCase().trim())

  const matchesReview =
    !reviewOnly || recipe.needs_review === true

  return matchesSearch && matchesReview
})


  async function loadRecipes() {
    setLoading(true)
    setError("")

    try {
      const response = await fetch(
        "/api/recipes/dataset/saved?limit=100"
      )

      if (!response.ok) {
        throw new Error("Failed to load saved recipes.")
      }

      const data: SavedDatasetResponse = await response.json()
      setRecipes(data.recipes)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadRecipes()
  }, [])

  return (
  <div className="space-y-5">
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Saved Dataset Recipes</CardTitle>
            <p className="mt-2 text-sm text-gray-500">
              Browse recipes stored in your SQLite database.
            </p>
          </div>

          <Button
            variant="outline"
            onClick={() => void loadRecipes()}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </Button>
        </div>
      </CardHeader>

      

<div className="mb-4 space-y-3">
  <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
    <div className="min-w-0 flex-1">
      <Input
        type="text"
        placeholder="Search recipes by name..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        className="h-11 w-full rounded-lg"
      />
    </div>

    <Button
      type="button"
      variant={reviewOnly ? "default" : "outline"}
      onClick={() => setReviewOnly(!reviewOnly)}
      className="h-11 shrink-0 rounded-lg px-5"
    >
      {reviewOnly ? "Show All Recipes" : "Needs Review Only"}
    </Button>
  </div>

  <div className="flex flex-wrap items-center justify-between gap-2">
    <p className="text-sm text-gray-500">
      Showing{" "}
      <span className="font-semibold text-gray-800">
        {filteredRecipes.length}
      </span>{" "}
      of {recipes.length} loaded recipes
    </p>

    {reviewOnly && (
      <span className="text-xs font-medium text-amber-700">
        Review filter active
      </span>
    )}
  </div>
</div>



      <CardContent className="pb-6">
  <div className="px-5 sm:px-8">
        {error && (
          <p role="alert" className="mb-4 text-sm text-red-600">
            {error}
          </p>
        )}

        {loading && (
          <p className="text-sm text-gray-500">
            Loading saved recipes...
          </p>
        )}

        {!loading && !error && recipes.length === 0 && (
          <p className="text-sm text-gray-500">
            No dataset recipes saved yet.
          </p>
        )}

        {!loading && !error && recipes.length > 0 && (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-3">ID</th>
                  <th className="p-3">Recipe</th>
                  <th className="p-3">Meal Type</th>
                  <th className="p-3">Confidence</th>
                  <th className="p-3">Needs Review</th>
                </tr>
              </thead>

              <tbody>
                {filteredRecipes.map((recipe) => (
                  
<tr
  key={recipe.id}
  className={`border-b transition-colors duration-200 ${
    selectedRecipeId === recipe.id
      ? "bg-emerald-100"
      : "hover:bg-gray-50"
  }`}
>

                    <td className="p-3">{recipe.id}</td>

                    
<td className="p-3 font-medium">
  
<button
  type="button"
  onClick={() => setSelectedRecipeId(recipe.id)}
  aria-pressed={selectedRecipeId === recipe.id}
  className={`text-left transition-colors hover:underline
    focus-visible:rounded focus-visible:outline-2
    focus-visible:outline-offset-2 focus-visible:outline-emerald-600
    ${
      selectedRecipeId === recipe.id
        ? "font-bold text-emerald-900"
        : "font-medium text-emerald-700"
    }`}
>

    {recipe.title}
  </button>
</td>


                    <td className="p-3">
                      {recipe.meal_type ?? "Unknown"}
                    </td>

                    <td className="p-3">
                      {typeof recipe.confidence === "number"
                        ? `${(recipe.confidence * 100).toFixed(1)}%`
                        : "—"}
                    </td>

                    <td className="p-3">
                      {recipe.needs_review ? (
                        <span className="font-medium text-amber-600">
                          Review
                        </span>
                      ) : (
                        <span className="text-emerald-600">
                          No
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        </div>
</CardContent>
    
    </Card>

    {selectedRecipeId !== null && (
      <RecipeDetails
        recipeId={selectedRecipeId}
        onClose={() => setSelectedRecipeId(null)}
      />
    )}
  </div>
  )
}

