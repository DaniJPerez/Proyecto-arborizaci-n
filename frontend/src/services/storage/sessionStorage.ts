import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { SESSION_STORAGE_KEY } from '@/config/constants';
import type { Session } from '@/shared/types/entities';

let webSessionValue: string | null = null;

export async function readStoredSession(): Promise<Session | null> {
  const value = Platform.OS === 'web'
    ? webSessionValue
    : await SecureStore.getItemAsync(SESSION_STORAGE_KEY);
  if (!value) return null;

  try {
    return JSON.parse(value) as Session;
  } catch {
    await SecureStore.deleteItemAsync(SESSION_STORAGE_KEY);
    return null;
  }
}

export function writeStoredSession(session: Session) {
  const value = JSON.stringify(session);
  if (Platform.OS === 'web') {
    webSessionValue = value;
    return Promise.resolve();
  }
  return SecureStore.setItemAsync(SESSION_STORAGE_KEY, value);
}

export function clearStoredSession() {
  if (Platform.OS === 'web') {
    webSessionValue = null;
    return Promise.resolve();
  }
  return SecureStore.deleteItemAsync(SESSION_STORAGE_KEY);
}