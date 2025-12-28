import { motion } from 'framer-motion'
import { useState } from 'react'

export function MRDiagram() {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)

  const nodes = {
    G: { x: 100, y: 150, label: 'G', fullName: 'Genetic Variant', color: '#3B82F6' },
    X: { x: 300, y: 150, label: 'X', fullName: 'Exposure (e.g., BMI)', color: '#10B981' },
    Y: { x: 500, y: 150, label: 'Y', fullName: 'Outcome (e.g., T2D)', color: '#F59E0B' },
    U: { x: 400, y: 50, label: 'U', fullName: 'Confounders', color: '#EF4444' },
  }

  return (
    <div className="mr-diagram">
      <h3>The MR Triangle</h3>
      <svg viewBox="0 0 600 250" className="diagram-svg">
        {/* Arrows */}
        {/* G -> X (valid) */}
        <motion.path
          d="M 140 150 L 260 150"
          stroke="#3B82F6"
          strokeWidth="3"
          fill="none"
          markerEnd="url(#arrowhead-blue)"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        />

        {/* X -> Y (causal effect) */}
        <motion.path
          d="M 340 150 L 460 150"
          stroke="#10B981"
          strokeWidth="3"
          fill="none"
          markerEnd="url(#arrowhead-green)"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        />

        {/* G -> Y (should not exist - exclusion) */}
        <motion.path
          d="M 130 120 Q 300 20 470 120"
          stroke="#EF4444"
          strokeWidth="2"
          strokeDasharray="8,4"
          fill="none"
          markerEnd="url(#arrowhead-red)"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        />

        {/* Cross out the invalid path */}
        <motion.line
          x1="290" y1="60" x2="310" y2="80"
          stroke="#EF4444"
          strokeWidth="3"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.0 }}
        />
        <motion.line
          x1="310" y1="60" x2="290" y2="80"
          stroke="#EF4444"
          strokeWidth="3"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 1.0 }}
        />

        {/* U -> X and U -> Y (confounders) */}
        <motion.path
          d="M 380 70 L 320 130"
          stroke="#9CA3AF"
          strokeWidth="2"
          strokeDasharray="4,4"
          fill="none"
          markerEnd="url(#arrowhead-gray)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ duration: 0.5, delay: 0.8 }}
        />
        <motion.path
          d="M 420 70 L 480 130"
          stroke="#9CA3AF"
          strokeWidth="2"
          strokeDasharray="4,4"
          fill="none"
          markerEnd="url(#arrowhead-gray)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ duration: 0.5, delay: 0.9 }}
        />

        {/* Arrowhead definitions */}
        <defs>
          <marker id="arrowhead-blue" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6" />
          </marker>
          <marker id="arrowhead-green" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#10B981" />
          </marker>
          <marker id="arrowhead-red" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#EF4444" />
          </marker>
          <marker id="arrowhead-gray" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#9CA3AF" />
          </marker>
        </defs>

        {/* Nodes */}
        {Object.entries(nodes).map(([key, node]) => (
          <g key={key}>
            <motion.circle
              cx={node.x}
              cy={node.y}
              r="30"
              fill={node.color}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.4, delay: key === 'U' ? 0.7 : 0.1 }}
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHoveredNode(key)}
              onMouseLeave={() => setHoveredNode(null)}
            />
            <text
              x={node.x}
              y={node.y + 6}
              textAnchor="middle"
              fill="white"
              fontSize="20"
              fontWeight="bold"
            >
              {node.label}
            </text>
            <text
              x={node.x}
              y={node.y + 55}
              textAnchor="middle"
              fill="#4B5563"
              fontSize="12"
            >
              {node.fullName}
            </text>
          </g>
        ))}
      </svg>

      {hoveredNode && (
        <motion.div
          className="diagram-tooltip"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {hoveredNode === 'G' && 'Genetic variants (SNPs) that affect the exposure'}
          {hoveredNode === 'X' && 'The exposure we want to test (e.g., BMI, blood pressure)'}
          {hoveredNode === 'Y' && 'The outcome of interest (e.g., disease risk)'}
          {hoveredNode === 'U' && 'Unmeasured confounders that affect both X and Y'}
        </motion.div>
      )}

      <div className="diagram-legend">
        <span className="legend-item">
          <span className="legend-line solid blue"></span>
          Valid causal path
        </span>
        <span className="legend-item">
          <span className="legend-line dashed red"></span>
          Must not exist (exclusion restriction)
        </span>
        <span className="legend-item">
          <span className="legend-line dashed gray"></span>
          Confounding (blocked by MR)
        </span>
      </div>
    </div>
  )
}
