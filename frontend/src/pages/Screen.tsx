import { useState } from 'react'
import { useApi, fmt_m } from '../hooks/useApi'
import Card from '../components/Card'

type Tab = 'beaten' | 'conviction'

interface BeatenItem {
  investor_id: string
  investor_name: string
  manager: string
  ticker: string | null
  company_name: string
  avg_cost_est: number
  current_price: number
  discount_pct: number
  value_k: number
  period: string
}

interface ConvictionItem {
  investor_id: string
  investor_name: string
  manager: string
  ticker: string | null
  company_name: string
  weight_pct: number
  value_k: number
  period: string
}

export default function Screen() {
  const [tab, setTab] = useState<Tab>('conviction')
  const { data: beaten, loading: bl } = useApi<BeatenItem[]>('/api/analysis/beaten-down')
  const { data: conviction, loading: cl } = useApi<ConvictionItem[]>('/api/analysis/high-conviction')

  const tabs: { id: Tab; label: string; desc: string }[] = [
    { id: 'conviction', label: '⭐ 고비중 신규 진입', desc: '포트폴리오 비중 5% 이상으로 처음 담은 종목 — 확신도 높음' },
    { id: 'beaten', label: '📉 가격 폭락 기회', desc: '현재가 < 기관 평균 매수가 추정치 — 기관보다 싸게 살 기회' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>🔍 투자 스크리닝</h1>
        <p style={{ color: 'var(--text2)', fontSize: 13 }}>
          13F 4단계 전략의 3단계: 매수 후보군 필터링
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: '8px 16px',
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: tab === t.id ? '#3b82f620' : 'var(--surface)',
            color: tab === t.id ? '#3b82f6' : 'var(--text2)',
            cursor: 'pointer',
            fontWeight: tab === t.id ? 700 : 400,
            fontSize: 13,
          }}>
            {t.label}
          </button>
        ))}
      </div>

      <p style={{ color: 'var(--text2)', fontSize: 12 }}>
        {tabs.find(t => t.id === tab)?.desc}
      </p>

      {tab === 'conviction' && (
        <>
          {cl ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text2)' }}>로딩 중…</div> : !conviction?.length ? (
            <Card><div style={{ textAlign: 'center', color: 'var(--text2)', padding: 40 }}>데이터 없음</div></Card>
          ) : (
            <Card style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'var(--surface2)' }}>
                      {['투자자', '종목', '포트폴리오 비중', '투자액', '분기'].map(h => (
                        <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, color: 'var(--text2)', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {conviction.map((item, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 600 }}>{item.investor_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text2)' }}>{item.manager}</div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 700, color: '#f59e0b' }}>{item.ticker || '—'}</div>
                          <div style={{ fontSize: 11, color: 'var(--text2)' }}>{item.company_name.slice(0, 30)}</div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              height: 6, width: Math.min(120, item.weight_pct * 4),
                              background: '#f59e0b', borderRadius: 3,
                            }} />
                            <span style={{ fontWeight: 700, color: '#f59e0b', fontFamily: 'monospace' }}>
                              {item.weight_pct.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px', fontFamily: 'monospace' }}>{fmt_m(item.value_k)}</td>
                        <td style={{ padding: '12px 16px', color: 'var(--text2)', fontSize: 12 }}>{item.period}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {tab === 'beaten' && (
        <>
          {bl ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text2)' }}>로딩 중…</div> : !beaten?.length ? (
            <Card>
              <div style={{ textAlign: 'center', color: 'var(--text2)', padding: 40 }}>
                데이터 없음 (현재가 업데이트 필요: 동기화 후 가격 데이터 반영 시간 소요)
              </div>
            </Card>
          ) : (
            <Card style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'var(--surface2)' }}>
                      {['투자자', '종목', '기관 평균매수가(추정)', '현재가', '할인율', '분기'].map(h => (
                        <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 12, color: 'var(--text2)', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {beaten.map((item, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 600 }}>{item.investor_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text2)' }}>{item.manager}</div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ fontWeight: 700, color: '#ef4444' }}>{item.ticker || '—'}</div>
                          <div style={{ fontSize: 11, color: 'var(--text2)' }}>{item.company_name.slice(0, 30)}</div>
                        </td>
                        <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--text2)' }}>
                          ${item.avg_cost_est.toFixed(2)}
                        </td>
                        <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#ef4444', fontWeight: 700 }}>
                          ${item.current_price.toFixed(2)}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{
                            background: '#ef444420', color: '#ef4444',
                            borderRadius: 6, padding: '3px 8px', fontWeight: 700, fontSize: 13,
                          }}>
                            -{item.discount_pct.toFixed(1)}%
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: 'var(--text2)', fontSize: 12 }}>{item.period}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}

      {/* Notice */}
      <Card style={{ borderLeft: '3px solid #f59e0b', background: '#1a1500' }}>
        <div style={{ fontSize: 12, color: '#aaa820', lineHeight: 1.8 }}>
          ⚠️ <strong>주의:</strong> "평균 매수가"는 13F 공시 시점의 value÷shares로 추정한 값입니다.
          실제 매수가와 다를 수 있으며(분기 중 누적 매수 등), 투자 결정의 보조 참고 자료로만 활용하세요.
          최종 매수 전 반드시 기업 펀더멘털 분석을 진행하세요.
        </div>
      </Card>
    </div>
  )
}
