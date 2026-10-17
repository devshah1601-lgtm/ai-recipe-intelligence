
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import SavedDatasetRecipes from "@/components/SavedDatasetRecipes"
import {
  ChefHat,
  ClipboardCheck,
  AlertTriangle,
  ArrowRight,
} from "lucide-react"

type DashboardProps = {
  onOpenExtractor: () => void
}

type RecipeStats = {
  total_recipes: number
  needs_review: number
}

type DatasetStats = {
  total_recipes: number
  needs_review: number
}

type SavedRecipe = {
  id: number
  title: string
  updated_at: string
}

export default function Dashboard({
  onOpenExtractor,
}: DashboardProps) {
  const [stats, setStats] = useState<RecipeStats | null>(null)
  const [datasetStats, setDatasetStats] =
  useState<DatasetStats | null>(null)
  const [latestRecipe, setLatestRecipe] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadDashboard() {
      try {
        
const [
  statsResponse,
  recipesResponse,
  datasetResponse,
] = await Promise.all([
  fetch("/api/recipes/stats"),
  fetch("/api/recipes/saved"),
  fetch("/api/recipes/dataset/stats"),
])


        if (
  !statsResponse.ok ||
  !recipesResponse.ok ||
  !datasetResponse.ok
) {
  throw new Error("Failed to load dashboard data.")
}

        const statsData: RecipeStats = await statsResponse.json()
        const recipesData: { recipes: SavedRecipe[] } =
          await recipesResponse.json()

        setStats(statsData)
        setLatestRecipe(recipesData.recipes?.[0]?.title ?? null)

        const datasetData: DatasetStats = await datasetResponse.json()
setDatasetStats(datasetData)
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

    loadDashboard()
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-emerald-900">
          Dashboard Overview
        </h1>
        <p className="mt-2 text-gray-600">
          Your recipe intelligence workspace.
        </p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <ChefHat className="text-emerald-600" />
            <CardTitle className="text-sm">
              Recipes Extracted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {loading ? "..." : stats?.total_recipes ?? 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <AlertTriangle className="text-amber-600" />
            <CardTitle className="text-sm">
              Needs Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {loading ? "..." : stats?.needs_review ?? 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ClipboardCheck className="text-blue-600" />
            <CardTitle className="text-sm">
              Latest Recipe
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-semibold">
              {loading ? "Loading..." : latestRecipe ?? "None yet"}
            </p>
          </CardContent>
        </Card>
      </div>

      
<div className="space-y-4">
  <h2 className="text-xl font-semibold text-emerald-900">
    Dataset Recipes
  </h2>

  <div className="grid gap-4 md:grid-cols-2">
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">
          Saved Dataset Recipes
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-emerald-600">
          {loading ? "..." : datasetStats?.total_recipes ?? 0}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Total recipes stored from dataset imports.
        </p>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle className="text-sm">
          Dataset Needs Review
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-amber-600">
          {loading ? "..." : datasetStats?.needs_review ?? 0}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Imported recipes flagged for manual review.
        </p>
      </CardContent>
    </Card>
  </div>
</div>

<SavedDatasetRecipes />
      <Card>
        <CardHeader>
          <CardTitle>Start Processing</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-gray-600">
            Extract ingredients, cooking instructions, and
            machine-learning predictions from a recipe URL.
          </p>
          <Button onClick={onOpenExtractor}>
            Open Recipe Extractor
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
