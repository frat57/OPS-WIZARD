"use client"

import useSWR from 'swr'

const fetcher = (url) => fetch(url).then(r => r.json())

function colorForAction(action) {
  if (!action) return 'bg-white'
  if (action === 'BLOCK') return 'bg-red-50 border-red-300'
  if (action === 'REVIEW') return 'bg-yellow-50 border-yellow-300'
  return 'bg-green-50 border-green-300'
}

export default function AlertsPage() {
  const { data, error, mutate } = useSWR('/api/alerts', fetcher)

  const blocked = (data || []).filter(d => d.suggested_action === 'BLOCK').length
  const review = (data || []).filter(d => d.suggested_action === 'REVIEW').length
  const allow = (data || []).filter(d => d.suggested_action === 'ALLOW').length
  const [filter, setFilter] = useState('ALL')

  return (
    <div className="max-w-5xl mx-auto py-8">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Alerts dashboard</h2>
          <p className="text-sm text-slate-500 mt-1">Latest alerts from the AI Ops Wizard — quick triage view.</p>
        </div>
          <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 text-sm">
            <div className="px-3 py-2 rounded bg-red-50 border border-red-200 text-red-700">BLOCK: {blocked}</div>
            <div className="px-3 py-2 rounded bg-yellow-50 border border-yellow-200 text-yellow-700">REVIEW: {review}</div>
            <div className="px-3 py-2 rounded bg-green-50 border border-green-200 text-green-700">ALLOW: {allow}</div>
          </div>
          <select value={filter} onChange={e => setFilter(e.target.value)} className="px-2 py-1 rounded border text-sm">
            <option value="ALL">All</option>
            <option value="BLOCK">BLOCK</option>
            <option value="REVIEW">REVIEW</option>
            <option value="ALLOW">ALLOW</option>
          </select>
          <button onClick={() => mutate()} className="px-3 py-2 rounded bg-indigo-600 text-white text-sm">Refresh</button>
          <button onClick={() => downloadCSV(data)} className="px-3 py-2 rounded bg-gray-700 text-white text-sm">Download CSV</button>
          <a href="http://localhost:8080" target="_blank" rel="noreferrer" className="px-3 py-2 rounded border text-sm">Open Adminer</a>
        </div>
      </header>

      {error && <div className="p-4 rounded bg-red-100 text-red-800">Failed to load alerts: {String(error?.message || error)}</div>}

      {!data && !error && (
        <div className="p-6 bg-white border rounded shadow-sm">
          <div className="h-4 bg-slate-100 rounded w-3/4 mb-4 animate-pulse" />
          <div className="h-3 bg-slate-100 rounded w-1/3 mb-2 animate-pulse" />
          <div className="h-3 bg-slate-100 rounded w-1/2 animate-pulse" />
        </div>
      )}

      {data && Array.isArray(data) && (
        <div className="overflow-auto rounded border bg-white shadow">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700">
              <tr>
                <th className="p-3 text-left">Transaction</th>
                <th className="p-3 text-left">Risk</th>
                <th className="p-3 text-left">Reason</th>
                <th className="p-3 text-left">Action</th>
                <th className="p-3 text-left">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.filter(r => filter === 'ALL' ? true : r.suggested_action === filter).map((row, idx) => (
                <tr key={row.transaction_id || idx} className={`border-b ${colorForAction(row.suggested_action)} border-l-4`}>
                  <td className="p-3 font-medium">{row.transaction_id || '—'}</td>
                  <td className="p-3 font-semibold">{Number(row.risk_score || 0).toFixed(2)}</td>
                  <td className="p-3 text-slate-700 max-w-xl truncate">{row.ai_reason || '—'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${row.suggested_action === 'BLOCK' ? 'bg-red-600 text-white' : row.suggested_action === 'REVIEW' ? 'bg-yellow-400 text-black' : 'bg-green-600 text-white'}`}>{row.suggested_action}</span>
                  </td>
                  <td className="p-3 text-xs text-slate-500">{new Date(row.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function downloadCSV(rows) {
  if (!rows || !rows.length) return
  const header = ['transaction_id', 'risk_score', 'ai_reason', 'suggested_action', 'created_at']
  const csv = [header.join(',')].concat(rows.map(r => [r.transaction_id, r.risk_score, JSON.stringify(r.ai_reason||''), r.suggested_action, r.created_at].map(c=>`"${String(c||'').replace(/"/g,'""')}"`).join(','))).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `alerts-${new Date().toISOString().slice(0,19)}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
