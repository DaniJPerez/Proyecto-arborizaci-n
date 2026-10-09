import { api } from '@/services/api/client';
import type { ArbolResumen } from '@/shared/types/entities';
import type { ArbolCrear } from '@/features/trees/types';

export const treesService = {
  async getAll() {
    const { data } = await api.get<ArbolResumen[]>('/arboles', {
      params: {
        limite: 100,
        desplazamiento: 0,
      },
    });

    return data;
  },

  async create(payload: ArbolCrear) {
    const { data } = await api.post<ArbolResumen>('/arboles', payload);
    return data;
  },
};