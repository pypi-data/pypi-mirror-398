import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";

/**
 * WORKER MANAGEMENT
 */
export function useWorkers() {
  return useQuery<any[]>({
    queryKey: ["/api/workers"],
  });
}

export function useCreateWorker() {
  return useMutation({
    mutationFn: async (workerData: any) => {
      const res = await fetch("/api/workers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(workerData),
      });
      if (!res.ok) throw new Error("Failed to create worker");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/workers"] });
    },
  });
}

export function useRemoveWorker() {
  return useMutation({
    mutationFn: async (id: string | number) => {
      const res = await fetch(`/api/workers/${id}`, { 
        method: "DELETE",
        headers: { "Content-Type": "application/json" }
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.message || "Failed to remove worker");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/workers"] });
    },
  });
}

/**
 * JOB MANAGEMENT
 */
export function useJobs() {
  return useQuery<any[]>({
    queryKey: ["/api/jobs"],
  });
}

const submitJobFn = async (jobData: any) => {
  const res = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobData),
  });
  if (!res.ok) throw new Error("Failed to submit job");
  return res.json();
};

// Satisfies both 'useSubmitJob' and 'useCreateJob' imports
export function useSubmitJob() {
  return useMutation({
    mutationFn: submitJobFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["/api/jobs"] }),
  });
}

export function useCreateJob() {
  return useMutation({
    mutationFn: submitJobFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["/api/jobs"] }),
  });
}

/**
 * AUTH & USER
 */
export function useUser() {
  return useQuery<any>({
    queryKey: ["/api/auth/user"],
  });
}
