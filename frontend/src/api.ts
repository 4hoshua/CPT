import { clearToken, getToken, setToken } from "./auth";

const BASE = "/api";

/** Raised when the server responds with 401 so the UI can return to login. */
export class UnauthorizedError extends Error {}

export async function login(username: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    throw new Error(
      res.status === 401 ? "Invalid username or password" : "Login failed"
    );
  }

  const data = (await res.json()) as { access_token: string };
  setToken(data.access_token);
}

async function authedFetch(path: string, init: RequestInit): Promise<Response> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...(init.headers ?? {}), Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    clearToken();
    throw new UnauthorizedError("Session expired");
  }
  return res;
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.detail ?? `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

/** Upload a .pkt/.pka file, return the decoded XML as a Blob. */
export async function convertToXml(file: File): Promise<Blob> {
  const form = new FormData();
  form.append("file", file);
  const res = await authedFetch("/convert/xml", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return res.blob();
}

/** Upload an XML file, return the extracted devices/cables JSON. */
export async function convertToJson(file: File): Promise<unknown> {
  const form = new FormData();
  form.append("file", file);
  const res = await authedFetch("/convert/json", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
