import { useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertTriangle, ArrowDownRight, BarChart3, CalendarDays,
  CheckCircle2, Clock3, Gauge, Info, Leaf, RefreshCw, ShieldCheck, Wind,
} from 'lucide-react'
import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import type { DayResponse, MonthResponse } from './types'

const formatMw = (value?: number | null) => value == null ? '—' : `${Math.round(value).toLocaleString()} MW`
const formatDateTime = (value?: string | null) => value ? new Intl.DateTimeFormat('en-GB', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London', timeZoneName: 'short',
}).format(new Date(value)) : '—'

function Kpi({ icon, label, value, note, tone = 'default' }: {
  icon: React.ReactNode; label: string; value: string; note: string; tone?: 'default' | 'risk' | 'good'
}) {
  return <article className={`kpi ${tone}`}>
    <div className="kpi-top"><span className="icon-wrap">{icon}</span><span>{label}</span></div>
    <strong>{value}</strong><small>{note}</small>
  </article>
}

function App() {
  const [deliveryDate, setDeliveryDate] = useState('2026-01-15')
  const [cutoff, setCutoff] = useState('09:50')
  const [day, setDay] = useState<DayResponse | null>(null)
  const [month, setMonth] = useState<MonthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [staticMode, setStaticMode] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    Promise.all([
      fetch(`/api/forecast?delivery_date=${deliveryDate}&cutoff=${cutoff}`, { signal: controller.signal }).then(r => r.ok ? r.json() : Promise.reject(r)),
      fetch(`/api/performance?cutoff=${cutoff}`, { signal: controller.signal }).then(r => r.ok ? r.json() : Promise.reject(r)),
    ]).then(([daily, monthly]) => { setDay(daily); setMonth(monthly); setStaticMode(false) })
      .catch(async err => {
        if (err.name === 'AbortError') return
        try {
          const demo = await fetch('/demo-data.json', { signal: controller.signal }).then(r => r.json())
          setDay(demo.days[deliveryDate]); setMonth(demo.month); setStaticMode(true)
          setError(cutoff === demo.cutoff ? '' : `Static preview uses the ${demo.cutoff} cutoff. Use the API deployment for custom cutoffs.`)
        } catch {
          setError('Unable to load the Elexon analysis.')
        }
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [deliveryDate, cutoff])

  const chartData = useMemo(() => day?.intervals.map(row => ({
    ...row,
    riskLow: Math.max(0, row.forecastMw - (month?.metrics.p90ShortfallMw || 0)),
    riskHigh: row.forecastMw + (month?.metrics.p90ShortfallMw || 0),
  })) || [], [day, month])

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="#top" aria-label="WindSight home"><span className="brand-mark"><Wind size={23}/></span><span>Wind<span>Sight</span></span></a>
      <nav><a className="active" href="#decision">Decision view</a><a href="#performance">Performance</a><a href="#methodology">Methodology</a></nav>
      <div className="source-pill"><span></span>Elexon · January 2026{staticMode ? ' · snapshot' : ''}</div>
    </header>

    <main id="top">
      <section className="hero">
        <div>
          <p className="eyebrow"><Leaf size={15}/> GB DAY-AHEAD PROCUREMENT</p>
          <h1>Know the wind.<br/><em>Price the uncertainty.</em></h1>
          <p className="hero-copy">A point-in-time view of the wind forecast your trading desk actually had before gate closure—and the historical error behind it.</p>
        </div>
        <div className="hero-status">
          <div><CheckCircle2 size={17}/><span>Decision-safe snapshot</span></div>
          <strong>{formatDateTime(day?.latestPublishTime)}</strong>
          <small>Latest eligible forecast publication</small>
        </div>
      </section>

      <section id="decision" className="control-panel">
        <div className="control-heading"><CalendarDays size={20}/><div><strong>Recreate a day-ahead decision</strong><span>All times shown in Europe/London</span></div></div>
        <label><span>Delivery day</span><input type="date" min="2026-01-01" max="2026-01-31" value={deliveryDate} onChange={e => setDeliveryDate(e.target.value)}/></label>
        <label><span>Gate closure</span><input type="time" value={cutoff} onChange={e => setCutoff(e.target.value)}/></label>
        <div className="cutoff-readout"><Clock3 size={17}/><div><span>Information cutoff</span><strong>{formatDateTime(day?.cutoffAt)}</strong></div></div>
      </section>

      {error && <div className="error"><AlertTriangle size={18}/>{error}</div>}
      {loading && !day ? <div className="loading"><RefreshCw className="spin"/> Building decision snapshot…</div> : day && month && <>
        <section className="kpi-grid">
          <Kpi icon={<Wind/>} label="Forecast energy" value={`${day.metrics.forecastEnergyGwh?.toFixed(1)} GWh`} note="Day-ahead wind expectation"/>
          <Kpi icon={<Activity/>} label="Observed energy" value={`${day.metrics.actualEnergyGwh?.toFixed(1)} GWh`} note="FUELHH outturn" tone="good"/>
          <Kpi icon={<ArrowDownRight/>} label="Mean bias" value={formatMw(day.metrics.biasMw)} note={day.metrics.biasMw! > 0 ? 'Wind was overforecast' : 'Wind was underforecast'} tone={day.metrics.biasMw! > 0 ? 'risk' : 'good'}/>
          <Kpi icon={<ShieldCheck/>} label="P90 shortfall buffer" value={formatMw(month.metrics.p90ShortfallMw)} note="January downside benchmark" tone="risk"/>
        </section>

        <section className="panel chart-panel">
          <div className="panel-head"><div><p className="section-label">DELIVERY PROFILE</p><h2>Forecast vs. actual wind generation</h2></div><div className="legend"><span className="forecast">Forecast</span><span className="actual">Actual</span><span className="band">P90 band</span></div></div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 12, bottom: 0, left: 4 }}>
                <defs><linearGradient id="risk" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f4b740" stopOpacity={.2}/><stop offset="100%" stopColor="#f4b740" stopOpacity={.02}/></linearGradient></defs>
                <CartesianGrid strokeDasharray="4 6" stroke="#dce5e2" vertical={false}/>
                <XAxis dataKey="label" interval={2} tick={{fill:'#61706d',fontSize:12}} axisLine={false} tickLine={false}/>
                <YAxis tickFormatter={v => `${Math.round(v/1000)}k`} tick={{fill:'#61706d',fontSize:12}} axisLine={false} tickLine={false} width={42}/>
                <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} MW`]} labelFormatter={label => `${label} UTC`}/>
                <Area dataKey="riskHigh" stroke="none" fill="url(#risk)"/>
                <Area dataKey="riskLow" stroke="none" fill="#fff"/>
                <Line type="monotone" dataKey="forecastMw" stroke="#dd9d20" strokeWidth={2.5} dot={false}/>
                <Line type="monotone" dataKey="actualMw" stroke="#087f78" strokeWidth={3} dot={false}/>
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-note"><Info size={16}/><span>Forecast selection is frozen at <strong>{formatDateTime(day.cutoffAt)}</strong>. Later publications are excluded.</span></div>
        </section>

        <section id="performance" className="performance-grid">
          <div className="panel scorecard">
            <div className="panel-head"><div><p className="section-label">JANUARY SCORECARD</p><h2>Forecast performance at gate closure</h2></div><Gauge/></div>
            <div className="score-grid">
              <div><span>MAE</span><strong>{formatMw(month.metrics.maeMw)}</strong><small>Typical absolute miss</small></div>
              <div><span>RMSE</span><strong>{formatMw(month.metrics.rmseMw)}</strong><small>Penalises large misses</small></div>
              <div><span>WAPE</span><strong>{month.metrics.wapePct}%</strong><small>Volume-weighted error</small></div>
              <div><span>Overforecast rate</span><strong>{month.metrics.overforecastPct}%</strong><small>Intervals with downside risk</small></div>
            </div>
          </div>
          <div className="panel risk-card">
            <p className="section-label">TRADING SIGNAL</p><h2>Plan for wind shortfall</h2>
            <div className="risk-number"><span>Historical P90</span><strong>{formatMw(month.metrics.p90ShortfallMw)}</strong></div>
            <p>In 90% of January intervals, forecast-minus-actual wind shortfall was no greater than this level at the selected gate closure.</p>
            <div className="caution"><AlertTriangle size={17}/><span>Descriptive pilot statistic, not a guaranteed reserve recommendation.</span></div>
          </div>
        </section>

        <section className="panel table-panel">
          <div className="panel-head"><div><p className="section-label">INTERVAL DETAIL</p><h2>Hourly decision ledger</h2></div><BarChart3/></div>
          <div className="table-scroll"><table><thead><tr><th>Delivery</th><th>Forecast</th><th>Actual</th><th>Error</th><th>Shortfall</th><th>Forecast published</th></tr></thead>
          <tbody>{day.intervals.map(row => <tr key={row.startTime}><td>{row.label}</td><td>{formatMw(row.forecastMw)}</td><td>{formatMw(row.actualMw)}</td><td className={row.errorMw! > 0 ? 'bad-text' : 'good-text'}>{row.errorMw! > 0 ? '+' : ''}{formatMw(row.errorMw)}</td><td>{formatMw(row.shortfallMw)}</td><td>{formatDateTime(row.publishTime)}</td></tr>)}</tbody></table></div>
        </section>
      </>}

      <section id="methodology" className="methodology">
        <div><p className="section-label">METHODOLOGY</p><h2>Point-in-time by design</h2></div>
        <ol><li><span>01</span><div><strong>Freeze the clock</strong><p>Set the day-ahead gate closure on D−1.</p></div></li><li><span>02</span><div><strong>Select eligible forecasts</strong><p>Take the latest WINDFOR publication available before the cutoff.</p></div></li><li><span>03</span><div><strong>Align the outturn</strong><p>Average two FUELHH half-hours to match each hourly wind forecast.</p></div></li><li><span>04</span><div><strong>Quantify downside</strong><p>Measure overforecast wind as potential procurement shortfall.</p></div></li></ol>
      </section>
    </main>
    <footer><div className="brand"><span className="brand-mark"><Wind size={18}/></span><span>Wind<span>Sight</span></span></div><p>Pilot decision support · Elexon FUELHH + WINDFOR only</p><a href="https://bmrs.elexon.co.uk/api-documentation" target="_blank">Data methodology ↗</a></footer>
  </div>
}

export default App

