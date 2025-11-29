// global styles are in ../styles for the app router
import '../styles/globals.css'

export const metadata = {
  title: 'AI Ops Wizard - Dashboard (MVP)',
  description: 'Minimal dashboard to test AI Core integrations'
}

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <body className="bg-slate-50 min-h-screen p-6">
        <div className="max-w-4xl mx-auto">
          <header className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-semibold">AI Ops Wizard — Dashboard (MVP)</h1>
              <p className="text-sm text-slate-500 mt-1">Demo UI to call the AI core and send events to n8n</p>
            </div>
            <nav>
              <a href="/dashboard/alerts" className="text-sm text-indigo-600 hover:underline">View Alerts →</a>
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  )
}
