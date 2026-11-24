const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateName(name: string): string | null {
  const value = name.trim()
  if (!value) return 'Name is required'
  if (value.length > 120) return 'Name must be at most 120 characters'
  return null
}

export function validateEmail(email: string): string | null {
  const value = email.trim()
  if (!value) return 'Email is required'
  if (!EMAIL_RE.test(value)) return 'Enter a valid email address'
  return null
}

export function validatePassword(password: string): string | null {
  if (!password) return 'Password is required'
  if (password.length < 8) return 'Password must be at least 8 characters'
  if (password.length > 128) return 'Password must be at most 128 characters'
  return null
}

export function validateSignInPassword(password: string): string | null {
  return password ? null : 'Password is required'
}

export function validateConfirm(password: string, confirm: string): string | null {
  if (!confirm) return 'Confirm your password'
  if (password !== confirm) return 'Passwords do not match'
  return null
}
