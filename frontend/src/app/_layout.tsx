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
  const inPreview = segments[0] === 'inventario-preview';

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: palette.canvas,
        }}
      >
        <ActivityIndicator color={palette.forest} />
      </View>
    );
  }

  // Permitir el acceso temporal al inventario de demostración.
  if (
    !session &&
    !inLogin &&
    !inPreview &&
    segments.length > 0
  ) {
    return <Redirect href={'/login' as Href} />;
  }

  // Si hay sesión, enviar al panel principal al entrar al login.
  if (session && inLogin) {
    return <Redirect href={'/(app)' as Href} />;
  }

  // Si hay sesión, mantener la navegación dentro de la aplicación.
  if (session && !inApp && !inPreview && segments[0] !== undefined) {
    return <Redirect href={'/(app)' as Href} />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: {
          backgroundColor: palette.canvas,
        },
      }}
    />
  );
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionGate />
    </QueryClientProvider>
  );
}