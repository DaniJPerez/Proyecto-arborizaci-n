import { api } from '@/services/api/client';
import type { ArbolResumen } from '@/shared/types/entities';
import type { ArbolCrear } from '@/features/trees/types';

export const treesService = {
  async create(payload: ArbolCrear) {
    const { data } = await api.post<ArbolResumen>('/arboles', payload);
    return data;
  },
};