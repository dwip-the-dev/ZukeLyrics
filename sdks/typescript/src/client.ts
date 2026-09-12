import { ZukeLyricsPayload, ZukeCatalogItem, ZukeStats } from "./types";

export interface ZukeClientOptions {
  owner?: string;
  repo?: string;
  branch?: string;
  token?: string;
  cacheTtlMs?: number;
}

export class ZukeLyricsClient {
  private owner: string;
  private repo: string;
  private branch: string;
  private token?: string;
  private cache: Map<string, { data: ZukeLyricsPayload; timestamp: number }> = new Map();
  private cacheTtlMs: number;

  constructor(options: ZukeClientOptions = {}) {
    this.owner = options.owner || "dwip-the-dev";
    this.repo = options.repo || "ZukeLyrics";
    this.branch = options.branch || "main";
    this.token = options.token;
    this.cacheTtlMs = options.cacheTtlMs || 1000 * 60 * 30; // 30 minutes
  }

  /**
   * Generates hash-tree path: lyrics-database/{c1}/{c2}/{videoId}.json
   */
  public getRelativePath(videoId: string): string {
    const clean = videoId.trim();
    const c1 = clean.length > 0 && /^[a-zA-Z0-9]$/.test(clean[0]) ? clean[0] : "_";
    const c2 = clean.length > 1 && /^[a-zA-Z0-9]$/.test(clean[1]) ? clean[1] : "_";
    return `lyrics-database/${c1}/${c2}/${clean}.json`;
  }

  /**
   * Gets primary Raw GitHub CDN URL
   */
  public getPrimaryCdnUrl(videoId: string): string {
    return `https://raw.githubusercontent.com/${this.owner}/${this.repo}/${this.branch}/${this.getRelativePath(videoId)}`;
  }

  /**
   * Gets secondary jsDelivr unthrottled CDN URL
   */
  public getFallbackCdnUrl(videoId: string): string {
    return `https://cdn.jsdelivr.net/gh/${this.owner}/${this.repo}@${this.branch}/${this.getRelativePath(videoId)}`;
  }

  /**
   * Fast check if lyrics exist in the repository
   */
  public async hasLyrics(videoId: string): Promise<boolean> {
    try {
      const res = await fetch(this.getPrimaryCdnUrl(videoId), { method: "HEAD" });
      if (res.ok) return true;
    } catch {}

    try {
      const res = await fetch(this.getFallbackCdnUrl(videoId), { method: "HEAD" });
      return res.ok;
    } catch {
      return false;
    }
  }

  /**
   * Fetches lyrics for a given YouTube Video ID with caching and multi-CDN fallback
   */
  public async getLyrics(videoId: string): Promise<ZukeLyricsPayload | null> {
    const cached = this.cache.get(videoId);
    if (cached && Date.now() - cached.timestamp < this.cacheTtlMs) {
      return cached.data;
    }

    // Try Primary GitHub Raw CDN
    try {
      const res = await fetch(this.getPrimaryCdnUrl(videoId));
      if (res.ok) {
        const data = (await res.json()) as ZukeLyricsPayload;
        this.cache.set(videoId, { data, timestamp: Date.now() });
        return data;
      }
    } catch {}

    // Try Fallback jsDelivr CDN
    try {
      const res = await fetch(this.getFallbackCdnUrl(videoId));
      if (res.ok) {
        const data = (await res.json()) as ZukeLyricsPayload;
        this.cache.set(videoId, { data, timestamp: Date.now() });
        return data;
      }
    } catch {}

    return null;
  }

  /**
   * Fetches full catalog of all tracks in the database
   */
  public async getCatalog(): Promise<ZukeCatalogItem[]> {
    const url = `https://raw.githubusercontent.com/${this.owner}/${this.repo}/${this.branch}/index/catalog.json`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load catalog: ${res.statusText}`);
    return (await res.json()) as ZukeCatalogItem[];
  }

  /**
   * Fetches repository statistics
   */
  public async getStats(): Promise<ZukeStats> {
    const url = `https://raw.githubusercontent.com/${this.owner}/${this.repo}/${this.branch}/api/v1/stats.json`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load stats: ${res.statusText}`);
    return (await res.json()) as ZukeStats;
  }

  /**
   * Pushes/commits a lyrics payload directly to the repository (Requires GitHub PAT with push rights)
   */
  public async uploadLyrics(payload: ZukeLyricsPayload, token?: string): Promise<{ success: boolean; sha?: string; error?: string }> {
    const activeToken = token || this.token;
    if (!activeToken) {
      return { success: false, error: "No GitHub Personal Access Token (PAT) provided for write operation." };
    }

    const relPath = this.getRelativePath(payload.videoId);
    const apiUrl = `https://api.github.com/repos/${this.owner}/${this.repo}/contents/${relPath}`;
    const contentUtf8 = JSON.stringify(payload, null, 2);
    const base64Content = Buffer.from(contentUtf8, "utf-8").toString("base64");

    try {
      // Check if file already exists to obtain current SHA
      let existingSha: string | undefined;
      const getRes = await fetch(apiUrl, {
        headers: {
          Authorization: `Bearer ${activeToken}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "ZukeLyrics-TS-Client"
        }
      });
      if (getRes.ok) {
        const fileMeta = await getRes.json();
        existingSha = fileMeta.sha;
      }

      const body: any = {
        message: `Add/update synced lyrics for ${payload.title} - ${payload.artist} [${payload.videoId}]`,
        content: base64Content,
        branch: this.branch
      };
      if (existingSha) {
        body.sha = existingSha;
      }

      const putRes = await fetch(apiUrl, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${activeToken}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "User-Agent": "ZukeLyrics-TS-Client"
        },
        body: JSON.stringify(body)
      });

      if (putRes.status === 200 || putRes.status === 201) {
        const resData = await putRes.json();
        return { success: true, sha: resData.content?.sha };
      } else {
        const errText = await putRes.text();
        return { success: false, error: `GitHub API error (${putRes.status}): ${errText}` };
      }
    } catch (err: any) {
      return { success: false, error: err.message || String(err) };
    }
  }
}
