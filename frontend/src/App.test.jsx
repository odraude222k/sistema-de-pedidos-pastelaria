import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './AdminApp.jsx'

describe('Painel administrativo', () => {
  it('solicita a chave administrativa', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Painel administrativo' })).toBeInTheDocument()
    expect(screen.getByLabelText('Chave administrativa')).toBeInTheDocument()
  })
})
