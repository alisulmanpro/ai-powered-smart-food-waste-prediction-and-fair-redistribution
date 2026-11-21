// One-command local setup:  npm run setup
// - creates .env files from the .env.example files (never overwrites existing ones)
// - installs admin + mobile dependencies
// - checks that Docker is available
import { execSync } from 'node:child_process'
import { copyFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const run = (cmd, cwd = root) => execSync(cmd, { cwd, stdio: 'inherit' })
const ok = (cmd) => {
  try {
    execSync(cmd, { stdio: 'ignore' })
    return true
  } catch {
    return false
  }
}

console.log('\n1/3  Environment files')
for (const dir of ['.', 'admin', 'mobile']) {
  const example = join(root, dir, '.env.example')
  const target = join(root, dir, '.env')
  if (existsSync(target)) console.log(`  ${join(dir, '.env')} already exists, skipped`)
  else if (existsSync(example)) {
    copyFileSync(example, target)
    console.log(`  created ${join(dir, '.env')}`)
  }
}

console.log('\n2/3  Frontend dependencies')
for (const dir of ['admin', 'mobile']) {
  console.log(`  npm install in ${dir}/`)
  run('npm install --no-audit --no-fund', join(root, dir))
}

console.log('\n3/3  Docker')
if (ok('docker compose version')) console.log('  docker compose found')
else console.warn('  WARNING: docker compose not found. Install Docker Desktop to run the backend.')

console.log(`
Done. Next:
  npm run up            # Postgres + backend with hot reload  -> http://localhost:8000/docs
  npm run mobile:start  # Expo (in another terminal)
  npm run admin:dev     # React admin (or: npm run up:admin to run it in Docker)
`)
