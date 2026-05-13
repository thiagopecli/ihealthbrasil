import api from './api'

const KEY = 'ihealthbrasil-cart'

function emitCartUpdated(){
  window.dispatchEvent(new Event('ihealthbrasil:cart-updated'))
}

function getLocalCart(){
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

function writeLocalCart(items){
  localStorage.setItem(KEY, JSON.stringify(items))
  return items
}

function toUiItems(cartPayload){
  const items = Array.isArray(cartPayload?.items) ? cartPayload.items : []
  return items.map((item) => ({
    id: item?.product?.id ?? item?.product?.slug ?? item?.product?.pk ?? item?.product?.product_id,
    backendItemId: item?.id,
    name: item?.product?.name || item?.product?.title,
    title: item?.product?.title || item?.product?.name,
    price: Number(item?.unit_price ?? item?.product?.price ?? 0),
    quantity: Number(item?.quantity || 0),
  }))
}

function addToLocalCart(product, quantity = 1){
  const cart = getLocalCart()
  const productId = product?.id ?? product?.slug ?? product?.pk ?? product?.product_id
  const index = cart.findIndex((item) => item.id === productId)
  if (index >= 0) {
    cart[index].quantity += quantity
    return writeLocalCart(cart)
  }
  return writeLocalCart([...cart, { id: productId, name: product.name || product.title, price: product.price, ...product, quantity }])
}

async function findServerItemByProductId(productId){
  const cartPayload = await api.fetchMyCart()
  const items = Array.isArray(cartPayload?.items) ? cartPayload.items : []
  return items.find((item) => {
    const pid = item?.product?.id ?? item?.product?.slug ?? item?.product?.pk ?? item?.product?.product_id
    return pid === productId
  })
}

export async function getCart(){
  try {
    const cartPayload = await api.fetchMyCart()
    const items = toUiItems(cartPayload)
    const local = getLocalCart()
    // Se o servidor retorna vazio mas localStorage tem itens, manter os locais
    if (Array.isArray(items) && items.length === 0 && Array.isArray(local) && local.length > 0) {
      return local
    }
    // Se servidor tem itens, sincronizar localStorage com servidor
    if (Array.isArray(items) && items.length > 0) {
      writeLocalCart(items)
      return items
    }
    // Se ambos vazios, retornar localStorage (pode estar vazio mesmo)
    return local
  } catch {
    return getLocalCart()
  }
}

export async function addToCart(product, quantity = 1){
  try {
    // Tenta adicionar ao servidor e mescla com localStorage
    const cartPayload = await api.addCartItem({ product_id: product.id, quantity })
    const serverItems = toUiItems(cartPayload)
    // Mescla com itens locais existentes para não perder dados
    const localItems = getLocalCart()
    const productId = product?.id ?? product?.slug ?? product?.pk ?? product?.product_id
    // Remove item duplicado se já existe
    const mergedLocal = localItems.filter(item => String(item.id) !== String(productId))
    // Adiciona o novo item do servidor ou local
    const newItem = serverItems[0] || { id: productId, name: product.name || product.title, price: product.price, quantity }
    const items = [...mergedLocal, newItem]
    writeLocalCart(items)
    emitCartUpdated()
    return items
  } catch {
    const items = addToLocalCart(product, quantity)
    emitCartUpdated()
    return items
  }
}

export async function updateCartQuantity(productId, quantity){
  if (!Number.isFinite(quantity) || quantity < 1) return removeFromCart(productId)

  try {
    const serverItem = await findServerItemByProductId(productId)
    if (!serverItem?.id) throw new Error('Item não encontrado no carrinho do servidor.')
    const cartPayload = await api.updateCartItem(serverItem.id, quantity)
    const items = toUiItems(cartPayload)
    writeLocalCart(items)
    emitCartUpdated()
    return items
  } catch {
    const cart = getLocalCart().filter((item) => item.id !== productId || quantity > 0)
    const index = cart.findIndex((item) => item.id === productId)
    if (index >= 0) cart[index].quantity = quantity
    const items = writeLocalCart(cart.filter((item) => item.quantity > 0))
    emitCartUpdated()
    return items
  }
}

export async function removeFromCart(productId){
  try {
    const serverItem = await findServerItemByProductId(productId)
    if (!serverItem?.id) throw new Error('Item não encontrado no carrinho do servidor.')
    const cartPayload = await api.removeCartItem(serverItem.id)
    const items = toUiItems(cartPayload)
    writeLocalCart(items)
    emitCartUpdated()
    return items
  } catch {
    const items = writeLocalCart(getLocalCart().filter((item) => item.id !== productId))
    emitCartUpdated()
    return items
  }
}

export async function clearCart(){
  try {
    await api.clearServerCart()
  } catch {
    // fallback local
  }
  localStorage.removeItem(KEY)
  emitCartUpdated()
}

export async function getCartTotals(){
  const items = await getCart()
  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0)
  const totalPrice = items.reduce((sum, item) => sum + (Number(item.price) || 0) * item.quantity, 0)
  return { totalItems, totalPrice }
}