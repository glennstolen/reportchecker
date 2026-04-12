export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Wrapper rundt fetch() som automatisk:
 * - Legger til riktig base-URL
 * - Sender session-cookie med alle forespørsler
 * - Redirecter til /login ved 401 (utløpt/ugyldig sesjon)
 */
export async function apiFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401 && typeof window !== "undefined") {
    window.location.href = "/login";
    return new Promise(() => {});
  }

  return response;
}
