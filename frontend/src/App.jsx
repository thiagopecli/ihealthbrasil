import './App.css'
import { useEffect, useRef, useState } from 'react'
import { ChevronDown, MapPin } from 'lucide-react'
import { useLanguage } from './LanguageContext'
import Header from './components/Header'
import BannerCarousel from './components/BannerCarousel'
import ProductGrid from './components/ProductGrid'
import Footer from './components/Footer'
import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  const [isLangOpen, setIsLangOpen] = useState(false)
  const [isLocationOpen, setIsLocationOpen] = useState(false)
  const [cepValue, setCepValue] = useState('')
  const [cepStatus, setCepStatus] = useState('')
  const [cepResult, setCepResult] = useState('')
  const [isSearchingCep, setIsSearchingCep] = useState(false)
  const [isLocating, setIsLocating] = useState(false)
  const [locationMessage, setLocationMessage] = useState('')
  const [currentLocation, setCurrentLocation] = useState('São Paulo, SP')
  const langRef = useRef(null)
  const locationRef = useRef(null)

  const { lang, setLang, t } = useLanguage()

  useEffect(() => {
    function handleClickFora(event) {
      if (langRef.current && !langRef.current.contains(event.target)) {
        setIsLangOpen(false)
      }

      if (locationRef.current && !locationRef.current.contains(event.target)) {
        setIsLocationOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickFora)
    return () => {
      document.removeEventListener('mousedown', handleClickFora)
    }
  }, [])

  function formatCep(value) {
    const digits = value.replace(/\D/g, '').slice(0, 8)
    if (digits.length <= 5) {
      return digits
    }

    return `${digits.slice(0, 5)}-${digits.slice(5)}`
  }

  async function handleCepSearch(event) {
    event.preventDefault()

    const cep = cepValue.replace(/\D/g, '')
    if (cep.length !== 8) {
      setCepStatus(t('cep_invalid'))
      setCepResult('')
      return
    }

    setIsSearchingCep(true)
    setCepStatus('Buscando CEP...')
    setCepResult('')

    try {
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
      const data = await response.json()

      if (!response.ok || data.erro) {
        throw new Error(t('cep_not_found_error'))
      }

      const locationText = [data.localidade, data.uf].filter(Boolean).join(', ')
      const streetText = [data.logradouro, data.bairro].filter(Boolean).join(' - ')

      setCurrentLocation(locationText || t('location_updated'))
      setCepResult([streetText, locationText].filter(Boolean).join(' • ') || t('cep_found_success'))
      setCepStatus('')
    } catch {
      setCepStatus(t('cep_not_found'))
      setCepResult('')
    } finally {
      setIsSearchingCep(false)
    }
  }

  async function handleUseCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationMessage(t('location_not_supported'))
      try {
        const fallbackResponse = await fetch('https://ipapi.co/json/')
        const fallbackData = await fallbackResponse.json()
        setCurrentLocation(
          [fallbackData.city, fallbackData.region_code || fallbackData.region].filter(Boolean).join(', ') ||
            t('location_approximate'),
        )
      } catch {
        setCurrentLocation(t('location_approximate'))
      }
      return
    }

    setIsLocating(true)
    setLocationMessage('')

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`,
            {
              headers: {
                Accept: 'application/json',
              },
            },
          )

          if (!response.ok) {
            throw new Error('Não foi possível identificar o endereço.')
          }

          const data = await response.json()
          const addressParts = [data.address?.city || data.address?.town || data.address?.village, data.address?.state]
            .filter(Boolean)
            .join(', ')

          setCurrentLocation(addressParts || data.display_name || t('location_updated'))
          setLocationMessage(t('location_updated'))
        } catch (error) {
          setCurrentLocation(`${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`)
          setLocationMessage(t('location_detected_no_address'))
        } finally {
          setIsLocating(false)
        }
      },
      () => {
        setLocationMessage(t('location_access_denied'))
        fetch('https://ipapi.co/json/')
          .then((response) => response.json())
          .then((fallbackData) => {
            setCurrentLocation(
              [fallbackData.city, fallbackData.region_code || fallbackData.region].filter(Boolean).join(', ') ||
                t('location_approximate'),
            )
          })
          .catch(() => {
            setCurrentLocation(t('location_approximate'))
          })
        setIsLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  const banners = [
    { id: 1, title: t('banner_outono'), color: '#ffffff' },
    { id: 2, title: t('banner_novidades'), color: '#ffffff' },
    { id: 3, title: t('banner_entrega'), color: '#ffffff' },
  ]

  const displayBanners = [...banners, ...banners, ...banners]

  const produtosDestaque = [
    {
      id: 1,
      nome: 'Vitamina C',
      preco: '49,90',
      categoria: 'Suplementos',
      imagem: 'https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80',
    },
    {
      id: 2,
      nome: 'Ômega 3',
      preco: '79,90',
      categoria: 'Saúde',
      imagem: 'https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80',
    },
    {
      id: 3,
      nome: 'Whey Protein',
      preco: '129,90',
      categoria: 'Esporte',
      imagem: 'https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80',
    },
    {
      id: 4,
      nome: 'Magnésio Quelato',
      preco: '35,00',
      categoria: 'Minerais',
      imagem: 'https://img.freepik.com/fotos-gratis/embalagens-de-comprimidos-e-capsulas-de-medicamentos_1339-2255.jpg?semt=ais_hybrid&w=740&q=80',
    },
  ]

  const categorias = ['Todos', 'Cosméticos', 'Sublinguais', 'Veterinários', 'Bioativos Apícolas']

  const [categoriaAtiva, setCategoriaAtiva] = useState('Todos')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [isVisible, setIsVisible] = useState(true)
  const [lastScrollY, setLastScrollY] = useState(0)

  const produtosFiltrados =
    categoriaAtiva === 'Todos'
      ? produtosDestaque
      : produtosDestaque.filter((produto) => produto.categoria === categoriaAtiva)

  const categoryKeyMap = {
    Todos: 'todos',
    'Cosméticos': 'cosmeticos',
    Sublinguais: 'sublinguais',
    'Veterinários': 'veterinarios',
    'Bioativos Apícolas': 'bioativos_apicolas',
  }

  useEffect(() => {
    const controlSubheader = () => {
      if (window.scrollY > lastScrollY && window.scrollY > 100) {
        setIsVisible(false)
      } else {
        setIsVisible(true)
      }

      setLastScrollY(window.scrollY)
    }

    window.addEventListener('scroll', controlSubheader)
    return () => window.removeEventListener('scroll', controlSubheader)
  }, [lastScrollY])

  const homeContent = (
    <>
      <Header />

      <div className={`subheader ${isVisible ? '' : 'hidden'}`}>
        <div className='subheader-left'>
          <button className='open-filters-btn' onClick={() => setIsFilterOpen(true)}>
            <span>☰</span> {t('filtros')}
          </button>

          {isFilterOpen && <div className='filter-overlay' onClick={() => setIsFilterOpen(false)} />}

          <aside className={`filter-sidebar ${isFilterOpen ? 'open' : ''}`}>
            <div className='sidebar-header'>
              <h3>{t('filtros')}</h3>
              <button className='close-btn' onClick={() => setIsFilterOpen(false)}>
                ✕
              </button>
            </div>

            <div className='filter-groups'>
              <h4>{t('categorias')}</h4>
              {categorias.map((cat) => (
                <button
                  key={cat}
                  className={`filter-link ${categoriaAtiva === cat ? 'active' : ''}`}
                  onClick={() => {
                    setCategoriaAtiva(cat)
                    setIsFilterOpen(false)
                  }}
                >
                  {t(categoryKeyMap[cat])}
                </button>
              ))}
            </div>
          </aside>

          <div className='delivery-wrapper' ref={locationRef}>
            <button
              type='button'
              className='delivery-info delivery-link delivery-trigger'
              onClick={() => setIsLocationOpen(!isLocationOpen)}
              aria-label='Abrir seletor de localização'
            >
              <span>{t('deliver')}</span>
              <strong>
                {currentLocation}
                <MapPin size={20} />
                <ChevronDown size={20} className={isLocationOpen ? 'rotate' : ''} />
              </strong>
            </button>

            {isLocationOpen && (
              <div className='delivery-popover' role='dialog' aria-label='Seleção de CEP'>
                <p className='delivery-popover-title'>{t('cepTitle')}</p>
                <p className='delivery-popover-text'>{t('cepText')}</p>

                <form className='delivery-popover-form' onSubmit={handleCepSearch}>
                  <input
                    type='text'
                    inputMode='numeric'
                    placeholder='00000-000'
                    value={cepValue}
                    onChange={(event) => setCepValue(formatCep(event.target.value))}
                  />
                  <button type='submit' className='delivery-popover-button' disabled={isSearchingCep}>
                    {isSearchingCep ? t('buscando') : t('buscar')}
                  </button>
                </form>

                {cepResult && <p className='delivery-popover-result'>{cepResult}</p>}
                {cepStatus && <p className='delivery-popover-status'>{cepStatus}</p>}

                <button
                  type='button'
                  className='delivery-popover-link'
                  onClick={handleUseCurrentLocation}
                  disabled={isLocating}
                >
                  {isLocating ? t('localizando') : t('usarLocal')}
                </button>

                {locationMessage && <p className='delivery-popover-status'>{locationMessage}</p>}
              </div>
            )}
          </div>
        </div>

        <nav className='category-menu'>
          <a href='#'>{t('nav_medicamentos')}</a>
          <a href='#'>{t('nav_bemestar')}</a>
          <a href='#'>{t('nav_naturais')}</a>
          <a href='#'>{t('nav_promocoes')}</a>
        </nav>

        <div className='subheader-right'>
          <div className='language-selector' ref={langRef} onClick={() => setIsLangOpen(!isLangOpen)}>
            <div className='selected-lang'>
              <span className='Flag'>{lang === 'pt' ? '🇧🇷' : lang === 'en' ? '🇺🇸' : lang === 'es' ? '🇪🇸' : '🇫🇷'}</span>
              <span>{lang.toUpperCase()}</span>
              <ChevronDown size={14} className={isLangOpen ? 'rotate' : ''} />
            </div>

            {isLangOpen && (
              <ul className='lang-dropdown'>
                <li
                  onClick={() => {
                    setLang('pt')
                    setIsLangOpen(false)
                  }}
                >
                  <span className='flag'>🇧🇷</span> Português
                </li>
                <li
                  onClick={() => {
                    setLang('en')
                    setIsLangOpen(false)
                  }}
                >
                  <span className='flag'>🇺🇸</span> English
                </li>
                <li
                  onClick={() => {
                    setLang('es')
                    setIsLangOpen(false)
                  }}
                >
                  <span className='flag'>🇪🇸</span> Español
                </li>
                <li
                  onClick={() => {
                    setLang('fr')
                    setIsLangOpen(false)
                  }}
                >
                  <span className='flag'>🇫🇷</span> Français
                </li>
              </ul>
            )}
          </div>
        </div>
      </div>

      <BannerCarousel banners={displayBanners} />
      <ProductGrid produtos={produtosFiltrados} />
      <Footer />
    </>
  )

  return (
    <div className='app-container'>
      <Routes>
        <Route path='/' element={homeContent} />
        <Route path='/login' element={<Login />} />
        <Route path='/register' element={<Register />} />
      </Routes>
    </div>
  )
}

export default App
