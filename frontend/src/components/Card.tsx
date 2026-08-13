import { ReactNode, CSSProperties } from 'react'

interface CardProps {
  children: ReactNode
  style?: CSSProperties
  onClick?: () => void
}

export default function Card({ children, style, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: 20,
        cursor: onClick ? 'pointer' : undefined,
        transition: onClick ? 'border-color 0.15s, transform 0.1s' : undefined,
        ...style,
      }}
      onMouseEnter={onClick ? e => {
        (e.currentTarget as HTMLElement).style.borderColor = '#3b82f6'
      } : undefined}
      onMouseLeave={onClick ? e => {
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'
      } : undefined}
    >
      {children}
    </div>
  )
}
