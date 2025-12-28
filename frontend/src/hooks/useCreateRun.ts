/**
 * React Query Hook for Creating Runs
 */

import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { createRun } from '@/lib/api/runs';
import type { CreateRunRequest, TaskResponse } from '@/types/run';

interface UseCreateRunOptions {
  onSuccess?: (data: TaskResponse) => void;
  onError?: (error: Error) => void;
}

export function useCreateRun(options?: UseCreateRunOptions) {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: CreateRunRequest) => createRun(data),
    onSuccess: (data) => {
      // Call custom success handler if provided
      if (options?.onSuccess) {
        options.onSuccess(data);
      } else {
        // Default: navigate to dashboard
        navigate('/dashboard');
      }
    },
    onError: (error) => {
      // Call custom error handler if provided
      if (options?.onError) {
        options.onError(error);
      }
      // Error will be handled by the component
      console.error('Failed to create run:', error);
    },
  });
}