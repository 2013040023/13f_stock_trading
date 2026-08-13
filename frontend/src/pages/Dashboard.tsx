import { useNavigate } from 'react-router-dom'
import { useApi, fmt_m } from '../hooks/useApi'
import Card from '../components/Card'

interface Investor {
  id: string
  name: string
  manager: string
  style: string
  color: string
  latest_period: string | null
  latest_filed: string | null
  total_value_k: number
  total_value_m: number
  holdings_count: number
}

const STRATEGY_GUIDE = [
  { step: '1단계', title: '거장 선별', desc: '장기 가치투자 스타일 기관만 추적 (단타 헤지펀드 제외)' },
  { step: '2단계', title: '데이터 분석', desc: 'SEC EDGAR 13F 공시에서 분기별 포트폴리오 변화 추적' },
  { step: '3단계', title: '필터링', desc: '컨센서스 매수 · 고비중 신규 진입 · 현재가<매수가 종목 발굴' },
  { step: '4단계', title: '검증 후 매수', desc: '펀더멘털 확인 → 가격 메리트 확인 → 분할 매수 실행' },
]

export default function Dashboard() {
  const { data: investors, loading } = useApi<Investor[]>('/api/investors')
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>
          📊 13F 거장 포트폴리오 대시보드
        </h1>
        <p style={{ color: 'var(--text2)', fontSize: 13 }}>
          SEC 13F 공시 기반 · 분기별 업데이트 · 장기 가치투자 거장 5인 추적
        </p>
      </div>

      {/* Investor Cards */}
      <section>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: 'var(--text2)' }}>
          추적 중인 투자자
        </h2>
        {loading ? (
          <div style={{ color: 'var(--text2)', padding: 40, textAlign: 'center' }}>
            데이터 로딩 중…
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {(investors || []).map(inv => (
              <Card key={inv.id} onClick={() => navigate(`/investor/${inv.id}`)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10,
                    background: inv.color + '20',
                    border: `2px solid ${inv.color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18, fontWeight: 700, color: inv.color,
                  }}>
                    {inv.manager.charAt(0)}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>{inv.name}</div>
                    <div style={{ color: inv.color, fontSize: 12 }}>{inv.manager}</div>
                  </div>
                </div>

                <div style={{
                  background: '#00000030',
                  borderRadius: 8,
                  padding: '6px 10px',
                  marginBottom: 14,
                  fontSize: 11,
                  color: 'var(--text2)',
                }}>
                  {inv.style}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text2)' }}>운용 규모</div>
                    <div style={{ fontWeight: 700, fontSize: 16, color: inv.color }}>
                      {inv.total_value_k > 0 ? fmt_m(inv.total_value_k) : '—'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text2)' }}>보유 종목</div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>
                      {inv.holdings_count > 0 ? `${inv.holdings_count}개` : '—'}
                    </div>
                  </div>
                </div>

                {inv.latest_period && (
                  <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text2)', borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                    최신 분기: {inv.latest_period} | 공시: {inv.latest_filed}
                  </div>
                )}
                {!inv.latest_period && (
                  <div style={{ marginTop: 12, fontSize: 11, color: '#f59e0b', borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                    ⚠️ 데이터 없음 — 우측 상단 '동기화' 클릭
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Strategy Guide */}
      <section>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: 'var(--text2)' }}>
          📋 13F 4단계 투자 전략
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
          {STRATEGY_GUIDE.map(s => (
            <Card key={s.step} style={{ borderLeft: '3px solid #3b82f6' }}>
              <div style={{ fontSize: 11, color: '#3b82f6', fontWeight: 700, marginBottom: 6 }}>{s.step}</div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{s.title}</div>
              <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.6 }}>{s.desc}</div>
            </Card>
          ))}
        </div>
      </section>

      {/* Warnings */}
      <section>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: 'var(--text2)' }}>
          ⚠️ 반드시 알아야 할 13F 한계점
        </h2>
        <Card style={{ borderLeft: '3px solid #f59e0b' }}>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              '최대 45일 시차: 분기 종료 후 45일 이내 공시 → 이미 포지션 청산했을 수도 있음',
              '롱 포지션만 공개: 공매도·현금·해외주식·채권 정보 없음',
              '공매도 헤지 가능성: 매수 ≠ 강세론 (헤지 목적일 수도 있음)',
              '단타 헤지펀드 제외: 45일 전 데이터는 초단타 펀드에 무의미',
            ].map((w, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, fontSize: 13 }}>
                <span style={{ color: '#f59e0b', flexShrink: 0 }}>•</span>
                <span style={{ color: 'var(--text2)' }}>{w}</span>
              </li>
            ))}
          </ul>
        </Card>
      </section>
    </div>
  )
}
