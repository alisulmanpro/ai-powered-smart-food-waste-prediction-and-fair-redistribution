import { useState } from 'react'
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { ApiError, api, type Me, type Role } from '../api/client'
import { ErrorBanner, LinkButton, PrimaryButton, RolePicker, TextField } from '../components/ui'
import {
  validateConfirm,
  validateEmail,
  validateName,
  validatePassword,
  validateSignInPassword,
} from '../lib/validation'

type Mode = 'signin' | 'signup'
type FieldName = 'name' | 'email' | 'password' | 'confirm'

export default function AuthScreen({ onAuthed }: { onAuthed: (me: Me) => void }) {
  const [mode, setMode] = useState<Mode>('signin')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [role, setRole] = useState<Role>('donor')
  const [touched, setTouched] = useState<Partial<Record<FieldName, boolean>>>({})
  const [serverErrors, setServerErrors] = useState<Partial<Record<FieldName, string>>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const isSignUp = mode === 'signup'

  const errors: Record<FieldName, string | null> = {
    name: isSignUp ? validateName(name) : null,
    email: validateEmail(email),
    password: isSignUp ? validatePassword(password) : validateSignInPassword(password),
    confirm: isSignUp ? validateConfirm(password, confirm) : null,
  }

  function errorFor(field: FieldName): string | null {
    if (serverErrors[field]) return serverErrors[field] ?? null
    return touched[field] ? errors[field] : null
  }

  function touch(field: FieldName) {
    setTouched((t) => ({ ...t, [field]: true }))
  }

  function clearServerError(field: FieldName) {
    setServerErrors((e) => ({ ...e, [field]: undefined }))
  }

  function switchMode(next: Mode) {
    setMode(next)
    setTouched({})
    setServerErrors({})
    setFormError(null)
    setNotice(null)
    setConfirm('')
  }

  async function onSubmit() {
    setTouched({ name: true, email: true, password: true, confirm: true })
    setFormError(null)
    setNotice(null)
    const fields: FieldName[] = isSignUp
      ? ['name', 'email', 'password', 'confirm']
      : ['email', 'password']
    if (fields.some((f) => errors[f])) return

    setSubmitting(true)
    try {
      if (isSignUp) {
        await api.register(name.trim(), email.trim(), password, role)
      }
      try {
        await api.login(email.trim(), password)
      } catch (err) {
        if (
          err instanceof ApiError &&
          err.status === 403 &&
          /not verified/i.test(err.message)
        ) {
          setNotice(
            'Verification email sent! Check your inbox and verify your account, then sign in.',
          )
          setMode('signin')
          setTouched({})
          setConfirm('')
          return
        }
        throw err
      }
      onAuthed(await api.me())
    } catch (err) {
      if (err instanceof ApiError && isSignUp && err.status === 409) {
        setServerErrors({ email: err.message })
      } else if (
        err instanceof ApiError &&
        !isSignUp &&
        err.status === 403 &&
        /not verified/i.test(err.message)
      ) {
        setNotice(err.message)
      } else {
        setFormError(err instanceof Error ? err.message : 'Something went wrong')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function onResendVerification() {
    setFormError(null)
    setSubmitting(true)
    try {
      await api.resendVerification(email.trim())
      setNotice('If that address is unverified, a new verification email is on its way.')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>Food Waste Redistribution</Text>
        <Text style={styles.subtitle}>
          {isSignUp ? 'Create your account' : 'Sign in to your account'}
        </Text>

        <View style={styles.card}>
          {formError ? <ErrorBanner message={formError} /> : null}
          {notice ? (
            <View style={styles.notice}>
              <Text style={styles.noticeText}>{notice}</Text>
            </View>
          ) : null}
          {notice && !isSignUp && email ? (
            <LinkButton title="Resend verification email" onPress={onResendVerification} />
          ) : null}

          {isSignUp ? (
            <>
              <RolePicker value={role} onChange={setRole} />
              <TextField
                label="Name"
                placeholder="Your name or organisation"
                value={name}
                onChangeText={(v) => {
                  setName(v)
                  clearServerError('name')
                }}
                onBlur={() => touch('name')}
                error={errorFor('name')}
                maxLength={120}
                autoCapitalize="words"
                returnKeyType="next"
              />
            </>
          ) : null}

          <TextField
            label="Email"
            placeholder="you@example.com"
            value={email}
            onChangeText={(v) => {
              setEmail(v)
              clearServerError('email')
            }}
            onBlur={() => touch('email')}
            error={errorFor('email')}
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            returnKeyType="next"
          />

          <TextField
            label="Password"
            placeholder={isSignUp ? 'At least 8 characters' : 'Your password'}
            value={password}
            onChangeText={(v) => {
              setPassword(v)
              clearServerError('password')
            }}
            onBlur={() => touch('password')}
            error={errorFor('password')}
            secureTextEntry
            returnKeyType={isSignUp ? 'next' : 'done'}
            onSubmitEditing={isSignUp ? undefined : onSubmit}
          />

          {isSignUp ? (
            <TextField
              label="Confirm password"
              placeholder="Repeat your password"
              value={confirm}
              onChangeText={(v) => {
                setConfirm(v)
                clearServerError('confirm')
              }}
              onBlur={() => touch('confirm')}
              error={errorFor('confirm')}
              secureTextEntry
              returnKeyType="done"
              onSubmitEditing={onSubmit}
            />
          ) : null}

          <PrimaryButton
            title={isSignUp ? 'Sign up' : 'Sign in'}
            onPress={onSubmit}
            loading={submitting}
          />

          <LinkButton
            title={
              isSignUp
                ? 'Already have an account? Sign in'
                : 'New here? Create an account'
            }
            onPress={() => switchMode(isSignUp ? 'signin' : 'signup')}
          />

          {isSignUp ? (
            <Text style={styles.note}>
              Admin accounts can only be created by an administrator.
            </Text>
          ) : null}
        </View>

        <Text style={styles.footer}>Decision support only. Follow food-safety rules.</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f5f7fa' },
  container: { flexGrow: 1, justifyContent: 'center', padding: 24, gap: 8 },
  title: { fontSize: 22, fontWeight: '600', color: '#1f2933' },
  subtitle: { color: '#616e7c', marginBottom: 8 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, gap: 14 },
  notice: {
    backgroundColor: '#e6f4ea',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#a7d7b8',
  },
  noticeText: { color: '#276749', fontSize: 14 },
  note: { color: '#616e7c', fontSize: 13, textAlign: 'center' },
  footer: { color: '#9aa5b1', fontSize: 12, textAlign: 'center', marginTop: 16 },
})
