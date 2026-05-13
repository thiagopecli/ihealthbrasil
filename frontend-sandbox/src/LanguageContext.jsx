import React, { createContext, useContext, useState, useEffect } from 'react'
import { getCurrentLanguage, setLanguage } from './i18n'

const LanguageContext = createContext()

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => getCurrentLanguage())

  const changeLanguage = (lang) => {
    setLanguageState(lang)
    setLanguage(lang)
  }

  return (
    <LanguageContext.Provider value={{ language, changeLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage deve ser usado dentro de LanguageProvider')
  }
  return context
}
