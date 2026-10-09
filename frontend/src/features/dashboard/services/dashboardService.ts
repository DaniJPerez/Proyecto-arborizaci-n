import { api } from '@/services/api/client';
import type { ArbolResumen } from '@/shared/types/entities';
import type { Estadisticas } from '@/features/dashboard/types';

export const dashboardService = {
  async getStats() {
    const { data } = await api.get<Estadisticas>('/estadisticas');
    return data;
  },
  async getRecentTrees() {
    const { data } = await api.get<ArbolResumen[]>('/arboles', {
      params: { limite: 5, desplazamiento: 0 },
    });
    return data;
  },
};