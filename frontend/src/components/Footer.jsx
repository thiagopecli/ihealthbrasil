import React from 'react'
import { Mail, Phone, MapPin } from 'lucide-react'

function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-column">
          <strong>CNPJ:</strong>
          <span>51.644.126/0001-30</span>
        </div>

        <div className="footer-column">
          <strong>Razão social</strong>
          <span>I HEALTH TECNOLOGIA E SAUDE LTDA</span>
        </div>

        <div className="footer-column">
          <strong>Endereço</strong>
          <span>RUA FLAVIO ANTONIO CORREIA CARACAS, 440, ANEXO I</span>
          <span>FREI HIGINO — PARNAÍBA - PI — 64207-035</span>
        </div>

        <div className="footer-column">
          <strong>Contato</strong>
          <a href="mailto:ana.fisiophb@gmail.com" className="footer-contact">
            <Mail className="footer-icon" size={16} />
            <span>ana.fisiophb@gmail.com</span>
          </a>
          <a href="tel:+558698306618" className="footer-contact">
            <Phone className="footer-icon" size={16} />
            <span>(86) 9830-6618</span>
          </a>
        </div>
      </div>
    </footer>
  )
}

export default Footer
