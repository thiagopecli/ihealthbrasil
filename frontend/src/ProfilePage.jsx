import React, { useState } from 'react';
import { User, Bell, Trash2, Shield, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

function ProfilePage() {
  const [activeTab, setActiveTab] = useState('dados');
  const [showPassword, setShowPassword] = useState(false);

  const [configs, setConfigs] = useState ({
    notificacoesEmail: true,
    notificacoesSms: false,
    perfilPiblico: true
  })

  const [userData, setUserData] = useState(() => {
    const salvos = localStorage.getItem('@ConnectHub:userData');
    return salvos ? JSON.parse(salvos) : {
      nome: 'Emanuel Vittor',
      email: 'exemplo@email.com',
      telefone: '(12) 93456-7890',
      endereco: 'Rua Exemplo, 123 - Campina Grande, PB',
      novaSenha: '',
      confirmarSenha: ''
    };
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData(prev => ({ ...prev, [name]: value }));
  };

  const handleConfigChange = (name) => {
    setConfigs(prev => ({ ...prev, [name]: !prev[name] }))
  }

  const handleSave = () => {
  const dadosAntigos = JSON.parse(localStorage.getItem('@ConnectHub:userData'));
  const senhaGravada = dadosAntigos?.novaSenha || '123456';

  if (userData.senhaAtual !== senhaGravada) {
    alert("A 'Senha Atual' está incorreta! Não podemos salvar as alterações.");
    return;
  }

  if (userData.novaSenha !== userData.confirmarSenha) {
    alert("As novas senhas não coincidem!");
    return;
  }

  localStorage.setItem('@ConnectHub:userData', JSON.stringify(userData));
  alert("Alterações salvas com sucesso! ✅");
  
  setUserData(prev => ({ ...prev, senhaAtual: '', novaSenha: '', confirmarSenha: '' }));
};

  return (
    <div className="profile-page-container" style={{ paddingTop: '120px' }}>
      <aside className="profile-sidebar">
        <div className="profile-header-sidebar">
          <div className="profile-avatar">
            <User size={40} color="#0090C1" />
          </div>
          <div className="profile-info">
            <h1>{userData?.nome?.split(' ')[0] || 'Usuário'}</h1>
            <span>Membro desde 2026</span>
          </div>
        </div>

        <nav className="profile-tabs-nav">
          <button className={`tab-btn ${activeTab === 'dados' ? 'active' : ''}`} onClick={() => setActiveTab('dados')}>
            Dados Pessoais
          </button>
          <button className={`tab-btn ${activeTab === 'seguranca' ? 'active' : ''}`} onClick={() => setActiveTab('seguranca')}>
            Segurança
          </button>
          <button className={`tab-btn ${activeTab === 'config' ? 'active' : ''}`} onClick={() => setActiveTab('config')}>
            Configurações
          </button>
        </nav>
      </aside>

      <main className="profile-card">
        {activeTab === 'dados' && (
          <div className="tab-section">
            <h2>Meus Dados</h2>
            <div className="profile-details" style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
              <div className="detail-group">
                <label>Nome Completo</label>
                <input className="profile-input" name="nome" value={userData.nome} onChange={handleChange} />
              </div>
              <div className="detail-group">
                <label>E-mail</label>
                <input className="profile-input" name="email" value={userData.email} onChange={handleChange} />
              </div>
              <div className="detail-group">
                <label>Endereço</label>
                <input className="profile-input" name="endereco" value={userData.endereco} onChange={handleChange} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'seguranca' && (
  <div className="tab-section">
    <h2>Segurança</h2>
    <div className="profile-details" style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
      
      <div className="detail-group">
        <label>Senha Atual</label>
        <input 
          type={showPassword ? "text" : "password"} 
          className="profile-input" 
          name="senhaAtual" 
          placeholder="Digite sua senha atual para confirmar"
          value={userData.senhaAtual || ''} 
          onChange={handleChange} 
        />
      </div>

      <hr style={{ border: '0.5px solid #eee', margin: '10px 0' }} />

      <div className="detail-group">
        <label>Nova Senha</label>
        <input 
          type={showPassword ? "text" : "password"} 
          className="profile-input" 
          name="novaSenha" 
          placeholder="Digite a nova senha"
          value={userData.novaSenha || ''} 
          onChange={handleChange} 
        />
      </div>

      <div className="detail-group">
        <label>Confirmar Nova Senha</label>
        <input 
          type={showPassword ? "text" : "password"} 
          className="profile-input" 
          name="confirmarSenha" 
          placeholder="Repita a nova senha"
          value={userData.confirmarSenha || ''} 
          onChange={handleChange} 
        />
      </div>

      <button 
        type="button" 
        onClick={() => setShowPassword(!showPassword)}
        style={{ background: 'none', border: 'none', color: '#0090C1', cursor: 'pointer', textAlign: 'left', fontWeight: 'bold', fontSize: '12px' }}
      >
        {showPassword ? "Esconder senhas" : "Ver senhas digitadas"}
      </button>
    </div>
  </div>
)}

{activeTab === 'config' && (
  <div className='tab-section'>
    <h2>Configurações da Conta</h2>

    <div className='config-group'>
      <h3><Bell size={18}/>Notificações</h3>
      <div className='config-item'>
        <span>Receber E-mails</span>
        <input type="checkbox" checked={configs.notificacoesEmail} onChange={() => handleConfigChange('notificacoesEmail')} />
      </div>
      <div className='config-item'>
        <span>Receber Sms</span>
        <input type="checkbox" checked={configs.notificacoesSms} onChange={() => handleConfigChange('notificacoesSms')} />
      </div>
    </div>

    <div className='config-group danger-zone'>
      <h3><Trash2 size={18}/>Deletar conta</h3>
      <p>Uma vez que deletar sua conta, não poderá recuperá-la, certeza?</p>
      <button className='delete-account-btn' onClick={() => alert('Em desenvolvimento')}>
        Excluir minha conta
      </button>
    </div>
  </div>
)}

        <div className="profile-actions" style={{ marginTop: '30px' }}>
          <button className="edit-profile-btn" onClick={handleSave}>
            Salvar Alterações
          </button>
          <br />
          <Link to="/" className="back-home-link">← Voltar para a loja</Link>
        </div>
      </main>
    </div>
  );
}

export default ProfilePage;