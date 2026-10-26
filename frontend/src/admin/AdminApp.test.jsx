import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './AdminApp.jsx'

describe('Painel administrativo', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.restoreAllMocks()
  })

  it('solicita a chave administrativa', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'Painel administrativo' })).toBeInTheDocument()
    expect(screen.getByLabelText('Usuário')).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
  })

  it('autentica com o usuário cadastrado no backend', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation((url) => Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(url.endsWith('/login') ? { access_token: 'token-seguro', token_type: 'bearer' } : []),
    }))
    render(<App />)
    fireEvent.change(screen.getByLabelText('Usuário'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'senha-segura' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar no painel' }))

    await waitFor(() => expect(screen.getByRole('heading', { name: 'Produtos' })).toBeInTheDocument())
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/admin\/login$/)
    expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe('Bearer token-seguro')
  })
})
