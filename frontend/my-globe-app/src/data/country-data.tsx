import generatedData from './generated-data.json';

export interface Paper {
  id: string;
  title: string;
  doi: string;
  year: number;
  cited_by_count: number;
}

export interface TopicTrend {
  year: number;
  topicName: string;
  volume: number;
}

export interface SubfieldData {
  name: string;
  totalWorks: number;
  score?: number; 
  topPapers?: Paper[];
}

export interface CountryStats {
  countryName: string;
  countryCode: string;
  topSubfields: SubfieldData[];
  uniqueSubfields: SubfieldData[];
  trends: Record<string, { year: number; volume: number }[]>;
}

const countryData: Record<string, CountryStats> = generatedData as unknown as Record<string, CountryStats>;

const countryFlags: Record<string, string> = {
  US: "🇺🇸", CN: "🇨🇳", IN: "🇮🇳", DE: "🇩🇪", JP: "🇯🇵",
  GB: "🇬🇧", FR: "🇫🇷", BR: "🇧🇷", IT: "🇮🇹", CA: "🇨🇦",
  RU: "🇷🇺", KR: "🇰🇷", AU: "🇦🇺", ES: "🇪🇸", MX: "🇲🇽",
  ID: "🇮🇩", TR: "🇹🇷", NL: "🇳🇱", SA: "🇸🇦", CH: "🇨🇭",
  SE: "🇸🇪", PL: "🇵🇱", BE: "🇧🇪", AR: "🇦🇷", NO: "🇳🇴",
};

export function getCountryData(countryCode: string): CountryStats | null {
  return countryData[countryCode] || null;
}

export function getCountryFlag(countryCode: string): string {
  return countryFlags[countryCode] || "🌍";
}
