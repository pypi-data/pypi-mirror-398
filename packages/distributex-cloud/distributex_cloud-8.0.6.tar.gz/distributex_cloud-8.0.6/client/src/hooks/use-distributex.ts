// client/src/hooks/use-distributex.ts - COMPLETE FIXED
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

async function fetcher(url: string, options?: RequestInit) {
  const response = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// User
export function useUser() {
  return useQuery({
    queryKey: ["/api/auth/user"],
    queryFn: () => fetcher("/api/auth/user"),
    retry: false,
  });
}

// Workers
export function useWorkers() {
  return useQuery({
    queryKey: ["/api/workers"],
    queryFn: () => fetcher("/api/workers"),
  });
}

export function useCreateWorker() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (worker: any) => fetcher("/api/workers", {
      method: "POST",
      body: JSON.stringify(worker),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/workers"] });
    },
  });
}

// FIXED: Remove Worker with Proper Authentication and Error Handling
export function useRemoveWorker() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (workerId: string | number) => {
      const id = typeof workerId === 'string' ? parseInt(workerId) : workerId;
      
      if (isNaN(id)) {
        throw new Error("Invalid worker ID");
      }
      
      console.log(`🗑️ Attempting to delete worker #${id}...`);
      
      const response = await fetch(`/api/workers/${id}`, {
        method: "DELETE",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          message: `HTTP ${response.status}: ${response.statusText}` 
        }));
        throw new Error(error.message || "Failed to delete worker");
      }

      return response.json();
    },
    onSuccess: (data, workerId) => {
      console.log(`✅ Worker #${workerId} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ["/api/workers"] });
    },
    onError: (error: Error, workerId) => {
      console.error(`❌ Failed to delete worker #${workerId}:`, error.message);
    }
  });
}

// Jobs
export function useJobs() {
  return useQuery({
    queryKey: ["/api/jobs"],
    queryFn: () => fetcher("/api/jobs"),
  });
}

export function useJob(id: number) {
  return useQuery({
    queryKey: ["/api/jobs", id],
    queryFn: () => fetcher(`/api/jobs/${id}`),
    enabled: !!id,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (job: any) => fetcher("/api/jobs", {
      method: "POST",
      body: JSON.stringify(job),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/jobs"] });
    },
  });
}
