import { NextResponse } from 'next/server'

export async function GET() {
  // Robust proxy: try multiple candidate backends (useful for dev inside or outside Docker)
  const candidates = []
  if (process.env.NEXT_PUBLIC_BACKEND_URL) candidates.push(process.env.NEXT_PUBLIC_BACKEND_URL.replace(/\/$/, ''))
  candidates.push('http://api:8000') // typical container internal name
  candidates.push('http://localhost:8000') // fallback for host dev

  const tried = []
  // small helper to apply a timeout
  const fetchWithTimeout = (url, opts = {}, ms = 5000) => {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), ms)
    return fetch(url, { signal: controller.signal, ...opts }).finally(() => clearTimeout(id))
  }

  for (const base of candidates) {
    if (!base) continue
    const url = `${base}/alerts`
    tried.push(url)
    try {
      const res = await fetchWithTimeout(url, { cache: 'no-store' }, 5000)
      if (!res.ok) {
        // try next candidate
        console.error(`proxy call to ${url} returned status ${res.status}`)
        continue
      }
      const json = await res.json()
      return NextResponse.json(json)
    } catch (err) {
      console.error(`proxy call to ${url} failed:`, err?.message || err)
      // continue to next candidate
    }
  }

  return NextResponse.json({ error: 'fetch failed', tried }, { status: 502 })
}
