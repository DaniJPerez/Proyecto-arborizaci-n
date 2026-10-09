import { zodResolver } from '@hookform/resolvers/zod';
import { router, type Href } from 'expo-router';
import { Controller, useForm } from 'react-hook-form';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/config/constants';
import { useLogin } from '@/features/auth/hooks/useLogin';
import { loginSchema, type LoginFormValues } from '@/features/auth/schemas';
import { getApiErrorMessage } from '@/services/api/client';
import { Eyebrow, Field, InlineMessage, PrimaryButton } from '@/shared/components/FormControls';

export function LoginScreen() {
  const login = useLogin();
  const { control, handleSubmit } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  function submit(values: LoginFormValues) {
    login.mutate(values, {
      onSuccess: () => router.replace('/(app)' as Href),
    });
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.brandMark}><Text style={styles.brandIcon}>A</Text></View>
        <Eyebrow>Inventario arbóreo escolar</Eyebrow>
        <Text style={styles.title}>Cuidar empieza{ '\n' }por conocer.</Text>
        <Text style={styles.subtitle}>Ingresa con la cuenta asignada por tu institución.</Text>

        <View style={styles.form}>
          <Controller name="email" control={control} render={({ field, fieldState }) => (
            <Field
              label="Correo electrónico"
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              error={fieldState.error?.message}
              placeholder="nombre@institucion.edu.co"
            />
          )} />
          <Controller name="password" control={control} render={({ field, fieldState }) => (
            <Field
              label="Contraseña"
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              secureTextEntry
              autoComplete="password"
              error={fieldState.error?.message}
              placeholder="Tu contraseña"
            />
          )} />
          {login.error ? <InlineMessage>{getApiErrorMessage(login.error)}</InlineMessage> : null}
          <PrimaryButton title="Iniciar sesión" loading={login.isPending} onPress={handleSubmit(submit)} />
        </View>
        <Text style={styles.privacy}>Los registros quedan asociados a la institución y al usuario autenticado.</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: palette.canvas },
  content: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 26, paddingVertical: 36 },
  brandMark: { width: 54, height: 54, marginBottom: 26, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: palette.forest },
  brandIcon: { color: palette.leaf, fontSize: 30, fontWeight: '900' },
  title: { marginTop: 13, color: palette.ink, fontSize: 38, fontWeight: '900', lineHeight: 43 },
  subtitle: { maxWidth: 320, marginTop: 12, color: palette.muted, fontSize: 16, lineHeight: 23 },
  form: { marginTop: 34, gap: 6 },
  privacy: { marginTop: 24, color: palette.muted, fontSize: 12, lineHeight: 18 },
});