import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Analytics, Dashboard, DocumentItem, Goal, LessonView, SubjectSummary, TopicCard } from "@/lib/types";

export const useDashboard = () => useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dashboard>("/api/dashboard") });
export const useSubjects = () => useQuery({ queryKey: ["subjects"], queryFn: () => api<SubjectSummary[]>("/api/subjects") });
export const useTopics = () => useQuery({ queryKey: ["topics"], queryFn: () => api<TopicCard[]>("/api/topics") });
export const useLesson = (id: number) =>
  useQuery({ queryKey: ["lesson", id], queryFn: () => api<LessonView>(`/api/lessons/${id}/start`, { method: "POST" }), staleTime: Infinity });
export const useAnalytics = (days: number) => useQuery({ queryKey: ["analytics", days], queryFn: () => api<Analytics>(`/api/analytics?days=${days}`) });
export const useDocuments = () => useQuery({ queryKey: ["documents"], queryFn: () => api<DocumentItem[]>("/api/documents") });
export const useGoals = () => useQuery({ queryKey: ["goals"], queryFn: () => api<Goal[]>("/api/goals") });
