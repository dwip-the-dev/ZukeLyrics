/**
 * ZukeLyrics Format (ZLF v1) Type Definitions
 */

export type SyncedType = "word" | "line" | "plain" | "instrumental";

export interface ZukeWordEntry {
  /** Start time in milliseconds */
  startTime: number;
  /** End time in milliseconds */
  endTime: number;
  /** Word or syllable token with optional trailing space */
  word: string;
}

export interface ZukeLyricLine {
  /** Line start time in milliseconds */
  time: number;
  /** Line end time in milliseconds */
  endTime: number;
  /** Plain text string of the line */
  text: string;
  /** Translated text in target language */
  translation?: string;
  /** Multi-language translations keyed by ISO language code */
  translations?: Record<string, string>;
  /** Romanized phonetic pronunciation (Romaji, Pinyin, etc.) */
  romanization?: string;
  /** Alias for romanization */
  romanized?: string;
  /** Whether the line is sung in duet / alternate voice */
  isDuet?: boolean;
  /** Whether the line is background vocal or ad-lib */
  isBackground?: boolean;
  /** Vocalist identifier (e.g. 'v1', 'v2', 'Freddie Mercury') */
  agent?: string;
  /** Word-level timing entries for progressive karaoke rendering */
  words?: ZukeWordEntry[];
}

export interface ZukeLyricsPayload {
  $schema?: string;
  version: number;
  videoId: string;
  /** Alias for videoId */
  id?: string;
  title: string;
  artist: string;
  album?: string;
  duration?: number;
  isrc?: string;
  spotifyId?: string;
  mbid?: string;
  language?: string;
  source?: string;
  syncedType: SyncedType;
  /** Whether track contains word-level synchronization */
  hasWordSync?: boolean;
  rawTtml?: string;
  rawLrc?: string;
  lines: ZukeLyricLine[];
}

export interface ZukeCatalogItem {
  videoId: string;
  title: string;
  artist: string;
  duration: number;
  language: string;
  syncedType: SyncedType;
  linesCount: number;
  path: string;
}

export interface ZukeStats {
  totalTracks: number;
  wordSynced: number;
  lineSynced: number;
  plain: number;
  instrumental: number;
  uniqueArtists: number;
  languages: Record<string, number>;
}
