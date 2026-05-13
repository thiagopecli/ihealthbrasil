import { categories, products, findProduct, filterProducts } from './mockData'

const BASE = import.meta.env.VITE_API_BASE || ''

function getAccess(){
  return localStorage.getItem('access')
}

export function hasSession(){
  return Boolean(getAccess())
}

function toArray(payload){
  if (Array.isArray(payload)) return payload
  if (payload && Array.isArray(payload.results)) return payload.results
  return []
}

function parseParams(params = ''){
  return new URLSearchParams(params)
}

async function request(path, opts = {}){
  const headers = new Headers(opts.headers || {})
  const token = getAccess()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${BASE}${path}`, { ...opts, headers })
  if (!res.ok) {
    const text = await res.text().catch(() => null)
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json().catch(() => null)
}

function useMockFallback(error){
  const msg = String(error?.message || error)
  // Reconhece erros de rede, erros HTTP, ou sem BASE URL
  return !BASE || /Failed to fetch|NetworkError|ECONNREFUSED|HTTP 4\d\d|HTTP 5\d\d/i.test(msg)
}

export async function login(username, password){
  try {
    const data = await request('/api/auth/token/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (data && data.access) localStorage.setItem('access', data.access)
    if (data && data.refresh) localStorage.setItem('refresh', data.refresh)
    return data
  } catch (error) {
    if (!useMockFallback(error)) throw error
    const demo = { access: 'mock-access-token', refresh: 'mock-refresh-token' }
    localStorage.setItem('access', demo.access)
    localStorage.setItem('refresh', demo.refresh)
    return demo
  }
}

export async function register(username, email, password, firstName, lastName, profile = 'PATIENT', phoneNumber = ''){
  try {
    const data = await request('/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        profile,
        phone_number: phoneNumber
      })
    })
    return data
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return {
      username,
      email,
      first_name: firstName,
      last_name: lastName,
      profile,
      phone_number: phoneNumber
    }
  }
}

export async function me(){
  try {
    return await request('/api/auth/me/')
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return {
      username: 'demo_user',
      first_name: 'Demo',
      last_name: 'User',
      profile: 'PATIENT',
      email: 'demo@example.com'
    }
  }
}

export async function logout(){
  const refresh = localStorage.getItem('refresh')
  try {
    await request('/api/auth/logout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    })
  } catch (error) {
    if (!useMockFallback(error)) throw error
  }
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}

export async function fetchCategories(){
  try {
    const data = await request('/api/categories/')
    return toArray(data)
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return categories
  }
}

export async function fetchProducts(params = ''){
  try {
    const q = params ? `?${params}` : ''
    const data = await request(`/api/products/${q}`)
    return toArray(data)
  } catch (error) {
    if (!useMockFallback(error)) throw error
    const search = parseParams(params)
    return filterProducts({
      search: search.get('search') || '',
      categorySlug: search.get('category_slug') || '',
      ordering: search.get('ordering') || '',
      requiresPrescription: search.get('requires_prescription') || ''
    })
  }
}

export async function fetchProduct(idOrSlug){
  try {
    const data = await request(`/api/products/${idOrSlug}/`)
    if (!data) {
      return findProduct(idOrSlug)
    }
    return data
  } catch (error) {
    const message = String(error?.message || '')
    const notFound = /not found|not existe|não encontrado|404/i.test(message)
    if (!useMockFallback(error) && !notFound) throw error
    return findProduct(idOrSlug)
  }
}

export async function fetchMyCart(){
  try {
    return await request('/api/carts/me/')
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return { items: [] }
  }
}

export async function addCartItem({ product_id, quantity = 1, product_variation_id = null }){
  try {
    return await request('/api/carts/items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id, quantity, product_variation_id })
    })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    const product = findProduct(product_id)
    return {
      items: [{
        id: Math.random(),
        product: product || { id: product_id },
        quantity,
        unit_price: product?.price || 0
      }]
    }
  }
}

export async function updateCartItem(itemId, quantity){
  try {
    return await request(`/api/carts/items/${itemId}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity })
    })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return { items: [] }
  }
}

export async function removeCartItem(itemId){
  try {
    return await request(`/api/carts/items/${itemId}/`, { method: 'DELETE' })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return { items: [] }
  }
}

export async function clearServerCart(){
  try {
    return await request('/api/carts/clear/', { method: 'DELETE' })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return { items: [] }
  }
}

export async function checkoutCart(payload = {}){
  try {
    return await request('/api/carts/checkout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return {
      id: Math.random(),
      ...payload,
      status: 'pending',
      created_at: new Date().toISOString()
    }
  }
}

export async function createPaymentIntent(orderId, payload = { currency: 'brl' }){
  try {
    return await request(`/api/orders/${orderId}/payment-intent/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return {
      id: Math.random(),
      order_id: orderId,
      ...payload,
      status: 'pending'
    }
  }
}

export async function shippingQuote(cep, service_codes = []){
  try {
    const data = await request('/api/carts/shipping-quote/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cep, service_codes })
    })
    return data
  } catch (error) {
    if (!useMockFallback(error)) throw error
    // Fallback: empty services so frontend may fall back to local simulation
    return { services: [] }
  }
}

export async function fetchOrders(){
  try {
    const data = await request('/api/orders/')
    return toArray(data)
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return []
  }
}

export async function fetchOrder(orderId){
  try {
    return await request(`/api/orders/${orderId}/`)
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return {
      id: orderId,
      status: 'pending',
      items: [],
      total: 0
    }
  }
}

export async function syncLocalCartAndCheckout(localItems = [], payload = {}){
  try {
    await clearServerCart()
    for (const item of localItems) {
      await addCartItem({ product_id: item.id, quantity: item.quantity || 1 })
    }
    return await checkoutCart(payload)
  } catch (error) {
    if (!useMockFallback(error)) throw error
    return { mock: true, items: localItems, total: localItems.reduce((sum, item) => sum + (Number(item.price) || 0) * (item.quantity || 1), 0) }
  }
}

export default {
  login,
  register,
  me,
  logout,
  fetchCategories,
  fetchProducts,
  fetchProduct,
  fetchMyCart,
  addCartItem,
  updateCartItem,
  removeCartItem,
  clearServerCart,
  checkoutCart,
  createPaymentIntent,
  shippingQuote,
  fetchOrders,
  fetchOrder,
  hasSession,
  syncLocalCartAndCheckout,
}
