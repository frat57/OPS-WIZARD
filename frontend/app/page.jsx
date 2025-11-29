"use client"

import { useState } from 'react'
import axios from 'axios'

export default function Page() {
  const [id, setId] = useState('evt-' + Math.random().toString(36).slice(2, 9))
  const [payloadText, setPayloadText] = useState(JSON.stringify({ amount: 42, user: { email: 'alice@example.com' } }, null, 2))
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  const N8N_WEBHOOK = process.env.NEXT_PUBLIC_N8N_WEBHOOK || 'http://localhost:5678/webhook/fraud-webhook'

      async function callAnalyze() {
    setLoading(true)
    try {
          const parsed = JSON.parse(payloadText)
          // try to map or pass-through: prefer TransactionData shape
          const tx = {
            amount: parsed.amount ?? parsed.tx_amount ?? 0,
            currency: parsed.currency ?? 'USD',
            merchant: parsed.merchant ?? parsed.shop ?? 'unknown',
            timestamp: parsed.timestamp ?? new Date().toISOString(),
            ip_address: parsed.ip_address ?? parsed.ip ?? '0.0.0.0',
            customer_id: parsed.customer_id ?? parsed.user?.id ?? parsed.user?.email ?? 'anon',
          }

          // POST to our own Next.js server as a proxy: avoids client trying to call container-internal hostnames
          const res = await axios.post(`/api/analyze`, tx, { headers: { 'Content-Type': 'application/json' } })
      setResult(res.data)
    } catch (err) {
      setResult({ error: (err?.response?.data || err.message) })
    } finally {
      setLoading(false)
    }
  }

  async function sendToN8n() {
    setLoading(true)
    try {
      const payload = JSON.parse(payloadText)
      const res = await axios.post(N8N_WEBHOOK, { id, payload }, { headers: { 'Content-Type': 'application/json' } })
      setResult({ forwarded: true, status: res.status, data: res.data })
    } catch (err) {
      setResult({ error: err?.message || String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white p-6 rounded shadow">
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-xs text-slate-500">Event ID</label>
          <input className="w-full rounded border px-3 py-2 mt-1" value={id} onChange={e => setId(e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-slate-500">Backend URL</label>
          <input className="w-full rounded border px-3 py-2 mt-1" value={BACKEND} disabled />
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-slate-500">Payload (JSON)</label>
        <textarea rows={8} className="w-full rounded border px-3 py-2 mt-1 font-mono text-sm" value={payloadText} onChange={e => setPayloadText(e.target.value)} />
      </div>

      <div className="flex gap-3 mb-4">
        <button onClick={callAnalyze} disabled={loading} className="bg-indigo-600 text-white px-4 py-2 rounded">{loading ? 'Working...' : 'Call /analyze'}</button>
        <button onClick={sendToN8n} disabled={loading} className="border px-4 py-2 rounded">Send to n8n webhook</button>
      </div>

      <div className="mt-6 bg-slate-50 p-4 rounded border h-64 overflow-auto">
        <pre className="text-sm font-mono whitespace-pre-wrap">{result ? JSON.stringify(result, null, 2) : 'No result yet'}</pre>
      </div>
    </div>
  )
}
