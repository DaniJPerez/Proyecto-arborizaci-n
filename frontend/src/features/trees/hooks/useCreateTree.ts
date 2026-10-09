import { useMutation, useQueryClient } from '@tanstack/react-query';

import { treesService } from '@/features/trees/services/treesService';

export const treeKeys = { lists: ['trees', 'list'] as const };

export function useCreateTree() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: treesService.create,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: treeKeys.lists }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]);
    },
  });
}