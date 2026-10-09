import { api } from '@/services/api/client';
import type { LoginInput, Session } from '@/features/auth/types';

export const authService = {
  async login(credentials: LoginInput) {
    const { data } = await api.post<Session>('/auth/login', credentials);
    return data;
  },
};