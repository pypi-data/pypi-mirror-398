#!/usr/bin/env node

/**
 * Setup script to generate .env.server if it doesn't exist.
 * Run automatically before `yarn dev`.
 */

import { existsSync, readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, '..');

const envServerPath = resolve(rootDir, '.env.server');
const envExamplePath = resolve(rootDir, '.env.example');

if (existsSync(envServerPath)) {
    console.log('✓ .env.server already exists');
    process.exit(0);
}

console.log('Creating .env.server from .env.example...');

if (!existsSync(envExamplePath)) {
    console.error('Error: .env.example not found');
    process.exit(1);
}

// Read .env.example and add PORT if not present
let content = readFileSync(envExamplePath, 'utf-8');

// Add PORT=3000 if not already in the file
if (!content.includes('PORT=')) {
    content = `PORT=3000\n${content}`;
}

writeFileSync(envServerPath, content);
console.log('✓ Created .env.server with PORT=3000');
console.log('  → Edit .env.server to add your TDP credentials');

