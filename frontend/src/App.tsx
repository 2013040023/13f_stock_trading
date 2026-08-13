import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Consensus from './pages/Consensus'
import NewBuys from './pages/NewBuys'
import Screen from './pages/Screen'
import axios from 'axios'

const NAV = [
  { to: '/', label: '대시보드', exact: true },
  { to: '/new-buys', label: '신규 매수' },
  { to: '/consensus', label: '컨센서스' },
  { to: '/screen', label: '스크리닝' },
]

function SyncButton() {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const handleSync = async () => {
    setLoading(true)
    setDone(false)
    try {
      await axios.post('/api/sync/all')
      setDone(true)
      setTimeout(() => setDone(false), 3000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button onClick={handleSync} disabled={loading} style={{
      background: loading ? '#2a2a3a' : '#3b82f6',
      color: '#fff',
      border: 'none',
      borderRadius: 8,
      padding: '7px 16px',
      cursor: loading ? 'not-allowed' : 'pointer',
      fontSize: 13,
      fontWeight: 600,
      transition: 'background 0.2s',
    }}>
      {loading ? '동기화 중…' : done ? '✓ 완료' : '🔄 SEC 동기화'}
    </button>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
        {/* Nav */}
        <nav style={{
          background: 'var(--surface)',
          borderBottom: '1px solid var(--border)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          height: 56,
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}>
          <span style={{ fontWeight: 700, fontSize: 16, color: '#fff', marginRight: 16 }}>
            📊 13F 거장 트래커
          </span>
          {NAV.map(n => (
            <NavLink key={n.to} to={n.to} end={n.exact} style={({ isActive }) => ({
              padding: '6px 14px',
              borderRadius: 8,
              background: isActive ? '#3b82f620' : 'transparent',
              color: isActive ? '#3b82f6' : 'var(--text2)',
              fontWeight: isActive ? 600 : 400,
              fontSize: 14,
              transition: 'all 0.15s',
            })}>
              {n.label}
            </NavLink>
          ))}
          <div style={{ flex: 1 }} />
          <SyncButton />
        </nav>

        {/* Notice banner */}
        <div style={{
          background: '#1a1a0a',
          borderBottom: '1px solid #3a3a0a',
          padding: '8px 24px',
          fontSize: 12,
          color: '#aaa820',
        }}>
          ⚠️ 13F 데이터는 분기 종료 후 최대 45일 시차 존재. 참고 자료로만 활용하세요.
          롱(매수) 포지션만 공시 | 공매도·현금·해외주식 미포함
        </div>

        <main style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 16px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/investor/:id" element={<Portfolio />} />
            <Route path="/consensus" element={<Consensus />} />
            <Route path="/new-buys" element={<NewBuys />} />
            <Route path="/screen" element={<Screen />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
