"use client"

import { createContext, useContext, useState } from "react"

type VisibilityContextType = {
  visible: boolean
  toggle: () => void
}

const VisibilityContext = createContext<VisibilityContextType>({
  visible: true,
  toggle: () => {},
})

export function VisibilityProvider({ children }: { children: React.ReactNode }) {
  const [visible, setVisible] = useState(true)
  const toggle = () => setVisible((v) => !v)
  return (
    <VisibilityContext.Provider value={{ visible, toggle }}>
      {children}
    </VisibilityContext.Provider>
  )
}

export function useVisibility() {
  return useContext(VisibilityContext)
}
