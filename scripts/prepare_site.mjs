import { cp, mkdir, rm } from 'node:fs/promises'

await rm('dist', { recursive: true, force: true })
await mkdir('dist', { recursive: true })
await cp('frontend/dist', 'dist', { recursive: true })
console.log('Prepared static Site output in dist/')
