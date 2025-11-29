import { NextResponse } from 'next/server'

export async function POST(req) {
  const candidates = []
  if (process.env.NEXT_PUBLIC_BACKEND_URL) candidates.push(process.env.NEXT_PUBLIC_BACKEND_URL.replace(/\/$/, ''))
  candidates.push('http://api:8000')
  candidates.push('http://localhost:8000')

  const body = await req.json().catch(() => null)
  const tried = []

  for (const base of candidates) {
    if (!base) continue
    const url = `${base}/analyze`
    tried.push(url)
    try {
      const res = await fetch(url, { method: 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' }, cache: 'no-store' })
      const text = await res.text().catch(() => null)
      // if backend returned a valid body (error or success) forward it
      if (res.ok) {
        const json = text ? JSON.parse(text) : {}
        return NextResponse.json(json)
      } else {
        // forward error status + body if possible
        try {
          const jsonErr = text ? JSON.parse(text) : { error: text }
          return NextResponse.json(jsonErr, { status: res.status })
        } catch (e) {
          return NextResponse.json({ error: text || 'backend error' }, { status: res.status })
        }
      }
    } catch (err) {
      // try next candidate
    }
  }

  return NextResponse.json({ error: 'fetch failed', tried }, { status: 502 })
}
