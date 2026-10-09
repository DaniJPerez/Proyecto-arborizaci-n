import { useCreateTree } from '@/features/trees/hooks/useCreateTree';
import { useUploadPhoto } from '@/features/trees/hooks/useUploadPhoto';
import type { ArbolResumen } from '@/shared/types/entities';
import type { ArbolCrear, FotoLocal } from '@/features/trees/types';

interface RegistrationResult {
  tree: ArbolResumen;
  photoError?: unknown;
}

export function useRegisterTree() {
  const createTree = useCreateTree();
  const uploadPhoto = useUploadPhoto();

  async function submit(values: ArbolCrear, photos: FotoLocal[]): Promise<RegistrationResult> {
    const tree = await createTree.mutateAsync(values);
    try {
      for (const photo of photos) {
        await uploadPhoto.mutateAsync({ treeId: tree.id, photo });
      }
      return { tree };
    } catch (photoError) {
      return { tree, photoError };
    }
  }

  return {
    submit,
    isPending: createTree.isPending || uploadPhoto.isPending,
  };
}