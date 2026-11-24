import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from 'react-native'
import type { Role } from '../api/client'

type TextFieldProps = TextInputProps & {
  label: string
  error?: string | null
}

export function TextField({ label, error, style, ...props }: TextFieldProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, error ? styles.inputError : null, style]}
        placeholderTextColor="#9aa5b1"
        {...props}
      />
      {error ? <Text style={styles.fieldError}>{error}</Text> : null}
    </View>
  )
}

type PrimaryButtonProps = {
  title: string
  onPress: () => void
  disabled?: boolean
  loading?: boolean
}

export function PrimaryButton({ title, onPress, disabled, loading }: PrimaryButtonProps) {
  const inactive = disabled || loading
  return (
    <Pressable
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.primary,
        pressed && !inactive ? styles.primaryPressed : null,
        inactive ? styles.primaryDisabled : null,
      ]}
      disabled={inactive}
      onPress={onPress}
    >
      {loading ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <Text style={styles.primaryText}>{title}</Text>
      )}
    </Pressable>
  )
}

export function LinkButton({ title, onPress }: { title: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      style={({ pressed }) => [styles.link, pressed ? styles.linkPressed : null]}
      onPress={onPress}
    >
      <Text style={styles.linkText}>{title}</Text>
    </Pressable>
  )
}

const ROLE_OPTIONS: { value: Role; title: string; description: string }[] = [
  { value: 'donor', title: 'Donor', description: 'I have surplus food to donate' },
  { value: 'recipient', title: 'Recipient', description: 'I collect food for my organisation' },
]

export function RolePicker({ value, onChange }: { value: Role; onChange: (role: Role) => void }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>I am a…</Text>
      <View style={styles.roleRow}>
        {ROLE_OPTIONS.map((option) => {
          const selected = value === option.value
          return (
            <Pressable
              key={option.value}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              style={[styles.roleCard, selected ? styles.roleCardSelected : null]}
              onPress={() => onChange(option.value)}
            >
              <Text style={[styles.roleTitle, selected ? styles.roleTitleSelected : null]}>
                {option.title}
              </Text>
              <Text style={styles.roleDescription}>{option.description}</Text>
            </Pressable>
          )
        })}
      </View>
    </View>
  )
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <View style={styles.banner} accessibilityRole="alert">
      <Text style={styles.bannerText}>{message}</Text>
    </View>
  )
}

export function Chip({ label, tone }: { label: string; tone: 'green' | 'amber' | 'blue' }) {
  const tones = {
    green: { bg: '#e6f4ea', fg: '#276749' },
    amber: { bg: '#fef3c7', fg: '#92400e' },
    blue: { bg: '#e0ecf7', fg: '#1f4e79' },
  } as const
  const t = tones[tone]
  return (
    <View style={[styles.chip, { backgroundColor: t.bg }]}>
      <Text style={[styles.chipText, { color: t.fg }]}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  field: { gap: 6 },
  label: { fontSize: 14, fontWeight: '600', color: '#3e4c59' },
  input: {
    borderWidth: 1,
    borderColor: '#cbd2d9',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    minHeight: 48,
    fontSize: 16,
    backgroundColor: '#fff',
    color: '#1f2933',
  },
  inputError: { borderColor: '#c53030' },
  fieldError: { color: '#c53030', fontSize: 13 },
  primary: {
    backgroundColor: '#2f855a',
    borderRadius: 8,
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  primaryPressed: { backgroundColor: '#276749' },
  primaryDisabled: { backgroundColor: '#9fb8a8' },
  primaryText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  link: { minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  linkPressed: { opacity: 0.6 },
  linkText: { color: '#2f855a', fontSize: 15, fontWeight: '600' },
  roleRow: { flexDirection: 'row', gap: 12 },
  roleCard: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#cbd2d9',
    borderRadius: 8,
    padding: 12,
    minHeight: 88,
    backgroundColor: '#fff',
    gap: 4,
  },
  roleCardSelected: { borderColor: '#2f855a', borderWidth: 2, backgroundColor: '#f0fff4' },
  roleTitle: { fontSize: 16, fontWeight: '600', color: '#3e4c59' },
  roleTitleSelected: { color: '#276749' },
  roleDescription: { fontSize: 13, color: '#616e7c' },
  banner: {
    backgroundColor: '#fde8e8',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#f5b5b5',
  },
  bannerText: { color: '#c53030', fontSize: 14 },
  chip: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4, alignSelf: 'flex-start' },
  chipText: { fontSize: 12, fontWeight: '600' },
})
