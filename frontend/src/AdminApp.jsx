import { useCallback, useEffect, useState } from 'react'
import './AdminApp.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const emptyProduct = { name: '', description: '', price: '', category_id: '' }

export default function AdminApp() {
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem('adminKey') || '')
  const [draftKey, setDraftKey] = useState('')
  const [activeTab, setActiveTab] = useState('products')
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [productForm, setProductForm] = useState(emptyProduct)
  const [editingId, setEditingId] = useState(null)
  const [categoryName, setCategoryName] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const request = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API_URL}/admin${path}`, { ...options, headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey, ...options.headers } })
    if (response.status === 401) {
      sessionStorage.removeItem('adminKey')
      setAdminKey('')
      throw new Error('Chave administrativa inválida.')
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || 'Não foi possível concluir a operação.')
    }
    return response.status === 204 ? null : response.json()
  }, [adminKey])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [categoryData, productData, orderData] = await Promise.all([request('/categories'), request('/products'), request('/orders')])
      setCategories(categoryData); setProducts(productData); setOrders(orderData)
    } catch (error) { setMessage(error.message) } finally { setLoading(false) }
  }, [request])

  useEffect(() => {
    // A carga é o efeito de sincronização do painel com a API após o acesso.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (adminKey) loadData()
  }, [adminKey, loadData])

  function login(event) {
    event.preventDefault()
    const key = draftKey.trim()
    if (key) { sessionStorage.setItem('adminKey', key); setAdminKey(key) }
  }

  async function saveProduct(event) {
    event.preventDefault()
    try {
      const payload = { ...productForm, price: Number(productForm.price), category_id: Number(productForm.category_id) }
      await request(editingId ? `/products/${editingId}` : '/products', { method: editingId ? 'PUT' : 'POST', body: JSON.stringify(payload) })
      setProductForm(emptyProduct); setEditingId(null); await loadData()
    } catch (error) { setMessage(error.message) }
  }

  function editProduct(product) {
    setProductForm({ name: product.name, description: product.description, price: product.price, category_id: product.category_id })
    setEditingId(product.id); window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function remove(path, confirmation) {
    if (!window.confirm(confirmation)) return
    try { await request(path, { method: 'DELETE' }); await loadData() } catch (error) { setMessage(error.message) }
  }

  async function createCategory(event) {
    event.preventDefault()
    try { await request('/categories', { method: 'POST', body: JSON.stringify({ name: categoryName }) }); setCategoryName(''); await loadData() } catch (error) { setMessage(error.message) }
  }

  async function changeOrderStatus(id, status) {
    try { await request(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }); await loadData() } catch (error) { setMessage(error.message) }
  }

  if (!adminKey) return <main className="login-shell"><form className="login-card" onSubmit={login}><span className="brand-mark">P</span><p className="eyebrow">Pastelaria</p><h1>Painel administrativo</h1><p className="muted">Informe sua chave de acesso para gerenciar o cardápio e os pedidos.</p><label>Chave administrativa<input type="password" value={draftKey} onChange={(event) => setDraftKey(event.target.value)} autoFocus /></label><button className="primary" type="submit">Entrar no painel</button></form></main>

  const pending = orders.filter((order) => order.status === 'pendente').length
  return <div className="admin-shell">
    <aside><div className="brand"><span className="brand-mark">P</span><div><strong>Pastelaria</strong><small>Administração</small></div></div><nav aria-label="Navegação principal"><button className={activeTab === 'products' ? 'active' : ''} onClick={() => setActiveTab('products')}>▦ Produtos</button><button className={activeTab === 'categories' ? 'active' : ''} onClick={() => setActiveTab('categories')}>◇ Categorias</button><button className={activeTab === 'orders' ? 'active' : ''} onClick={() => setActiveTab('orders')}>◷ Pedidos {pending > 0 && <span>{pending}</span>}</button></nav><button className="logout" onClick={() => { sessionStorage.removeItem('adminKey'); setAdminKey('') }}>Sair</button></aside>
    <main><header><div><p className="eyebrow">Visão geral</p><h1>{activeTab === 'products' ? 'Produtos' : activeTab === 'categories' ? 'Categorias' : 'Pedidos'}</h1></div><button className="refresh" onClick={loadData}>↻ Atualizar</button></header>{message && <div className="notice" role="status">{message}</div>}{loading && <p className="muted">Carregando dados...</p>}
      {activeTab === 'products' && <><section className="card"><div className="section-title"><div><h2>{editingId ? 'Editar produto' : 'Novo produto'}</h2><p>Preencha as informações exibidas no cardápio.</p></div></div><form className="product-form" onSubmit={saveProduct}><label>Nome<input required minLength="2" value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} /></label><label>Categoria<select required value={productForm.category_id} onChange={(e) => setProductForm({ ...productForm, category_id: e.target.value })}><option value="">Selecione</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label>Preço<input required min="0.01" step="0.01" type="number" value={productForm.price} onChange={(e) => setProductForm({ ...productForm, price: e.target.value })} /></label><label className="wide">Descrição<textarea rows="3" value={productForm.description} onChange={(e) => setProductForm({ ...productForm, description: e.target.value })} /></label><div className="form-actions">{editingId && <button type="button" className="ghost" onClick={() => { setEditingId(null); setProductForm(emptyProduct) }}>Cancelar</button>}<button className="primary" disabled={!categories.length}>{editingId ? 'Salvar alterações' : 'Adicionar produto'}</button></div></form></section><section className="card"><div className="section-title"><div><h2>Cardápio</h2><p>{products.length} produto(s) cadastrado(s)</p></div></div><div className="table-wrap"><table><thead><tr><th>Produto</th><th>Categoria</th><th>Preço</th><th>Ações</th></tr></thead><tbody>{products.map((product) => <tr key={product.id}><td><strong>{product.name}</strong><small>{product.description || 'Sem descrição'}</small></td><td><span className="tag">{product.category.name}</span></td><td>{money.format(product.price)}</td><td><button className="link" onClick={() => editProduct(product)}>Editar</button><button className="link danger" onClick={() => remove(`/products/${product.id}`, 'Excluir este produto?')}>Excluir</button></td></tr>)}</tbody></table>{!products.length && <Empty text="Nenhum produto cadastrado." />}</div></section></>}
      {activeTab === 'categories' && <section className="card"><div className="section-title"><div><h2>Categorias do cardápio</h2><p>Organize os produtos para facilitar a escolha do cliente.</p></div></div><form className="inline-form" onSubmit={createCategory}><label>Nova categoria<input required minLength="2" placeholder="Ex.: Pastéis doces" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} /></label><button className="primary">Criar categoria</button></form><div className="category-grid">{categories.map((category) => <article key={category.id}><div><strong>{category.name}</strong><small>{products.filter((product) => product.category_id === category.id).length} produto(s)</small></div><button className="icon-danger" aria-label={`Excluir ${category.name}`} onClick={() => remove(`/categories/${category.id}`, 'Excluir esta categoria?')}>×</button></article>)}</div>{!categories.length && <Empty text="Nenhuma categoria cadastrada." />}</section>}
      {activeTab === 'orders' && <section className="orders-grid">{orders.map((order) => <article className="card order-card" key={order.id}><div className="order-head"><div><span className="order-number">Pedido #{order.id}</span><small>{new Date(order.created_at).toLocaleString('pt-BR')}</small></div><span className={`status ${order.status}`}>{order.status}</span></div><div className="customer"><strong>{order.customer_name}</strong><span>{order.customer_phone}</span></div><div className="order-total"><span>Total</span><strong>{money.format(order.total)}</strong></div>{order.status === 'pendente' && <div className="order-actions"><button className="reject" onClick={() => changeOrderStatus(order.id, 'recusado')}>Recusar</button><button className="accept" onClick={() => changeOrderStatus(order.id, 'aceito')}>Aceitar pedido</button></div>}{order.status === 'aceito' && <button className="primary full" onClick={() => changeOrderStatus(order.id, 'finalizado')}>Marcar como finalizado</button>}</article>)}{!orders.length && <div className="card"><Empty text="Nenhum pedido recebido." /></div>}</section>}
    </main>
  </div>
}

function Empty({ text }) { return <div className="empty"><span>◎</span><p>{text}</p></div> }
