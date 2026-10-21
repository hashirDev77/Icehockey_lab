export type Json = Record<string, unknown>;

export interface ProviderResult {
  endpoint: string;
  status: number;
  body: Json | null;
  error?: string;
}

function errorText(body: Json | null, status: number): string {
  const raw = body?.message ?? body?.error ?? body?.detail;
  if (typeof raw === "string" && raw.trim()) return raw;
  if (Array.isArray(raw)) return raw.map(String).join("; ");
  if (raw && typeof raw === "object") {
    const obj = raw as Json;
    if (typeof obj.message === "string") return obj.message;
    try {
      return JSON.stringify(raw);
    } catch {
      /* fall through */
    }
  }
  return `Request failed (${status})`;
}

export async function iceHockeyGet(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<ProviderResult> {
  const clean = path.replace(/^\//, "").replace(/^v1\/ice_hockey\//, "");
  const url = new URL(`/msdata/v1/ice_hockey/${clean}`, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }
  const endpoint = `/v1/ice_hockey/${clean}${url.search}`;
  const response = await fetch(url.toString(), { headers: { accept: "application/json" } });
  const text = await response.text();
  let body: Json | null = null;
  if (text) {
    try {
      body = JSON.parse(text) as Json;
    } catch {
      if (!response.ok && response.status !== 404) {
        throw new Error(text.slice(0, 200) || `Request failed (${response.status})`);
      }
      return { endpoint, status: response.status, body: null, error: "Response was not JSON" };
    }
  }
  if (response.status === 404) {
    return { endpoint, status: 404, body: null };
  }
  if (!response.ok) {
    throw new Error(errorText(body, response.status));
  }
  return { endpoint, status: response.status, body };
}
