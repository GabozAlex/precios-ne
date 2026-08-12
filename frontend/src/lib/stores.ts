import type { StoreKey } from './types'

export type { StoreKey }

export const STORE_KEYS: StoreKey[] = ['damasco', 'multimax', 'daka', 'ivoo']

export const STORE_WEBSITES: Record<StoreKey, string> = {
  damasco: 'https://www.damascovzla.com',
  multimax: 'https://multimax.com.ve',
  daka: 'https://tiendasdaka.com/ve',
  ivoo: 'https://www.ivoo.com',
}

export interface StoreMeta {
  key: StoreKey
  label: string
  colorClass: string
  website: string
}

export const STORES: Record<StoreKey, StoreMeta> = {
  damasco: {
    key: 'damasco',
    label: 'Damasco',
    colorClass: 'bg-store-damasco',
    website: STORE_WEBSITES.damasco,
  },
  multimax: {
    key: 'multimax',
    label: 'Multimax',
    colorClass: 'bg-store-multimax',
    website: STORE_WEBSITES.multimax,
  },
  daka: {
    key: 'daka',
    label: 'Daka',
    colorClass: 'bg-store-daka',
    website: STORE_WEBSITES.daka,
  },
  ivoo: {
    key: 'ivoo',
    label: 'Ivoo',
    colorClass: 'bg-store-ivoo',
    website: STORE_WEBSITES.ivoo,
  },
}

export function getStoreMeta(key: string): StoreMeta {
  return STORES[key as StoreKey] || {
    key: key as StoreKey,
    label: key,
    colorClass: 'bg-gray-400',
    website: '#',
  }
}
