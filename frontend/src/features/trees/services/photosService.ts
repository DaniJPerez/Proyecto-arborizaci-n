import { api } from '@/services/api/client';
import type { FotoLocal } from '@/features/trees/types';
import { Platform } from 'react-native';

export const photosService = {
  async upload(treeId: string, photo: FotoLocal) {
    const form = new FormData();
    if (Platform.OS === 'web') {
      const response = await fetch(photo.uri);
      if (!response.ok) {
        throw new Error('No se pudo leer la fotografía seleccionada.');
      }
      form.append('archivo', await response.blob(), photo.name);
    } else {
      form.append('archivo', {
        uri: photo.uri,
        name: photo.name,
        type: photo.mimeType,
      } as unknown as Blob);
    }
    const { data } = await api.post(`/arboles/${treeId}/fotos`, form, {
      params: { tipo: photo.tipo },
    });
    return data;
  },
};