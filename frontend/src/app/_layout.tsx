import { QueryClientProvider } from '@tanstack/react-query';
import { Redirect, Stack, useSegments, type Href } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';

import { palette } from '@/config/constants';
import { useAuthStore } from '@/features/auth/store';
import { queryClient } from '@/services/api/queryClient';

function SessionGate() {
  const { session, hydrated, hydrate } = useAuthStore();
  const segments = useSegments() as string[];
  const inLogin = segments[0] === 'login';
  const inApp = segments[0] === '(app)';

  useEffect(() => { void hydrate(); }, [hydrate]);

  if (!hydrated) {
    return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.canvas }}><ActivityIndicator color={palette.forest} /></View>;
  }

  if (!session && !inLogin && segments.length > 0) return <Redirect href={'/login' as Href} />;
  if (session && inLogin) return <Redirect href={'/(app)' as Href} />;
  if (session && !inApp && segments[0] !== undefined) return <Redirect href={'/(app)' as Href} />;

  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: palette.canvas } }} />
  );
}

export default function RootLayout() {
  return <QueryClientProvider client={queryClient}><SessionGate /></QueryClientProvider>;
}
