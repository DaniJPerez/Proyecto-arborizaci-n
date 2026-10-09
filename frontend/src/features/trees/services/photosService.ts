import { api } from '@/services/api/client';
import type { FotoLocal } from '@/features/trees/types';

export const photosService = {
  async upload(treeId: string, photo: FotoLocal) {
    const form = new FormData();
    form.append('archivo', {
      uri: photo.uri,
      name: photo.name,
      type: photo.mimeType,
    } as unknown as Blob);
    const { data } = await api.post(`/arboles/${treeId}/fotos`, form, {
      params: { tipo: photo.tipo },
    });
    return data;
  },
};