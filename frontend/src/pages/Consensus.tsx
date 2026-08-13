import { useState } from 'react'
import { useApi, fmt_m } from '../hooks/useApi'
import Card from '../components/Card'

interface ConsensusItem {
  cusip: string
  ticker: string | null
  company_name: string
  investor_count: number
  investors: { investor_name: string; manager: string; color: string; value: number }[]
  total_value_k: number
}

export default function Consensus() {
  const [minInvestors, setMinInvestors] = useState(2)
  const { data, loading } = useApi<ConsensusItem[]>(`/api/analysis/consensus?min_investors=${minInvestors}`, [minInvestors])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>🎯 컨센서스 매수</h1>
        <p style={{ color: 'var(--text2)', fontSize: 13 }}>
          같은 분기에 여러 거장이 동시에 신규 매수한 종목 — 가장 강력한 시그널
        </p>
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span style={{ color: 'var(--text2)', fontSize: 13 }}>최소 투자자 수:</span>
        {[2, 3, 4, 5].map(n => (
          <button key={n} onClick={() => setMinInvestors(n)} style={{
            padding: '6px 14px',
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: minInvestors === n ? '#3b82f6' : 'var(--surface2)',
            color: minInvestors === n ? '#fff' : 'var(--text2)',
            cursor: 'pointer',
            fontWeight: minInvestors === n ? 700 : 400,
            fontSize: 13,
          }}>
            {n}명 이상
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text2)' }}>로딩 중…</div>
      ) : !data?.length ? (
        <Card>
          <div style={{ textAlign: 'center', color: 'var(--text2)', padding: 40 }}>
            {minInvestors}명 이상 동시 신규 매수 종목 없음 (데이터 없을 경우 SEC 동기화 먼저 실행)
          </div>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {data.map((item, i) => (
            <Card key={item.cusip}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 20, fontWeight: 700, color: '#10b981' }}>
                      {item.ticker || '—'}
                    </span>
                    <span style={{
                      background: '#10b98120', color: '#10b981',
                      borderRadius: 6, padding: '2px 8px', fontSize: 12, fontWeight: 700,
                    }}>
                      {item.investor_count}명 동시 매수
                    </span>
                  </div>
                  <div style={{ color: 'var(--text2)', fontSize: 12, marginBottom: 12 }}>
                    {item.company_name}
                  </div>
                  {/* Investor dots */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {item.investors.map((inv, j) => (
                      <div key={j} style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        background: 'var(--surface2)', borderRadius: 20,
                        padding: '4px 10px',
                      }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: inv.color || '#888' }} />
                        <span style={{ fontSize: 12 }}>{inv.manager}</span>
                        <span style={{ fontSize: 11, color: 'var(--text2)' }}>{fmt_m(inv.value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 11, color: 'var(--text2)' }}>총 매수액</div>
                  <div style={{ fontWeight: 700, fontSize: 18, color: '#3b82f6' }}>{fmt_m(item.total_value_k)}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
