import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

export function useApi<T>(url: string, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get<T>(url)
      setData(res.data)
    } catch (e: any) {
      setError(e.message || 'API 오류')
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => { fetch() }, [fetch, ...deps])

  return { data, loading, error, refetch: fetch }
}

export function fmt_m(k: number) {
  const m = k / 1000
  if (m >= 1000) return `$${(m / 1000).toFixed(1)}B`
  return `$${m.toFixed(0)}M`
}

export function fmt_num(n: number) {
  return n.toLocaleString()
}

export function pct_color(pct: number) {
  if (pct > 0) return 'var(--green)'
  if (pct < 0) return 'var(--red)'
  return 'var(--text2)'
}
