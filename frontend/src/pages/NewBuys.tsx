import { useApi, fmt_m } from '../hooks/useApi'
import Card from '../components/Card'

interface NewBuy {
  investor_id: string
  investor_name: string
  manager: string
  color: string
  ticker: string | null
  company_name: string
  value_k: number
  value_m: number
  shares: number
  weight_pct: number
  period: string
}

export default function NewBuys() {
  const { data, loading } = useApi<NewBuy[]>('/api/analysis/new-buys')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>🆕 신규 매수 종목</h1>
        <p style={{ color: 'var(--text2)', fontSize: 13 }}>
          최신 분기에 각 거장이 새로 진입한 종목 — 전분기에 없던 포지션
        </p>
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text2)' }}>로딩 중…</div>
      ) : !data?.length ? (
        <Card>
          <div style={{ textAlign: 'center', color: 'var(--text2)', padding: 40 }}>
            데이터가 없습니다. 우측 상단에서 SEC 동기화를 실행하세요.
          </div>
        </Card>
      ) : (
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--surface2)' }}>
                  {['투자자', '종목', '평가액', '비중', '분기'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, color: 'var(--text2)', fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((b, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: b.color, flexShrink: 0 }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13 }}>{b.investor_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text2)' }}>{b.manager}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 700, color: '#10b981' }}>{b.ticker || '—'}</div>
                      <div style={{ fontSize: 11, color: 'var(--text2)' }}>{b.company_name.slice(0, 35)}</div>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontWeight: 600 }}>{fmt_m(b.value_k)}</td>
                    <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>
                      <span style={{
                        color: b.weight_pct >= 5 ? '#f59e0b' : 'var(--text)',
                        fontWeight: b.weight_pct >= 5 ? 700 : 400,
                      }}>
                        {b.weight_pct.toFixed(1)}%
                        {b.weight_pct >= 5 && ' ⭐'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text2)', fontSize: 12 }}>{b.period}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
