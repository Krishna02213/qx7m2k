export type Metrics = {
  count: number
  maeMw?: number
  rmseMw?: number
  biasMw?: number
  wapePct?: number
  overforecastPct?: number
  p90ShortfallMw?: number
  maxShortfallMw?: number
  forecastEnergyGwh?: number
  actualEnergyGwh?: number
}

export type Interval = {
  startTime: string
  label: string
  forecastMw: number
  actualMw: number | null
  errorMw: number | null
  shortfallMw: number | null
  publishTime: string
}

export type DayResponse = {
  deliveryDate: string
  cutoff: string
  cutoffAt: string
  latestPublishTime: string | null
  publicationCount: number
  intervals: Interval[]
  metrics: Metrics
}

export type MonthResponse = {
  cutoff: string
  metrics: Metrics
  days: Array<{ date: string } & Metrics>
  worstIntervals: Interval[]
}

