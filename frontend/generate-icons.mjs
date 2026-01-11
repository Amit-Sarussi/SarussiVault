// Icon generation script for PWA
// Usage: npm install sharp --save-dev
// Then: node generate-icons.mjs

import sharp from 'sharp'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const logoPath = join(__dirname, 'src', 'assets', 'logo.svg')
const publicDir = join(__dirname, 'public')

async function generateIcons() {
  try {
    console.log('Generating PWA icons...')
    
    // Generate 192x192 icon
    await sharp(logoPath)
      .resize(192, 192, {
        fit: 'contain',
        background: { r: 255, g: 255, b: 255, alpha: 1 }
      })
      .png()
      .toFile(join(publicDir, 'icon-192x192.png'))
    
    console.log('✓ Generated icon-192x192.png')
    
    // Generate 512x512 icon
    await sharp(logoPath)
      .resize(512, 512, {
        fit: 'contain',
        background: { r: 255, g: 255, b: 255, alpha: 1 }
      })
      .png()
      .toFile(join(publicDir, 'icon-512x512.png'))
    
    console.log('✓ Generated icon-512x512.png')
    console.log('Icons generated successfully!')
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      console.error(`
Error: sharp module not found.
Please install it first:
  npm install sharp --save-dev
`)
    } else {
      console.error('Error generating icons:', error.message)
    }
    process.exit(1)
  }
}

generateIcons()
