
import { useState, type ChangeEvent } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Upload, Download, FileSpreadsheet } from "lucide-react"


type UploadMode = "urls" | "dataset"

type RecipeResult = {
  row: number
  url?: string
  status: "success" | "error"
  error?: string
  database_status?: "saved" | "duplicate"
  database_id?: number
  recipe?: {
    title?: string
    source_url?: string
    ml_prediction?: {
      meal_type?: string
      confidence?: number
      needs_review?: boolean
    }
  }
}

type BatchResponse = {
  total: number
  successful: number
  failed: number
  saved?: number
  duplicates?: number
  results: RecipeResult[]
}


export default function BulkCSV() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [data, setData] = useState<BatchResponse | null>(null)
  const [mode, setMode] = useState<UploadMode>("urls")

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null)
    setData(null)
    setError("")
  }

  async function handleUpload() {
    if (!file) return

    setLoading(true)
    setError("")
    setData(null)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const endpoint =
  mode === "dataset"
    ? "/api/recipes/import-csv"
    : "/api/recipes/csv"

const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : "CSV processing failed."
        )
      }

      setData(result)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      )
    } finally {
      setLoading(false)
    }
  }

  function downloadJSON() {
    if (!data) return

    const blob = new Blob(
      [JSON.stringify(data, null, 2)],
      { type: "application/json" }
    )

    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "recipe_results.json"
    link.click()
    URL.revokeObjectURL(url)
  }

  
function downloadCSV() {
  if (!data) return

  const escapeCSV = (value: unknown) => {
    const text = String(value ?? "")
    return `"${text.replace(/"/g, '""')}"`
  }

  const headers = [
    "Row",
    "URL",
    "Status",
    "Database Status",
    "Database ID",
    "Recipe Title",
    "Meal Type",
    "Confidence",
    "Needs Review",
    "Error",
  ]

  const rows = data.results.map((item) => [
    item.row,
    item.url ?? item.recipe?.source_url ?? "",
    item.status,
    item.database_status ?? "",
    item.database_id ?? "",
    item.recipe?.title ?? "",
    item.recipe?.ml_prediction?.meal_type ?? "",
    item.recipe?.ml_prediction?.confidence ?? "",
    item.recipe?.ml_prediction?.needs_review ?? "",
    item.error ?? "",
  ])

  const csv = [
    headers.map(escapeCSV).join(","),
    ...rows.map((row) => row.map(escapeCSV).join(",")),
  ].join("\r\n")

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8;",
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")

  link.href = url
  link.download =
    mode === "dataset"
      ? "dataset_recipe_results.csv"
      : "url_recipe_results.csv"

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}



const needsReviewCount =
  data?.results.filter(
    (item) =>
      item.status === "success" &&
      item.recipe?.ml_prediction?.needs_review === true
  ).length ?? 0


  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-emerald-900">
          Bulk CSV Processing
        </h1>
        
<p className="mt-2 text-gray-600">
  {mode === "dataset"
    ? "Import recipe datasets, enrich them using machine learning, and detect duplicates."
    : "Upload a CSV containing recipe URLs and process them together."}
</p>

      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="text-emerald-600" />
            {mode === "urls" ? "Upload Recipe URLs" : "Upload Recipe Dataset"}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          
<div className="grid gap-3 sm:grid-cols-2">
  <Button
    type="button"
    variant={mode === "urls" ? "default" : "outline"}
    onClick={() => {
      setMode("urls")
      setFile(null)
      setData(null)
      setError("")
    }}
  >
    Recipe URL CSV
  </Button>

  <Button
    type="button"
    variant={mode === "dataset" ? "default" : "outline"}
    onClick={() => {
      setMode("dataset")
      setFile(null)
      setData(null)
      setError("")
    }}
  >
    Recipe Dataset CSV
  </Button>
</div>

          
<p className="text-sm text-gray-600">
  {mode === "urls"
    ? "Upload a CSV containing a url column with recipe website links."
    : "Upload a recipe dataset CSV containing recipe names, ingredients, and instructions. Maximum 1,000 rows and 10 MB."}
</p>


          <Input
  key={mode}
  type="file"
  accept=".csv,text/csv"
  onChange={handleFileChange}
/>

          <Button
            onClick={handleUpload}
            disabled={!file || loading}
          >
            <Upload className="mr-2 h-4 w-4" />
            {loading ? "Processing..." : "Process CSV"}
          </Button>

          {error && (
            <p role="alert" className="text-sm text-red-600">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {data && (
        <>
          
<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {[
    {
      label: "Total",
      value: data.total,
      color: "text-gray-900",
    },
    {
      label: "Successful",
      value: data.successful,
      color: "text-emerald-600",
    },
    {
      label: "Failed",
      value: data.failed,
      color: "text-red-600",
    },
    ...(mode === "dataset"
      ? [
          {
            label: "Saved",
            value: data.saved ?? 0,
            color: "text-blue-600",
          },
          {
            label: "Duplicates",
            value: data.duplicates ?? 0,
            color: "text-amber-600",
          },
          {
            label: "Needs Review",
            value: needsReviewCount,
            color: "text-orange-600",
          },
        ]
      : []),
  ].map((stat) => (
    <Card key={stat.label}>
      <CardContent className="pt-6">
        <p className="text-sm text-gray-500">
          {stat.label}
        </p>
        <p className={`text-3xl font-bold ${stat.color}`}>
          {stat.value}
        </p>
      </CardContent>
    </Card>
  ))}
</div>


          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle>Processing Results</CardTitle>
                <div className="flex flex-wrap gap-2">
                    <Button variant="outline" onClick={downloadCSV}>
                    <Download className="mr-2 h-4 w-4" />
                        Download CSV
                    </Button>

                    <Button variant="outline" onClick={downloadJSON}>
                    <Download className="mr-2 h-4 w-4" />
                        Download JSON
                    </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  
<thead>
  <tr className="border-b">
    <th className="p-3">Row</th>
    <th className="p-3">Recipe</th>
    <th className="p-3">Status</th>
    {mode === "dataset" && (
      <th className="p-3">Database Status</th>
    )}
    <th className="p-3">Meal Type</th>
    <th className="p-3">Confidence</th>
    <th className="p-3">Needs Review</th>
  </tr>
</thead>


                  
<tbody>
  {data.results.map((item, index) => (
    <tr key={`${item.row}-${index}`} className="border-b">
      <td className="p-3">{item.row}</td>

      <td className="p-3">
        <span className="font-medium">
          {item.recipe?.title ?? item.url ?? "Unknown recipe"}
        </span>
        {item.error && (
          <p className="mt-1 text-xs text-red-600">
            {item.error}
          </p>
        )}
      </td>

      <td className="p-3">
        {item.status === "success" ? (
          <span className="font-medium text-emerald-600">
            Success
          </span>
        ) : (
          <span className="font-medium text-red-600">
            Failed
          </span>
        )}
      </td>

      {mode === "dataset" && (
        <td className="p-3">
          {item.database_status === "saved" ? (
            <span className="font-medium text-blue-600">
              Saved
            </span>
          ) : item.database_status === "duplicate" ? (
            <span className="font-medium text-amber-600">
              Duplicate
            </span>
          ) : (
            "—"
          )}
        </td>
      )}

      <td className="p-3">
        {item.recipe?.ml_prediction?.meal_type ?? "—"}
      </td>

      <td className="p-3">
        {typeof item.recipe?.ml_prediction?.confidence === "number"
          ? `${(
              item.recipe.ml_prediction.confidence * 100
            ).toFixed(1)}%`
          : "—"}
      </td>

      <td className="p-3">
        {item.recipe?.ml_prediction?.needs_review === true ? (
          <span className="font-medium text-orange-600">
            Review
          </span>
        ) : item.recipe?.ml_prediction ? (
          <span className="text-emerald-600">No</span>
        ) : (
          "—"
        )}
      </td>
    </tr>
  ))}
</tbody>

                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
