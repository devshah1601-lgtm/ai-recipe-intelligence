
import {
  LayoutDashboard,
  Link2,
  FileSpreadsheet,
  Video,
  BrainCircuit,
  ChefHat,
} from "lucide-react"

export type Page =
  | "dashboard"
  | "extractor"
  | "csv"
  | "video"
  | "review"

type SidebarProps = {
  activePage: Page
  onNavigate: (page: Page) => void
}

const menuItems: {
  id: Page
  label: string
  icon: typeof LayoutDashboard
  available: boolean
}[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    available: true,
  },
  {
    id: "extractor",
    label: "Recipe Extractor",
    icon: Link2,
    available: true,
  },
  {
    id: "csv",
    label: "Bulk CSV",
    icon: FileSpreadsheet,
    available: true,
  },
  {
    id: "video",
    label: "Video to Recipe",
    icon: Video,
    available: false,
  },
  {
    id: "review",
    label: "Model Review",
    icon: BrainCircuit,
    available: true,
  },
]

export default function Sidebar({
  activePage,
  onNavigate,
}: SidebarProps) {
  return (
    <aside className="w-full border-b border-emerald-100 bg-white p-4 md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="mb-8 flex items-center gap-3">
        <div className="rounded-xl bg-emerald-600 p-2 text-white">
          <ChefHat size={24} />
        </div>

        <div>
          <h2 className="font-bold text-emerald-900">
            Recipe Intelligence
          </h2>
          <p className="text-xs text-gray-500">
            AI Cooking Platform
          </p>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto md:flex-col">
        {menuItems.map((item) => {
          const Icon = item.icon
          const selected = activePage === item.id

          return (
            <button
              key={item.id}
              type="button"
              disabled={!item.available}
              onClick={() => onNavigate(item.id)}
              className={`flex shrink-0 items-center gap-3 rounded-lg px-4 py-3 text-left text-sm transition ${
                selected
                  ? "bg-emerald-100 font-semibold text-emerald-800"
                  : "text-gray-600 hover:bg-gray-100"
              } ${
                !item.available
                  ? "cursor-not-allowed opacity-45"
                  : ""
              }`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {!item.available && (
                <span className="text-[10px]">
                  Soon
                </span>
              )}
            </button>
          )
        })}
      </nav>

      <div className="mt-10 hidden rounded-xl bg-emerald-50 p-4 md:block">
        <p className="text-sm font-semibold text-emerald-900">
          Local AI Platform
        </p>
        <p className="mt-1 text-xs text-gray-600">
          Built with React, FastAPI, and machine learning.
        </p>
      </div>
    </aside>
  )
}
