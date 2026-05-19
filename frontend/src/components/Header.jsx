import logoImg from '../assets/Logo_preto_branco.png.png'
import { Search, ShoppingCart } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLanguage } from '../LanguageContext'

function Header() {
  const { t } = useLanguage()

  return (
    <header className='main-header'>
      <a className='logo-area logo-link' href='/' aria-label='Ir para a tela inicial'>
        <img src={logoImg} alt='iHealth Brasil' className='logo-img' />
      </a>

      <div className='search-bar'>
        <Search className='search-icon' size={20} />
        <input type='text' placeholder={t('search')} />
      </div>

      <div className='user-menu'>
        <Link to="/login" className='login-btn' style={{ textDecoration: 'none' }}>
          {t('login')}
        </Link>
        <button className='cart-btn'>
          <ShoppingCart size={20} />
          {t('cart')}
        </button>
      </div>
    </header>
  )
}

export default Header