import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useApi, fmt_m, fmt_num, pct_color } from '../hooks/useApi'
import Card from '../components/Card'

interface Holding {
  id: number
  ticker: string | null
  cusip: string
  company_name: string
  shares: number
  value_k: number
  value_m: number
  weight_pct: number
  shares_change: number
  value_change_k: number
  is_new: boolean
  is_sold: boolean
  current_price: number | null
}

interface PortfolioData {
  investor: { name: string; manager: string; style: string; color: string }
  period: string
  filed_at: string
  total_value_k: number
  total_value_b: number
  holdings: Holding[]
}

function ChangeTag({ is_new, shares_change }: { is_new: boolean; shares_change: number }) {
  if (is_new) return <span style={{ background: '#10b98120', color: '#10b981', borderRadius: 4, padding: '2px 7px', fontSize: 11, fontWeight: 700 }}>NEW</span>
  if (shares_change > 0) return <span style={{ background: '#3b82f620', color: '#3b82f6', borderRadius: 4, padding: '2px 7px', fontSize: 11 }}>▲ 증가</span>
  if (shares_change < 0) return <span style={{ background: '#ef444420', color: '#ef4444', borderRadius: 4, padding: '2px 7px', fontSize: 11 }}>▼ 감소</span>
  return <span style={{ color: 'var(--text2)', fontSize: 11 }}>유지</span>
}

export default function Portfolio() {
  const { id } = useParams<{ id: string }>()
  const { data, loading, error } = useApi<PortfolioData>(`/api/investors/${id}/holdings`)

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text2)' }}>로딩 중…</div>
  if (error) return <div style={{ padding: 40, color: 'var(--red)' }}>오류: {error}</div>
  if (!data) return null

  const [newOnly, setNewOnly] = useState(false)

  const inv = data.investor
  const holdings = data.holdings.filter(h => !h.is_sold)
  const newBuys = holdings.filter(h => h.is_new)
  const displayed = newOnly ? newBuys : holdings

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{
          width: 52, height: 52, borderRadius: 12,
          background: inv.color + '20', border: `2px solid ${inv.color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, fontWeight: 700, color: inv.color,
        }}>
          {inv.manager.charAt(0)}
        </div>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>{inv.name}</h1>
          <div style={{ color: inv.color, fontSize: 13 }}>{inv.manager} · {inv.style}</div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: '운용 규모', value: fmt_m(data.total_value_k) },
          { label: '보유 종목', value: `${holdings.length}개` },
          { label: '신규 매수', value: `${newBuys.length}개`, clickable: true },
          { label: '분기', value: data.period },
        ].map(s => (
          <Card
            key={s.label}
            onClick={s.clickable && newBuys.length > 0 ? () => setNewOnly(v => !v) : undefined}
            style={s.clickable && newBuys.length > 0 ? { cursor: 'pointer', outline: newOnly ? `2px solid ${inv.color}` : 'none' } : {}}
          >
            <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontWeight: 700, fontSize: 18, color: inv.color }}>{s.value}</div>
            {s.clickable && newOnly && <div style={{ fontSize: 10, color: inv.color, marginTop: 2 }}>필터 중 ✓</div>}
          </Card>
        ))}
      </div>

      {/* Holdings Table */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>
          포트폴리오 상세 ({data.period} 기준)
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--surface2)' }}>
                {['순위', '종목', '변동', '보유 주식', '평가액', '비중', '현재가'].map(h => (
                  <th key={h} style={{
                    padding: '10px 14px', textAlign: 'left', fontSize: 12,
                    color: 'var(--text2)', fontWeight: 600, whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayed.map((h, i) => (
                <tr key={h.id} style={{
                  borderBottom: '1px solid var(--border)',
                  background: h.is_new ? '#10b98108' : 'transparent',
                }}>
                  <td style={{ padding: '10px 14px', color: 'var(--text2)', fontSize: 12 }}>{i + 1}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600 }}>{h.ticker || '—'}</div>
                    <div style={{ fontSize: 11, color: 'var(--text2)' }}>{h.company_name.slice(0, 30)}</div>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <ChangeTag is_new={h.is_new} shares_change={h.shares_change} />
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace' }}>
                    <div>{fmt_num(h.shares)}</div>
                    {h.shares_change !== 0 && (
                      <div style={{ fontSize: 11, color: pct_color(h.shares_change) }}>
                        {h.shares_change > 0 ? '+' : ''}{fmt_num(h.shares_change)}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace' }}>
                    {fmt_m(h.value_k)}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        height: 4, width: Math.max(4, Math.min(80, h.weight_pct * 3)),
                        background: inv.color, borderRadius: 2,
                      }} />
                      <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{h.weight_pct.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: 'var(--text2)' }}>
                    {h.current_price ? `$${h.current_price.toFixed(2)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
