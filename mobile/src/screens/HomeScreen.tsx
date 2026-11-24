import type { ReactNode } from 'react'
import { ScrollView, StyleSheet, Text, View } from 'react-native'
import type { Me } from '../api/client'
import { Chip, LinkButton } from '../components/ui'

const ROLE_LABEL: Record<Me['role'], string> = {
  donor: 'Donor',
  recipient: 'Recipient',
  admin: 'Admin',
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{title}</Text>
      {children}
    </View>
  )
}

function DonorHome({ me }: { me: Me }) {
  return (
    <>
      <Section title="Estimated surplus">
        <Chip label="Estimate" tone="blue" />
        <Text style={styles.big}>—</Text>
        <Text style={styles.muted}>
          Surplus predictions appear here once the prediction model is connected.
        </Text>
      </Section>
      <Section title="Your donations">
        <Text style={styles.muted}>
          No donations yet. The create-donation flow is coming in the next update.
        </Text>
        {me.donor_profile ? (
          <Text style={styles.muted}>Business: {me.donor_profile.business_name}</Text>
        ) : (
          <Text style={styles.muted}>Donor profile not set up yet.</Text>
        )}
      </Section>
    </>
  )
}

function RecipientHome({ me }: { me: Me }) {
  const profile = me.recipient_profile
  return (
    <>
      <Section title="Your organisation">
        {profile ? (
          <>
            <Text style={styles.body}>{profile.organisation_name}</Text>
            <Chip
              label={profile.verified ? 'Verified' : 'Pending admin verification'}
              tone={profile.verified ? 'green' : 'amber'}
            />
            <Text style={styles.muted}>Capacity: {profile.capacity_units} units</Text>
          </>
        ) : (
          <Text style={styles.muted}>
            Recipient profile not set up yet. Add your capacity, storage and categories to
            start receiving allocations.
          </Text>
        )}
      </Section>
      <Section title="Allocation inbox">
        <Text style={styles.muted}>
          No allocations yet. Offers matched to your profile will appear here.
        </Text>
      </Section>
    </>
  )
}

function AdminHome() {
  return (
    <>
      <Section title="Admin tools">
        <Text style={styles.muted}>
          Verify users, review allocations, plan collections and manage data & models from
          the admin panel. Mobile admin tooling is coming in the next update.
        </Text>
      </Section>
      <Section title="Accounts">
        <Text style={styles.muted}>
          Admin accounts can only be created by another administrator.
        </Text>
      </Section>
    </>
  )
}

export default function HomeScreen({ me, onLogout }: { me: Me; onLogout: () => void }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Welcome, {me.name}</Text>
          <Chip label={ROLE_LABEL[me.role]} tone="green" />
        </View>
        <LinkButton title="Sign out" onPress={onLogout} />
      </View>

      {me.role === 'donor' ? <DonorHome me={me} /> : null}
      {me.role === 'recipient' ? <RecipientHome me={me} /> : null}
      {me.role === 'admin' ? <AdminHome /> : null}

      <Text style={styles.footer}>Decision support only. Follow food-safety rules.</Text>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f5f7fa' },
  container: { padding: 24, gap: 16 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerText: { flex: 1, gap: 6 },
  title: { fontSize: 20, fontWeight: '600', color: '#1f2933' },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, gap: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600', color: '#1f2933' },
  big: { fontSize: 32, fontWeight: '700', color: '#1f2933' },
  body: { fontSize: 16, color: '#1f2933' },
  muted: { color: '#616e7c', fontSize: 14 },
  footer: { color: '#9aa5b1', fontSize: 12, textAlign: 'center', marginTop: 8 },
})
