import './App.css'
import logoImg from './assets/Logo_ConnectHub_Branca.svg'
import {useState, useEffect, useRef} from 'react';
import {Search, ShoppingCart, MapPin, ChevronDown,} from 'lucide-react'

function App() {
  const [isLangOpen, setIsLangOpen] = useState(false);
  const langRef = useRef(null);

  useEffect(() => {
    function handleClickFora(event) {
      if (langRef.current && !langRef.current.contains(event.target)) {
        setIsLangOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickFora);
    return () => {
      document.removeEventListener("mousedown", handleClickFora);
    };
  }, [langRef])
  
  return (
    <div className='app-container'>
      <header className='main-header'>
        <div className='logo-area'>
          <img src={logoImg} alt='iHealth Brasil' className='logo-img'/>
            <div className='logo-text'>
              <strong>ConnectHub</strong>
              <span>Onde tecnologia e natureza se encontram</span>
            </div>
        </div>
        <div className='search-bar'>
          <Search className='search-icon' size={20}/>
          <input type="text" placeholder='Pesquisar'/>
        </div>
        <div className='user-menu'>
          <button className='login-btn'>Entrar</button>
          <button className='cart-btn'>
            <ShoppingCart size={20}/>
            Seu carrinho
          </button>
        </div>
      </header>

      <div className='location-bar'>
        <div className='delivery-info'>
          <span>
            Entregar em:
          </span>
              <strong>
                São Paulo, SP
                <MapPin size={20}/>
                <ChevronDown size={20}/>
              </strong>
        </div>

        <nav className='category-menu'>
          <a href="#">Medicamentos</a>
          <a href="#">Bem-Estar</a>
          <a href="#">Naturais</a>
          <a href="#">Promoções</a>
        </nav>

    <div className='language-selector' ref={langRef} onClick={() => setIsLangOpen(!isLangOpen)}>
        <div className='selected-lang'>
          <span className='Flag'>🇧🇷</span>
          <span>PT</span>
          <ChevronDown size={14} className={isLangOpen ? 'rotate' : ''}/>
        </div>

      {isLangOpen && (
        <ul className='lang-dropdown'>
          <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇧🇷</span>Potuguês</li>
          <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇺🇸</span>Inglês</li>
          <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇪🇸</span>Espanhol</li>
          <li onClick={() => setIsLangOpen(false)}><span className='flag'>🇫🇷</span>Françês</li>
        </ul>
      )}
    </div>

      </div>
      <main className='content'>
        <div className='content-wrapper'>
          <section className='main-banner'>
            <h2>[imagem do banner aqui]</h2>
          </section>
          <section className='categories-preview'>
          </section>
        </div>
        
        <div className='content-wrapper'>
          <h3>O que você procura?</h3>
        </div>
      </main>
    </div>
  )
}

export default App