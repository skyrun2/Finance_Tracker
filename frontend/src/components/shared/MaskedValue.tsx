"use client"

import { useVisibility } from "@/hooks/use-visibility"

export function MaskedValue({ value }: { value: string }) {
  const { visible } = useVisibility()
  return <span>{visible ? value : "$ ••••"}</span>
}
