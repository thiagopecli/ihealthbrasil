import React, { useState } from 'react';
import { User } from 'lucide-react';
import { Link } from 'react-router-dom';

const DetailField = ({ label, type = "text", value, placeholder }) => (
  <div className="detail-group">
    <label>{label}</label>
    <input type={type} className="profile-input" defaultValue={value} placeholder={placeholder} />
  </div>
);

function ProfilePage() {
  const [activeTab, setActiveTab] = useState('dados');

  const tabs = [
    { id: 'dados', label: 'Dados Pessoais' },
    { id: 'seguranca', label: 'Segurança' },
    { id: 'config', label: 'Configurações' }
  ];

  return (
    <div className="profile-page-container">
      <aside className="profile-sidebar">
        <div className="profile-header-sidebar">
          <div className="profile-avatar">
            <User size={40} color="#0090C1" />
          </div>
          <div className="profile-info">
            <h1>Emanuel</h1>
            <span>Membro desde 2026</span>
          </div>
        </div>

        <nav className="profile-tabs-nav">
          {tabs.map(tab => (
            <button 
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="profile-card">
        {activeTab === 'dados' && (
          <div className="tab-section">
            <h2>Meus Dados</h2>
            <div className="profile-details">
              <DetailField label="E-mail" value="emanuel@gmail.com" />
              <DetailField label="Telefone" value="(10) 12345-6789" />
              <DetailField label="Endereço Principal" value="Rua Exemplo, 123 - Campina Grande, PB" />
            </div>
          </div>
        )}

        {activeTab === 'seguranca' && (
          <div className="tab-section">
            <h2>Segurança</h2>
            <div className="profile-details">
              <DetailField label="Senha Atual" type="password" placeholder="********" />
              <DetailField label="Nova Senha" type="password" />
            </div>
          </div>
        )}

        {activeTab === 'config' && (
          <div className="tab-section">
            <h2>Configurações</h2>
            <div className="profile-details">
              <div className="detail-group-row">
                <div>
                  <label>Notificações</label>
                  <p>Receber ofertas por e-mail</p>
                </div>
                <input type="checkbox" defaultChecked />
              </div>
            </div>
          </div>
        )}

        <div className="profile-actions">
          <button className="edit-profile-btn">Salvar Alterações</button>
          <Link to="/" className="back-home-link">← Voltar para a loja</Link>
        </div>
      </main>
    </div>
  );
}

export default ProfilePage;