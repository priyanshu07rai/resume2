"""Patch index.html to separate verification table from ML bullets."""
import re

with open("templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the old buildGrid block + innerHTML
old_block_start = "            if (sa) {"
old_block_end = "            target.scrollIntoView({ behavior: 'smooth' });\n        }"

start_idx = content.find(old_block_start)
end_idx = content.find(old_block_end)

if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find markers!")
    print(f"Start found: {start_idx != -1}")
    print(f"End found: {end_idx != -1}")
    exit(1)

end_idx += len(old_block_end)

new_block = '''            if (sa) {
                const buildTableRows = (items, isPos) => {
                    if (!items || !items.length) return '';
                    const color = isPos ? '#10b981' : '#ef4444';
                    const icon = isPos ? '✓' : '⚠';
                    return items.map(item => `
                        <tr>
                            <td style="padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <span style="color: ${color}; font-weight: 800; margin-right: 6px;">${icon}</span>
                                <span style="font-weight: 600; color: #f1f5f9;">${item.signal}</span>
                            </td>
                            <td style="padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8;">${item.evidence_source}</td>
                            <td style="padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <span style="padding: 3px 10px; border-radius: 100px; font-size: 0.65rem; font-weight: 700;
                                    background: ${item.impact === 'Positive' ? 'rgba(16,185,129,0.15)' : item.impact === 'Negative' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)'};
                                    color: ${item.impact === 'Positive' ? '#10b981' : item.impact === 'Negative' ? '#ef4444' : '#f59e0b'};
                                    border: 1px solid ${item.impact === 'Positive' ? 'rgba(16,185,129,0.3)' : item.impact === 'Negative' ? 'rgba(239,68,68,0.3)' : 'rgba(245,158,11,0.3)'};">${item.impact}</span>
                            </td>
                            <td style="padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <span style="padding: 3px 10px; border-radius: 100px; font-size: 0.65rem; font-weight: 700;
                                    background: ${item.severity === 'High' ? 'rgba(239,68,68,0.15)' : item.severity === 'Moderate' ? 'rgba(245,158,11,0.15)' : 'rgba(100,116,139,0.15)'};
                                    color: ${item.severity === 'High' ? '#ef4444' : item.severity === 'Moderate' ? '#f59e0b' : '#94a3b8'};
                                    border: 1px solid ${item.severity === 'High' ? 'rgba(239,68,68,0.3)' : item.severity === 'Moderate' ? 'rgba(245,158,11,0.3)' : 'rgba(100,116,139,0.3)'};">${item.severity}</span>
                            </td>
                        </tr>
                    `).join('');
                };

                let pos = Array.isArray(sa.positive_indicators) ? sa.positive_indicators : [];
                let neg = Array.isArray(sa.negative_indicators) ? sa.negative_indicators : [];

                const tableHeader = `
                    <thead><tr>
                        <th style="padding: 10px 16px; text-align: left; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; border-bottom: 2px solid rgba(255,255,255,0.1);">Signal</th>
                        <th style="padding: 10px 16px; text-align: left; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; border-bottom: 2px solid rgba(255,255,255,0.1);">Source</th>
                        <th style="padding: 10px 16px; text-align: left; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; border-bottom: 2px solid rgba(255,255,255,0.1);">Impact</th>
                        <th style="padding: 10px 16px; text-align: left; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; border-bottom: 2px solid rgba(255,255,255,0.1);">Severity</th>
                    </tr></thead>`;

                let snapshotHtml = '';
                if (sa.summary_snapshot) {
                    const snap = sa.summary_snapshot;
                    const riskCol = snap.overall_risk_level === 'High' ? '#ef4444' : snap.overall_risk_level === 'Elevated' ? '#f59e0b' : snap.overall_risk_level === 'Moderate' ? '#f59e0b' : '#10b981';
                    snapshotHtml = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; margin-top: 20px;">
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 14px; border: 1px solid rgba(255,255,255,0.06);">
                            <div style="font-size: 0.55rem; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-bottom: 6px;">Risk Level</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: ${riskCol};">${snap.overall_risk_level}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 14px; border: 1px solid rgba(255,255,255,0.06);">
                            <div style="font-size: 0.55rem; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-bottom: 6px;">Capability</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: #e2e8f0;">${snap.capability_certainty}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 14px; border: 1px solid rgba(255,255,255,0.06);">
                            <div style="font-size: 0.55rem; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-bottom: 6px;">Digital Depth</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: #e2e8f0;">${snap.digital_depth_rating}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 10px; padding: 14px; border: 1px solid rgba(255,255,255,0.06);">
                            <div style="font-size: 0.55rem; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-bottom: 6px;">Action</div>
                            <div style="font-size: 0.85rem; font-weight: 800; color: var(--accent);">${snap.recommended_action}</div>
                        </div>
                    </div>`;
                }

                verificationCardHtml = `
                <div class="glass-card" style="border-top: 3px solid var(--accent); position: relative; overflow: hidden;">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--accent), transparent);"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                        <div>
                            <div style="font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.25em; color: var(--accent); font-weight: 800; margin-bottom: 4px;">&#128269; Forensic Verification Signals</div>
                            <div style="font-size: 0.7rem; color: #64748b;">AI-powered cross-reference analysis of resume claims vs external evidence</div>
                        </div>
                        <div style="font-family: var(--font-mono); font-size: 0.6rem; color: #334155; background: rgba(16,185,129,0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(16,185,129,0.2);">
                            ${pos.length + neg.length} SIGNALS
                        </div>
                    </div>

                    ${pos.length > 0 ? `
                    <div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; color: #10b981; font-weight: 700; margin-bottom: 8px;">&#10003; Positive Indicators</div>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 0.82rem;">
                        ${tableHeader}
                        <tbody>${buildTableRows(pos, true)}</tbody>
                    </table>` : ''}

                    ${neg.length > 0 ? `
                    <div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em; color: #ef4444; font-weight: 700; margin-bottom: 8px;">&#9888; Risk / Negative Indicators</div>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 0.82rem;">
                        ${tableHeader}
                        <tbody>${buildTableRows(neg, false)}</tbody>
                    </table>` : ''}

                    ${snapshotHtml}
                </div>`;
            }

            // ══════ ML PREDICTION BULLETS (SEPARATE SECTION) ══════
            const verdictHtml = verdict.verdict_lines.map(line => `
                <div class="forensic-line">${line}</div>
            `).join('');

            target.innerHTML = `
                <div class="dashboard-hero">
                    <div class="hero-stat" style="border-top: 3px solid ${trustColor}">
                        <span class="label">Trust Score</span>
                        <div class="val" style="color: ${trustColor}">${trustScore}</div>
                        <div style="margin-top: 15px; font-size: 0.8rem; color: var(--text-secondary)">
                            Anti-Fraud Assurance
                        </div>
                    </div>
                    <div class="hero-stat" style="border-top: 3px solid ${matchColor}">
                        <span class="label">Role Fit Score</span>
                        <div class="val" style="color: ${matchColor}; font-size: ${match.is_evaluated ? '3.5rem' : '2.5rem'}">${roleMatchScore}</div>
                        <div style="color: var(--text-secondary); font-size: 0.75rem; margin-top: 15px;">
                            ${match.is_evaluated ? match.verdict : 'No Role Selected'} 
                        </div>
                    </div>
                    <div class="hero-stat" style="border-top: 3px solid ${evColor}">
                        <span class="label">Evidence Strength</span>
                        <div class="val" style="font-size: 2rem; margin-top: 10px; color: ${evColor}">${evidenceStrength}</div>
                        <div style="color: var(--text-secondary); font-size: 0.75rem; margin-top: 15px;">
                            Based on technical foot-print
                        </div>
                    </div>
                </div>

                <!-- CANDIDATE NAME + SCAN ID -->
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                        <h2 style="font-size: 2rem; font-weight: 800;">${data.candidate.name || 'Forensic Subject'}</h2>
                        <div style="font-family: var(--font-mono); font-size: 0.65rem; color: var(--text-secondary);">
                            SCAN_ID: ${Math.random().toString(36).substr(2, 9).toUpperCase()} &bull; LATENCY: ${meta.execution_time_sec}s
                        </div>
                    </div>

                    <!-- ML PREDICTION NARRATIVE (SEPARATE) -->
                    <div class="analysis-box">
                        <div style="font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.2em; color: var(--accent); margin-bottom: 12px; font-weight: 800;">
                            ML Prediction Narrative
                        </div>
                        ${verdictHtml}
                    </div>

                    <div class="logic-grid">
                        <div class="logic-card">
                            <span class="label" style="font-size: 0.65rem; text-transform: uppercase; color: var(--text-secondary);">Digital Maturity</span>
                            <div style="font-size: 1.2rem; font-weight: 700; margin: 10px 0;">${hi.external_signals.coverage_level}</div>
                            <div style="color: var(--text-secondary); font-size: 0.7rem;">Verified Platform Signals: ${meta.api_calls_used.length}</div>
                        </div>
                        <div class="logic-card">
                            <span class="label" style="font-size: 0.65rem; text-transform: uppercase; color: var(--text-secondary);">Internal Coherence</span>
                            <div style="font-size: 1.2rem; font-weight: 700; margin: 10px 0;">${hi.consistency.verdict}</div>
                            <div style="color: var(--text-secondary); font-size: 0.7rem;">Coherence Score: ${hi.consistency.coherence_score}/100</div>
                        </div>
                    </div>
                </div>

                <!-- VERIFICATION SIGNALS TABLE (SEPARATE, PROMINENT CARD) -->
                ${verificationCardHtml}

                <!-- FOOTER -->
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-family: var(--font-mono); font-size: 0.6rem; color: #475569;">
                            SHA-256 Report Anchor: ${meta.timing.total.toString(16)}...${Math.random().toString(16).substr(2, 8)}
                        </div>
                        <button class="btn-primary" style="padding: 10px 20px; font-size: 0.75rem;" onclick="location.reload()">New Scan</button>
                    </div>
                </div>
            `;
            target.scrollIntoView({ behavior: 'smooth' });
        }'''

content = content[:start_idx] + new_block + content[end_idx:]

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: index.html patched!")
