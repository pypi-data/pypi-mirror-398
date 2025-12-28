import { useState, useMemo } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts'
import * as Slider from '@radix-ui/react-slider'
import { RefreshCw } from 'lucide-react'

// Generate synthetic MR data
function generateData(nSnps: number, trueBeta: number, pleiotropy: number, seed: number) {
  const rng = mulberry32(seed)

  return Array.from({ length: nSnps }, (_, i) => {
    const betaExp = 0.05 + rng() * 0.15  // SNP-exposure effect
    const seExp = 0.01 + rng() * 0.02

    // Add pleiotropy to some SNPs
    const pleiotropicEffect = rng() < 0.2 ? (rng() - 0.5) * pleiotropy : 0
    const betaOut = trueBeta * betaExp + pleiotropicEffect + (rng() - 0.5) * 0.02
    const seOut = 0.015 + rng() * 0.025

    return {
      snp: `rs${1000000 + i}`,
      betaExp,
      seExp,
      betaOut,
      seOut,
      waldRatio: betaOut / betaExp,
      waldSe: Math.abs(seOut / betaExp),
      isOutlier: Math.abs(pleiotropicEffect) > 0.01,
    }
  })
}

// Simple seeded RNG
function mulberry32(a: number) {
  return function() {
    let t = a += 0x6D2B79F5
    t = Math.imul(t ^ t >>> 15, t | 1)
    t ^= t + Math.imul(t ^ t >>> 7, t | 61)
    return ((t ^ t >>> 14) >>> 0) / 4294967296
  }
}

// IVW estimator
function ivw(data: ReturnType<typeof generateData>) {
  const weights = data.map(d => 1 / (d.waldSe ** 2))
  const weightedSum = data.reduce((sum, d, i) => sum + d.waldRatio * weights[i], 0)
  const totalWeight = weights.reduce((a, b) => a + b, 0)
  const beta = weightedSum / totalWeight
  const se = Math.sqrt(1 / totalWeight)
  return { beta, se, method: 'IVW' }
}

// Weighted median estimator
function weightedMedian(data: ReturnType<typeof generateData>) {
  const weights = data.map(d => 1 / (d.waldSe ** 2))
  const totalWeight = weights.reduce((a, b) => a + b, 0)
  const normalizedWeights = weights.map(w => w / totalWeight)

  const sorted = data.map((d, i) => ({ ratio: d.waldRatio, weight: normalizedWeights[i] }))
    .sort((a, b) => a.ratio - b.ratio)

  let cumWeight = 0
  for (const item of sorted) {
    cumWeight += item.weight
    if (cumWeight >= 0.5) {
      return { beta: item.ratio, se: 0.05, method: 'Weighted Median' }
    }
  }
  return { beta: sorted[sorted.length - 1].ratio, se: 0.05, method: 'Weighted Median' }
}

// MR-Egger estimator
function mrEgger(data: ReturnType<typeof generateData>) {
  const n = data.length
  const weights = data.map(d => 1 / (d.seOut ** 2))

  const sumW = weights.reduce((a, b) => a + b, 0)
  const sumWX = data.reduce((sum, d, i) => sum + weights[i] * d.betaExp, 0)
  const sumWY = data.reduce((sum, d, i) => sum + weights[i] * d.betaOut, 0)
  const sumWXX = data.reduce((sum, d, i) => sum + weights[i] * d.betaExp ** 2, 0)
  const sumWXY = data.reduce((sum, d, i) => sum + weights[i] * d.betaExp * d.betaOut, 0)

  const denom = sumW * sumWXX - sumWX ** 2
  const beta = (sumW * sumWXY - sumWX * sumWY) / denom
  const intercept = (sumWXX * sumWY - sumWX * sumWXY) / denom

  const residuals = data.map((d, i) => weights[i] * (d.betaOut - intercept - beta * d.betaExp) ** 2)
  const mse = residuals.reduce((a, b) => a + b, 0) / (n - 2)
  const se = Math.sqrt(mse * sumW / denom)

  return { beta, se, intercept, method: 'MR-Egger' }
}

export function InteractiveDemo() {
  const [trueBeta, setTrueBeta] = useState(0.5)
  const [pleiotropy, setPleiotropy] = useState(0.1)
  const [nSnps, setNSnps] = useState(20)
  const [seed, setSeed] = useState(42)

  const data = useMemo(() => generateData(nSnps, trueBeta, pleiotropy, seed), [nSnps, trueBeta, pleiotropy, seed])

  const results = useMemo(() => ({
    ivw: ivw(data),
    median: weightedMedian(data),
    egger: mrEgger(data),
  }), [data])

  const scatterData = data.map(d => ({
    x: d.betaExp,
    y: d.betaOut,
    snp: d.snp,
    isOutlier: d.isOutlier,
  }))

  return (
    <section className="section">
      <h2>Interactive MR Demo</h2>
      <p className="intro">
        <strong>Where do these numbers come from?</strong> Each dot is a SNP. The x-axis shows β<sub>exposure</sub>{' '}
        (from a GWAS regressing the exposure on that SNP), and the y-axis shows β<sub>outcome</sub>{' '}
        (from a GWAS regressing the outcome on that SNP).
      </p>
      <p className="intro">
        <strong>Two-sample MR:</strong> These betas typically come from <em>different studies</em> — one
        GWAS for the exposure, another for the outcome. This avoids bias from using the same sample twice,
        and lets us combine published summary statistics without needing individual-level data.
      </p>
      <p className="intro">
        <strong>Why not individual-level?</strong> One-sample MR (same individuals, full data) has more
        power, but individual-level genetic data is rarely shared. Two-sample MR works with publicly
        available GWAS summaries, enabling analyses across thousands of traits.
      </p>
      <p className="intro">
        <strong>The causal effect:</strong> If the exposure truly causes the outcome, these points fall
        along a line through the origin — the slope is the causal effect (β<sub>outcome</sub>/β<sub>exposure</sub>).
        Red dots are pleiotropic outliers. Try increasing pleiotropy to see how methods differ.
      </p>

      <div className="demo-layout">
        <div className="controls">
          <div className="control-group">
            <label>
              True Causal Effect (β): <strong>{trueBeta.toFixed(2)}</strong>
            </label>
            <Slider.Root
              className="slider-root"
              value={[trueBeta]}
              onValueChange={([v]) => setTrueBeta(v)}
              min={0}
              max={1}
              step={0.05}
            >
              <Slider.Track className="slider-track">
                <Slider.Range className="slider-range" />
              </Slider.Track>
              <Slider.Thumb className="slider-thumb" />
            </Slider.Root>
          </div>

          <div className="control-group">
            <label>
              Pleiotropy Level: <strong>{pleiotropy.toFixed(2)}</strong>
            </label>
            <Slider.Root
              className="slider-root"
              value={[pleiotropy]}
              onValueChange={([v]) => setPleiotropy(v)}
              min={0}
              max={0.5}
              step={0.05}
            >
              <Slider.Track className="slider-track">
                <Slider.Range className="slider-range" />
              </Slider.Track>
              <Slider.Thumb className="slider-thumb" />
            </Slider.Root>
          </div>

          <div className="control-group">
            <label>
              Number of SNPs: <strong>{nSnps}</strong>
            </label>
            <Slider.Root
              className="slider-root"
              value={[nSnps]}
              onValueChange={([v]) => setNSnps(v)}
              min={5}
              max={50}
              step={5}
            >
              <Slider.Track className="slider-track">
                <Slider.Range className="slider-range" />
              </Slider.Track>
              <Slider.Thumb className="slider-thumb" />
            </Slider.Root>
          </div>

          <button className="regenerate-btn" onClick={() => setSeed(s => s + 1)}>
            <RefreshCw size={16} />
            Regenerate Data
          </button>
        </div>

        <div className="chart-container">
          <h4>SNP Effects: Exposure vs Outcome</h4>
          <ResponsiveContainer width="100%" height={340}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 60, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                name="Exposure Effect"
                type="number"
                label={{ value: 'β Exposure', position: 'bottom', offset: 0 }}
              />
              <YAxis
                dataKey="y"
                name="Outcome Effect"
                label={{ value: 'β Outcome', angle: -90, position: 'left' }}
              />
              <Tooltip
                formatter={(value) => typeof value === 'number' ? value.toFixed(4) : value}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.snp || ''}
              />
              <Legend verticalAlign="bottom" wrapperStyle={{ paddingTop: 20 }} />

              {/* IVW line */}
              <ReferenceLine
                segment={[{ x: 0, y: 0 }, { x: 0.2, y: 0.2 * results.ivw.beta }]}
                stroke="#3B82F6"
                strokeWidth={2}
              />

              {/* Egger line */}
              <ReferenceLine
                segment={[
                  { x: 0, y: results.egger.intercept || 0 },
                  { x: 0.2, y: (results.egger.intercept || 0) + 0.2 * results.egger.beta }
                ]}
                stroke="#10B981"
                strokeWidth={2}
                strokeDasharray="5,5"
              />

              {/* True effect line */}
              <ReferenceLine
                segment={[{ x: 0, y: 0 }, { x: 0.2, y: 0.2 * trueBeta }]}
                stroke="#9CA3AF"
                strokeWidth={1}
                strokeDasharray="3,3"
              />

              <Scatter
                name="SNPs"
                data={scatterData.filter(d => !d.isOutlier)}
                fill="#3B82F6"
              />
              <Scatter
                name="Outliers"
                data={scatterData.filter(d => d.isOutlier)}
                fill="#EF4444"
              />
            </ScatterChart>
          </ResponsiveContainer>
          <div className="line-legend">
            <span className="line-legend-item">
              <span className="line-sample solid blue"></span>
              IVW estimate
            </span>
            <span className="line-legend-item">
              <span className="line-sample dashed green"></span>
              MR-Egger estimate
            </span>
            <span className="line-legend-item">
              <span className="line-sample dashed gray"></span>
              True effect
            </span>
          </div>
        </div>

        <div className="results-table">
          <h4>Method Comparison</h4>
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Estimate</th>
                <th>SE</th>
                <th>Bias</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>True Effect</td>
                <td><strong>{trueBeta.toFixed(3)}</strong></td>
                <td>-</td>
                <td>-</td>
              </tr>
              <tr className={Math.abs(results.ivw.beta - trueBeta) < 0.1 ? 'good' : 'bad'}>
                <td>IVW</td>
                <td>{results.ivw.beta.toFixed(3)}</td>
                <td>{results.ivw.se.toFixed(3)}</td>
                <td>{(results.ivw.beta - trueBeta).toFixed(3)}</td>
              </tr>
              <tr className={Math.abs(results.median.beta - trueBeta) < 0.1 ? 'good' : 'bad'}>
                <td>Weighted Median</td>
                <td>{results.median.beta.toFixed(3)}</td>
                <td>{results.median.se.toFixed(3)}</td>
                <td>{(results.median.beta - trueBeta).toFixed(3)}</td>
              </tr>
              <tr className={Math.abs(results.egger.beta - trueBeta) < 0.1 ? 'good' : 'bad'}>
                <td>MR-Egger</td>
                <td>{results.egger.beta.toFixed(3)}</td>
                <td>{results.egger.se.toFixed(3)}</td>
                <td>{(results.egger.beta - trueBeta).toFixed(3)}</td>
              </tr>
            </tbody>
          </table>
          <p className="table-note">
            Increase pleiotropy to see how robust methods (Median, Egger) handle bias better than IVW.
          </p>
        </div>
      </div>
    </section>
  )
}
