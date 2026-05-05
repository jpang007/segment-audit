/**
 * Visual Renderer for Enhanced Audit Output (v2)
 * Renders account_brief + sa_action_plan beautifully
 */

class AuditVisualRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    render(data) {
        if (!data.account_brief && !data.sa_action_plan) {
            // Fallback to old format
            return null;
        }

        const html = `
            ${this.renderAccountBrief(data.account_brief)}
            ${this.renderSAActionPlan(data.sa_action_plan)}
        `;

        this.container.innerHTML = html;
        this.attachEventListeners();
    }

    renderAccountBrief(brief) {
        if (!brief) return '';

        const assessment = brief.workspace_health_assessment || {};
        const toneColors = {
            'Strong': '#10b981',
            'Mixed': '#f59e0b',
            'Needs Attention': '#ef4444'
        };
        const toneColor = toneColors[assessment.overall_tone] || '#6b7280';

        return `
            <div class="account-brief-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #1f2937;">🎯 Account Brief</h2>
                    <button onclick="copyAccountBrief()" class="btn-copy" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600;">
                        📋 Copy for Customer
                    </button>
                </div>

                <!-- Health Assessment -->
                <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid ${toneColor};">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <span style="background: ${toneColor}; color: white; padding: 6px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 600;">
                            ${assessment.overall_tone || 'Mixed'}
                        </span>
                        <span style="font-size: 1.1rem; color: #1f2937; font-weight: 600;">Workspace Health</span>
                    </div>
                    <p style="margin: 0; color: #374151; line-height: 1.6;">${assessment.health_reasoning || ''}</p>
                </div>

                <!-- Key Strengths & Concerns -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <h3 style="font-size: 0.875rem; text-transform: uppercase; color: #10b981; margin-bottom: 12px; letter-spacing: 0.5px;">✅ Key Strengths</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.8;">
                            ${(assessment.key_strengths || []).map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <h3 style="font-size: 0.875rem; text-transform: uppercase; color: #ef4444; margin-bottom: 12px; letter-spacing: 0.5px;">⚠️ Key Concerns</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.8;">
                            ${(assessment.key_concerns || []).map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                </div>

                <!-- Critical Findings -->
                ${(brief.critical_findings && brief.critical_findings.length > 0) ? `
                    <div style="margin-bottom: 20px;">
                        <h3 style="font-size: 0.875rem; text-transform: uppercase; color: #6b7280; margin-bottom: 12px; letter-spacing: 0.5px;">🚨 Critical Findings</h3>
                        ${brief.critical_findings.map(f => `
                            <div style="background: #fef2f2; border-left: 3px solid #ef4444; padding: 16px; border-radius: 6px; margin-bottom: 12px;">
                                <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 8px;">
                                    <strong style="color: #991b1b;">${f.finding}</strong>
                                    <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-left: 8px;">
                                        ${f.confidence}
                                    </span>
                                </div>
                                <div style="color: #7f1d1d; font-size: 0.875rem; margin-bottom: 8px;">${f.why_it_matters}</div>
                                <div style="color: #991b1b; font-weight: 600; font-size: 0.875rem;">→ ${f.recommended_action}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                <!-- Activation Opportunities -->
                ${(brief.activation_opportunities && brief.activation_opportunities.length > 0) ? `
                    <div style="margin-bottom: 20px;">
                        <h3 style="font-size: 0.875rem; text-transform: uppercase; color: #6b7280; margin-bottom: 12px; letter-spacing: 0.5px;">🚀 Activation Opportunities</h3>
                        ${brief.activation_opportunities.map(o => `
                            <div style="background: #f0fdf4; border-left: 3px solid #10b981; padding: 16px; border-radius: 6px; margin-bottom: 12px;">
                                <strong style="color: #065f46;">${o.opportunity}</strong>
                                <div style="color: #047857; font-size: 0.875rem; margin-top: 6px;">Reach: ${o.potential_reach}</div>
                                <div style="color: #059669; font-size: 0.875rem;">Effort: ${o.effort}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                <!-- Data Gaps -->
                ${(brief.data_gaps_affecting_analysis && brief.data_gaps_affecting_analysis.length > 0) ? `
                    <div style="background: #fffbeb; border-left: 3px solid #f59e0b; padding: 16px; border-radius: 6px;">
                        <strong style="color: #92400e;">ℹ️ Data Limitations</strong>
                        <ul style="margin: 8px 0 0 20px; color: #78350f; font-size: 0.875rem;">
                            ${brief.data_gaps_affecting_analysis.map(g => `<li>${g}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderSAActionPlan(plan) {
        if (!plan || !plan.findings) return '';

        const summary = plan.summary || {};
        const metadata = plan.audit_metadata || {};

        return `
            <div class="sa-action-plan-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #1f2937;">📋 SA Action Plan</h2>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <select id="priorityFilter" onchange="filterFindings()" style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 6px;">
                            <option value="all">All Priorities</option>
                            <option value="P0">P0 Only</option>
                            <option value="P1">P1 Only</option>
                            <option value="P2">P2 Only</option>
                        </select>
                        <button onclick="exportJSON()" class="btn-export" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600;">
                            💾 Export JSON
                        </button>
                    </div>
                </div>

                <!-- Summary Stats -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                    <div style="background: #fef2f2; padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #991b1b;">${summary.by_priority?.P0 || 0}</div>
                        <div style="font-size: 0.875rem; color: #7f1d1d;">P0 Findings</div>
                    </div>
                    <div style="background: #fef3c7; padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #92400e;">${summary.by_priority?.P1 || 0}</div>
                        <div style="font-size: 0.875rem; color: #78350f;">P1 Findings</div>
                    </div>
                    <div style="background: #fef9c3; padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #854d0e;">${summary.by_priority?.P2 || 0}</div>
                        <div style="font-size: 0.875rem; color: #713f12;">P2 Findings</div>
                    </div>
                    <div style="background: #eff6ff; padding: 16px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #1e40af;">${summary.by_confidence?.High || 0}</div>
                        <div style="font-size: 0.875rem; color: #1e3a8a;">High Confidence</div>
                    </div>
                </div>

                <!-- Findings List -->
                <div id="findingsList">
                    ${plan.findings.map((finding, idx) => this.renderFinding(finding, idx)).join('')}
                </div>
            </div>
        `;
    }

    renderFinding(finding, idx) {
        const priorityColors = {
            'P0': { bg: '#fef2f2', border: '#ef4444', text: '#991b1b', badge: '#fee2e2' },
            'P1': { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', badge: '#fef3c7' },
            'P2': { bg: '#fef9c3', border: '#eab308', text: '#854d0e', badge: '#fef08a' }
        };
        const colors = priorityColors[finding.priority] || priorityColors['P2'];

        const confidenceIcons = {
            'High': '⚡',
            'Medium': '⚠️',
            'Low': 'ℹ️'
        };

        return `
            <div class="finding-card" data-priority="${finding.priority}" style="background: ${colors.bg}; border-left: 4px solid ${colors.border}; padding: 20px; border-radius: 8px; margin-bottom: 16px;">
                <!-- Finding Header -->
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px; cursor: pointer;" onclick="toggleFindingExpand(${idx})">
                    <div style="flex: 1;">
                        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                            <span style="background: ${colors.badge}; color: ${colors.text}; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                                ${finding.priority}
                            </span>
                            <span style="color: ${colors.text}; font-size: 0.875rem; font-weight: 600;">
                                ${finding.category}
                            </span>
                            <span style="font-size: 1rem;">${confidenceIcons[finding.confidence] || ''}</span>
                            <span style="color: #6b7280; font-size: 0.75rem;">${finding.confidence}</span>
                        </div>
                        <h3 style="margin: 0; color: ${colors.text}; font-size: 1.1rem;">${finding.finding_fact}</h3>
                    </div>
                    <button id="expandBtn${idx}" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: ${colors.text}; padding: 0 8px;">▼</button>
                </div>

                <!-- Finding Body (Collapsible) -->
                <div id="findingBody${idx}" style="display: none;">
                    <!-- Evidence -->
                    ${finding.evidence && finding.evidence.length > 0 ? `
                        <div style="margin-bottom: 16px;">
                            <div style="font-weight: 600; color: ${colors.text}; margin-bottom: 8px; font-size: 0.875rem; text-transform: uppercase;">📊 Evidence</div>
                            <ul style="margin: 0; padding-left: 20px; color: #374151;">
                                ${finding.evidence.map(e => `<li style="margin-bottom: 4px;">${e}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    <!-- Interpretation -->
                    ${finding.interpretation ? `
                        <div style="background: white; padding: 16px; border-radius: 6px; margin-bottom: 16px;">
                            <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px; font-size: 0.875rem;">💡 Interpretation</div>
                            <div style="color: #374151; margin-bottom: 8px;"><strong>Likely:</strong> ${finding.interpretation.likely_implication}</div>
                            ${finding.interpretation.alternative_explanations && finding.interpretation.alternative_explanations.length > 0 ? `
                                <div style="color: #6b7280; font-size: 0.875rem;">
                                    <strong>Could also be:</strong>
                                    <ul style="margin: 4px 0 0 20px;">
                                        ${finding.interpretation.alternative_explanations.map(alt => `<li>${alt}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}

                    <!-- Why It Matters -->
                    ${finding.why_it_matters ? `
                        <div style="background: white; padding: 16px; border-radius: 6px; margin-bottom: 16px;">
                            <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px; font-size: 0.875rem;">⚠️ Why It Matters</div>
                            <div style="color: #374151; font-size: 0.875rem;">
                                <div style="margin-bottom: 6px;"><strong>Business:</strong> ${finding.why_it_matters.business_impact}</div>
                                <div style="margin-bottom: 6px;"><strong>Technical:</strong> ${finding.why_it_matters.technical_impact}</div>
                                <div><strong>Urgency:</strong> ${finding.why_it_matters.urgency}</div>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Validation Steps -->
                    ${finding.validation_steps && finding.validation_steps.length > 0 ? `
                        <div style="background: #eff6ff; padding: 16px; border-radius: 6px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <div style="font-weight: 600; color: #1e40af; font-size: 0.875rem;">✅ Validation Steps</div>
                                <button onclick="copyText(${JSON.stringify(finding.validation_steps).replace(/"/g, '&quot;')})" style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Copy</button>
                            </div>
                            <ol style="margin: 0; padding-left: 20px; color: #1e40af;">
                                ${finding.validation_steps.map(step => `<li style="margin-bottom: 6px;">${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}

                    <!-- Implementation Steps -->
                    ${finding.implementation_steps && finding.implementation_steps.length > 0 ? `
                        <div style="background: #f0fdf4; padding: 16px; border-radius: 6px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <div style="font-weight: 600; color: #065f46; font-size: 0.875rem;">🔧 Implementation Steps</div>
                                <button onclick="copyText(${JSON.stringify(finding.implementation_steps).replace(/"/g, '&quot;')})" style="background: #10b981; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Copy</button>
                            </div>
                            <ol style="margin: 0; padding-left: 20px; color: #065f46;">
                                ${finding.implementation_steps.map(step => `<li style="margin-bottom: 6px;">${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}

                    <!-- Customer-Safe Wording -->
                    ${finding.customer_safe_wording ? `
                        <div style="background: #fef3c7; padding: 16px; border-radius: 6px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <div style="font-weight: 600; color: #92400e; font-size: 0.875rem;">💬 Customer-Safe Wording</div>
                                <button onclick="copyText('${finding.customer_safe_wording.replace(/'/g, "\\'")}')" style="background: #f59e0b; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Copy</button>
                            </div>
                            <div style="color: #78350f; font-size: 0.875rem; font-style: italic;">"${finding.customer_safe_wording}"</div>
                        </div>
                    ` : ''}

                    <!-- Ownership & Effort -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        ${finding.ownership ? `
                            <div style="background: white; padding: 12px; border-radius: 6px;">
                                <div style="font-weight: 600; color: #1f2937; margin-bottom: 6px; font-size: 0.75rem;">👥 Ownership</div>
                                <div style="font-size: 0.75rem; color: #374151;">
                                    <div style="margin-bottom: 4px;"><strong>SA:</strong> ${finding.ownership.sa_owner}</div>
                                    <div style="margin-bottom: 4px;"><strong>Customer:</strong> ${finding.ownership.customer_owner}</div>
                                    <div style="color: #6b7280;"><strong>Escalate:</strong> ${finding.ownership.escalation_path}</div>
                                </div>
                            </div>
                        ` : ''}
                        ${finding.effort_estimate ? `
                            <div style="background: white; padding: 12px; border-radius: 6px;">
                                <div style="font-weight: 600; color: #1f2937; margin-bottom: 6px; font-size: 0.75rem;">⏱️ Effort Estimate</div>
                                <div style="font-size: 0.75rem; color: #374151;">
                                    <div style="margin-bottom: 4px;"><strong>Validation:</strong> ${finding.effort_estimate.validation_effort} (${finding.effort_estimate.validation_time_range || 'TBD'})</div>
                                    <div><strong>Implementation:</strong> ${finding.effort_estimate.implementation_effort}</div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Event listeners are attached via onclick in HTML for simplicity
    }
}

// Global functions for onclick handlers
function toggleFindingExpand(idx) {
    const body = document.getElementById(`findingBody${idx}`);
    const btn = document.getElementById(`expandBtn${idx}`);
    if (body.style.display === 'none') {
        body.style.display = 'block';
        btn.textContent = '▲';
    } else {
        body.style.display = 'none';
        btn.textContent = '▼';
    }
}

function copyText(text) {
    const textArray = Array.isArray(text) ? text.join('\n') : text;
    navigator.clipboard.writeText(textArray).then(() => {
        alert('✓ Copied to clipboard!');
    });
}

function copyAccountBrief() {
    // Will implement
    alert('Account Brief copy feature coming soon!');
}

function filterFindings() {
    const priority = document.getElementById('priorityFilter').value;
    const cards = document.querySelectorAll('.finding-card');
    cards.forEach(card => {
        if (priority === 'all' || card.dataset.priority === priority) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function exportJSON() {
    if (window.lastGeneratedResult) {
        const blob = new Blob([JSON.stringify(window.lastGeneratedResult, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `audit_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }
}
