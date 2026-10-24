import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App.jsx'

describe('App', () => {
  it('atualiza o contador quando o botão é clicado', () => {
    render(<App />)

    const counter = screen.getByRole('button', { name: 'Count is 0' })
    fireEvent.click(counter)

    expect(screen.getByRole('button', { name: 'Count is 1' })).toBeInTheDocument()
  })
})
