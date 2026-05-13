import React, { useEffect, useRef, useState } from 'react'
import { NavLink, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, MapPin, Search, ShoppingCart } from 'lucide-react'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Catalog from './pages/Catalog'
import Product from './pages/Product'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import Orders from './pages/Orders'
import OrderDetail from './pages/OrderDetail'
import logoImg from './assets/Logo_ConnectHub_Branca.svg'
import { getCartTotals } from './cart'
import api from './api'
import { showToast } from './toast'
import { t, getLanguageFlag, getLanguageLabel } from './i18n'
import { useLanguage } from './LanguageContext'

const LOCATION_STORAGE_KEY = 'ihealthbrasil-location'

function formatLocationLabel(value) {
  if (!value) return 'Definir localização'
  if (typeof value === 'string') return value.split(',')[0]?.trim() || value
  if (value.city) return value.city
  if (value.displayName) return value.displayName.split(',')[0]?.trim() || value.displayName
  if (value.label) return value.label.split(',')[0]?.trim() || value.label
  return 'Definir localização'
}

async function reverseGeocode(latitude, longitude) {
  const response = await fetch(
    `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`,
    {
      headers: {
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
      }
    }
  )

  if (!response.ok) {
    throw new Error('Não foi possível identificar sua localização atual.')
  }

  const data = await response.json()
  const address = data?.address || {}
  const city = address.city || address.town || address.village || address.municipality || address.county || ''
  const state = address.state || ''

  return {
    latitude,
    longitude,
    city,
    state,
    displayName: data?.display_name || [city, state].filter(Boolean).join(', ') || 'Sua localização atual'
  }
}

async function geocodeLocation(query) {
  const cleanQuery = query.trim().replace(/\D/g, '')
  const isCEP = cleanQuery.length === 8

  if (isCEP) {
    try {
      const cepResponse = await fetch(`https://viacep.com.br/ws/${cleanQuery}/json/`)
      if (cepResponse.ok) {
        const cepData = await cepResponse.json()
        if (!cepData.erro) {
          const city = cepData.localidade || ''
          const state = cepData.uf || ''
          return {
            latitude: 0,
            longitude: 0,
            city,
            state,
            displayName: `${city}, ${state}`,
            query,
            fromCEP: true
          }
        }
      }
    } catch {
      // Se falhar, tenta com Nominatim
    }
  }

  const response = await fetch(
    `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=br&q=${encodeURIComponent(query)}`,
    {
      headers: {
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
      }
    }
  )

  if (!response.ok) {
    throw new Error('Digite uma cidade, bairro ou um CEP válido (8 dígitos).')
  }

  const data = await response.json()
  const match = data?.[0]

  if (!match) {
    throw new Error('Não encontramos esse local. Tente um CEP ou informar cidade/bairro.')
  }

  const parts = [match.address?.city || match.address?.town || match.address?.village || match.address?.municipality || '', match.address?.state || '']
    .filter(Boolean)

  return {
    latitude: Number(match.lat),
    longitude: Number(match.lon),
    city: parts[0] || query,
    state: parts[1] || '',
    displayName: match.display_name || parts.join(', ') || query,
    query
  }
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const langRef = useRef(null)
  const { language, changeLanguage } = useLanguage()
  const [searchTerm, setSearchTerm] = useState('')
  const [isLangOpen, setIsLangOpen] = useState(false)
  const [isVisible, setIsVisible] = useState(true)
  const [lastScrollY, setLastScrollY] = useState(0)
  const [cartItems, setCartItems] = useState(0)
  const [currentUser, setCurrentUser] = useState(null)
  const [toasts, setToasts] = useState([])
  const [isLocationOpen, setIsLocationOpen] = useState(false)
  const [locationValue, setLocationValue] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(LOCATION_STORAGE_KEY) || 'null')
    } catch {
      return null
    }
  })
  const [locationInput, setLocationInput] = useState('')
  const [locationLoading, setLocationLoading] = useState(false)
  const [locationError, setLocationError] = useState(null)

  useEffect(() => {
    function onToast(event){
      const toast = event?.detail
      if (!toast?.id || !toast?.message) return
      setToasts((current) => [...current, toast])

      window.setTimeout(() => {
        setToasts((current) => current.filter((item) => item.id !== toast.id))
      }, 3200)
    }

    window.addEventListener('ihealthbrasil:toast', onToast)
    return () => window.removeEventListener('ihealthbrasil:toast', onToast)
  }, [])

  useEffect(() => {
    let alive = true

    async function refreshAuth(){
      try {
        if (!api.hasSession()) {
          if (alive) setCurrentUser(null)
          return
        }
        const me = await api.me()
        if (alive) setCurrentUser(me)
      } catch {
        if (alive) setCurrentUser(null)
      }
    }

    function onAuthUpdated(){
      refreshAuth()
    }

    refreshAuth()
    window.addEventListener('ihealthbrasil:auth-updated', onAuthUpdated)

    return () => {
      alive = false
      window.removeEventListener('ihealthbrasil:auth-updated', onAuthUpdated)
    }
  }, [])

  useEffect(() => {
    const query = new URLSearchParams(location.search)
    setSearchTerm(query.get('search') || '')
  }, [location.search])

  useEffect(() => {
    async function refreshFromRoute() {
      try {
        const totals = await getCartTotals()
        setCartItems(totals.totalItems || 0)
      } catch {
        setCartItems(0)
      }
    }

    refreshFromRoute()

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  useEffect(() => {
    function handleClickOutside(event) {
      if (langRef.current && !langRef.current.contains(event.target)) {
        setIsLangOpen(false)
      }
    }

    async function refreshCart() {
      try {
        const totals = await getCartTotals()
        setCartItems(totals.totalItems || 0)
      } catch {
        setCartItems(0)
      }
    }

    function handleScroll() {
      if (window.scrollY > lastScrollY && window.scrollY > 100) {
        setIsVisible(false)
      } else {
        setIsVisible(true)
      }
      setLastScrollY(window.scrollY)
    }

    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('scroll', handleScroll)
    window.addEventListener('ihealthbrasil:cart-updated', refreshCart)
    refreshCart()

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('ihealthbrasil:cart-updated', refreshCart)
    }
  }, [lastScrollY])

  useEffect(() => {
    if (!locationValue) {
      setLocationInput('')
    }
  }, [locationValue])

  useEffect(() => {
    let alive = true

    async function detectCurrentLocation() {
      if (locationValue || !navigator.geolocation) return

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          if (!alive) return
          setLocationLoading(true)
          setLocationError(null)
          try {
            const resolved = await reverseGeocode(position.coords.latitude, position.coords.longitude)
            if (!alive) return
            setLocationValue(resolved)
            localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(resolved))
          } catch (error) {
            if (!alive) return
            setLocationError(error.message || 'Não foi possível identificar sua localização atual.')
          } finally {
            if (alive) setLocationLoading(false)
          }
        },
        (error) => {
          if (!alive) return
          if (error?.code === 1) {
            setLocationError('Permita o acesso à localização para detectar seu endereço atual.')
          } else {
            setLocationError('Não foi possível identificar sua localização atual.')
          }
        },
        { enableHighAccuracy: false, timeout: 12000, maximumAge: 600000 }
      )
    }

    detectCurrentLocation()

    return () => {
      alive = false
    }
  }, [locationValue])

  async function handleLocationSave(event) {
    event.preventDefault()

    if (!locationInput.trim()) {
      setLocationError('Digite uma cidade, bairro ou endereço.')
      return
    }

    setLocationLoading(true)
    setLocationError(null)

    try {
      const resolved = await geocodeLocation(locationInput.trim())
      setLocationValue(resolved)
      localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(resolved))
      setIsLocationOpen(false)
      showToast('Localização atualizada.', 'success')
    } catch (error) {
      setLocationError(error.message || 'Não foi possível salvar a localização.')
      showToast(error.message || 'Não foi possível salvar a localização.', 'error')
    } finally {
      setLocationLoading(false)
    }
  }

  function handleUseCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationError('Seu navegador não suporta geolocalização.')
      return
    }

    setLocationLoading(true)
    setLocationError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const resolved = await reverseGeocode(position.coords.latitude, position.coords.longitude)
          setLocationValue(resolved)
          localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(resolved))
          setLocationInput(resolved.displayName || '')
          setIsLocationOpen(false)
          showToast('Localização atual detectada.', 'success')
        } catch (error) {
          setLocationError(error.message || 'Não foi possível identificar sua localização atual.')
          showToast(error.message || 'Não foi possível identificar sua localização atual.', 'error')
        } finally {
          setLocationLoading(false)
        }
      },
      (error) => {
        setLocationLoading(false)
        if (error?.code === 1) {
          setLocationError('Permita o acesso à localização para detectar seu endereço atual.')
          showToast('Permita o acesso à localização para detectar seu endereço atual.', 'error')
        } else {
          setLocationError('Não foi possível identificar sua localização atual.')
          showToast('Não foi possível identificar sua localização atual.', 'error')
        }
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 600000 }
    )
  }

  function handleChangeLanguage(lang) {
    changeLanguage(lang)
    setIsLangOpen(false)
  }

  function handleSearch(event) {
    event.preventDefault()
    navigate(`/catalog?search=${encodeURIComponent(searchTerm)}`)
  }

  async function handleLogout(){
    try {
      await api.logout()
      showToast('Sessao encerrada com sucesso.', 'success')
    } finally {
      setCurrentUser(null)
      window.dispatchEvent(new Event('ihealthbrasil:auth-updated'))
      navigate('/login')
    }
  }

  return (
    <div className="shell">
      <header className="main-header">
        <Link className="logo-area" to="/" aria-label="Ir para a página inicial">
          <img src={logoImg} alt="iHealth Brasil" className="logo-img" />
          <div className="logo-text">
            <strong>ConnectHub</strong>
            <span>Onde tecnologia e natureza se encontram</span>
          </div>
        </Link>

        <form className="search-bar" onSubmit={handleSearch}>
          <Search className="search-icon" size={20} />
          <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder={t(language, 'header.searchPlaceholder')} />
        </form>

        <div className="user-menu">
          {currentUser ? (
            <>
              <span className="login-btn" style={{ cursor: 'default' }}>{currentUser.first_name || currentUser.username}</span>
              <Link className="secondary-btn" to="/orders">Pedidos</Link>
              <button className="ghost-btn" type="button" onClick={handleLogout}>{t(language, 'header.logout')}</button>
            </>
          ) : (
            <Link className="login-btn" to="/login">{t(language, 'header.login')}</Link>
          )}
          <Link className="cart-btn" to="/cart">
            <ShoppingCart size={20} />
{t(language, 'header.cart')}
            <span className="cart-count">{cartItems}</span>
          </Link>
        </div>
      </header>

      <div className={`subheader ${isVisible ? '' : 'hidden'}`}>
        <div className="subheader-left">
          <button className="open-filters-btn" type="button" onClick={() => navigate('/catalog')}>
            <span>☰</span> {t(language, 'header.filters')}
          </button>
          <div className="delivery-info location-selector-wrap">
            <span>{t(language, 'header.deliverTo')}</span>
            <button
              className="delivery-location-button"
              type="button"
              onClick={() => {
                setIsLocationOpen((current) => {
                  const nextOpen = !current
                  if (nextOpen) setLocationInput(locationValue?.displayName || '')
                  return nextOpen
                })
              }}
              aria-expanded={isLocationOpen}
              aria-label="Definir localização de entrega"
            >
              <strong>{locationLoading ? 'Detectando...' : formatLocationLabel(locationValue)}</strong>
              <MapPin size={18} />
              <ChevronDown size={18} className={isLocationOpen ? 'rotate' : ''} />
            </button>
            {isLocationOpen ? (
              <div className="location-popover" role="dialog" aria-label="Definir localização">
                <form onSubmit={handleLocationSave} className="location-form">
                  <label className="location-label" htmlFor="location-input">Cidade, bairro ou endereço</label>
                  <input
                    id="location-input"
                    value={locationInput}
                    onChange={(event) => setLocationInput(event.target.value)}
                    placeholder={locationValue?.displayName || 'Ex: São Paulo, SP'}
                  />
                  {locationError ? <p className="location-error">{locationError}</p> : null}
                  <div className="button-row location-actions">
                    <button className="secondary-btn" type="button" onClick={handleUseCurrentLocation} disabled={locationLoading}>
                      Usar minha localização
                    </button>
                    <button className="primary-btn" type="submit" disabled={locationLoading}>
                      {locationLoading ? 'Salvando...' : 'Salvar'}
                    </button>
                  </div>
                </form>
              </div>
            ) : null}
          </div>
        </div>

        <nav className="category-menu">
          <NavLink to="/catalog?category_slug=analgesicos">{t(language, 'nav.medications')}</NavLink>
          <NavLink to="/catalog?category_slug=vitaminas">{t(language, 'nav.wellness')}</NavLink>
          <NavLink to="/catalog?category_slug=cuidados-pessoais">{t(language, 'nav.natural')}</NavLink>
          <NavLink to="/catalog?ordering=price">{t(language, 'nav.promotions')}</NavLink>
        </nav>

        <div className="subheader-right">
          <div className="language-selector" ref={langRef} onClick={() => setIsLangOpen(!isLangOpen)}>
            <div className="selected-lang">
              <span className="Flag">{getLanguageFlag(language)}</span>
              <span>{getLanguageLabel(language)}</span>
              <ChevronDown size={14} className={isLangOpen ? 'rotate' : ''} />
            </div>

            {isLangOpen && (
              <ul className="lang-dropdown">
                <li onClick={() => handleChangeLanguage('pt')}><span className="flag">🇧🇷</span> {t(language, 'languages.portuguese')}</li>
                <li onClick={() => handleChangeLanguage('en')}><span className="flag">🇺🇸</span> {t(language, 'languages.english')}</li>
                <li onClick={() => handleChangeLanguage('es')}><span className="flag">🇪🇸</span> {t(language, 'languages.spanish')}</li>
                <li onClick={() => handleChangeLanguage('fr')}><span className="flag">🇫🇷</span> {t(language, 'languages.french')}</li>
              </ul>
            )}
          </div>
        </div>
      </div>

      <main className="page-area">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/product/:id" element={<Product />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
        </Routes>
      </main>

      <div className="toast-stack" aria-live="polite" aria-atomic="true">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type || 'info'}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}
