import { useState, useEffect, useRef } from 'react'
import logoImg from '../assets/Logo_preto_branco.png.png'
import { Search, ShoppingCart, ChevronDown } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useLanguage } from '../LanguageContext'

function isAuthenticated() {
  return !!localStorage.getItem('access_token')
}

function Header() {
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setOpen(false)
    navigate('/')
  }

  return (
    <header className='main-header'>
      <a className='logo-area logo-link' href='/' aria-label='Ir para a tela inicial'>
        <img src={logoImg} alt='iHealth Brasil' className='logo-img' />
      </a>

      <div className='search-bar'>
        <Search className='search-icon' size={20} />
        <input type='text' placeholder={t('search')} />
      </div>

      <div className='user-menu' ref={menuRef}>
        {isAuthenticated() ? (
          <>
            <div className='profile-dropdown'>
              <button className='profile-btn' onClick={(e) => { e.stopPropagation(); setOpen((s) => !s); }}>
                <span className='profile-name'>{JSON.parse(localStorage.getItem('user') || 'null')?.first_name || JSON.parse(localStorage.getItem('user') || 'null')?.username}</span>
                <ChevronDown size={16} />
              </button>
              {open && (
                <ul className='dropdown-menu'>
                  <li>
                    <Link to='/profile' onClick={() => setOpen(false)}>{t('my_account') || 'Minha conta'}</Link>
                  </li>
                  <li>
                    <Link to='/orders' onClick={() => setOpen(false)}>{t('my_orders') || 'Meus pedidos'}</Link>
                  </li>
                  <li>
                    <Link to='/favorites' onClick={() => setOpen(false)}>{t('favorites') || 'Favoritos'}</Link>
                  </li>
                  <li>
                    <button className='logout-btn' onClick={logout}>{t('logout') || 'Sair'}</button>
                  </li>
                </ul>
              )}
            </div>
            <button className='cart-btn'>
              <ShoppingCart size={20} />
              {t('cart')}
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className='login-btn' style={{ textDecoration: 'none' }}>
              {t('login')}
            </Link>
            <button className='cart-btn'>
              <ShoppingCart size={20} />
              {t('cart')}
            </button>
          </>
        )}
      </div>
    </header>
  )
}

export default Header