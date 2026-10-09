import { api } from '@/services/api/client';
import type { Catalogos } from '@/features/catalogs/types';

export const catalogsService = {
  async getAll() {
    const { data } = await api.get<Catalogos>('/catalogos');
    return data;
  },
};