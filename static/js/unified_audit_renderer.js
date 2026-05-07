/**
 * Unified Audit Renderer - Clean, Single-Page Design
 * Single export button, unified visual hierarchy, minimal clutter
 */

class UnifiedAuditRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.data = null;
    }

    render(data) {
        this.data = data;

        // Check if we have audit data
        if (!data.account_brief && !data.sa_action_plan && !data.expansion_summary) {
            return null;
        }

        // Build unified layout
        const html = `
            <!-- Fixed Header with Export -->
            <div style="position: sticky; top: 0; z-index: 100; background: white; border-bottom: 2px solid #e5e7eb; padding: 16px 0; margin: -24px -24px 24px -24px; padding-left: 24px; padding-right: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0; font-size: 1.5rem; color: #1f2937;">Analysis Results</h2>
                        <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 0.875rem;">Generated ${new Date().toLocaleDateString()}</p>
                    </div>
                    <button onclick="window.unifiedRenderer.exportAll()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3); transition: all 0.2s;">
                        <span>📥</span>
                        <span>Export Full Report</span>
                    </button>
                </div>
            </div>

            <!-- Content -->
            ${this.renderWorkspaceAudit(data)}
            ${this.renderActivationExpansion(data)}
        `;

        this.container.innerHTML = html;
        this.attachEventListeners();
    }

    renderWorkspaceAudit(data) {
        if (!data.account_brief && !data.sa_action_plan) return '';

        const brief = data.account_brief || {};
        const actionPlan = data.sa_action_plan || {};
        const assessment = brief.workspace_health_assessment || {};

        const toneColors = {
            'Strong': { bg: '#d1fae5', text: '#065f46', border: '#10b981' },
            'Mixed': { bg: '#fef3c7', text: '#92400e', border: '#f59e0b' },
            'Needs Attention': { bg: '#fee2e2', text: '#991b1b', border: '#ef4444' }
        };
        const colors = toneColors[assessment.overall_tone] || toneColors['Mixed'];

        return `
            <!-- Executive Summary Card -->
            <div style="background: white; border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

                <!-- Health Badge -->
                <div style="display: inline-block; background: ${colors.bg}; color: ${colors.text}; padding: 8px 16px; border-radius: 20px; font-weight: 600; font-size: 0.875rem; margin-bottom: 20px;">
                    ${assessment.overall_tone || 'Mixed'} Health
                </div>

                <!-- Health Reasoning -->
                <p style="font-size: 1.125rem; color: #374151; line-height: 1.7; margin: 0 0 32px 0;">
                    ${assessment.health_reasoning || ''}
                </p>

                <!-- Two Column Layout: Strengths & Concerns -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 32px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <span style="font-size: 1.5rem;">✅</span>
                            <h3 style="margin: 0; font-size: 1rem; color: #10b981; text-transform: uppercase; letter-spacing: 0.5px;">Key Strengths</h3>
                        </div>
                        <ul style="margin: 0; padding: 0; list-style: none;">
                            ${(assessment.key_strengths || []).map(s => `
                                <li style="padding: 8px 0; color: #374151; line-height: 1.6; padding-left: 24px; position: relative;">
                                    <span style="position: absolute; left: 0; color: #10b981;">•</span>
                                    ${s}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <span style="font-size: 1.5rem;">⚠️</span>
                            <h3 style="margin: 0; font-size: 1rem; color: #ef4444; text-transform: uppercase; letter-spacing: 0.5px;">Key Concerns</h3>
                        </div>
                        <ul style="margin: 0; padding: 0; list-style: none;">
                            ${(assessment.key_concerns || []).map(c => `
                                <li style="padding: 8px 0; color: #374151; line-height: 1.6; padding-left: 24px; position: relative;">
                                    <span style="position: absolute; left: 0; color: #ef4444;">•</span>
                                    ${c}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>

                <!-- Critical Findings (Compact Inline) -->
                ${(brief.critical_findings && brief.critical_findings.length > 0) ? `
                    <div style="margin-bottom: 32px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <span style="font-size: 1.5rem;">🚨</span>
                            <h3 style="margin: 0; font-size: 1rem; color: #1f2937; text-transform: uppercase; letter-spacing: 0.5px;">Priority Actions</h3>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            ${brief.critical_findings.map((f, idx) => `
                                <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px 20px; border-radius: 8px; display: flex; gap: 16px; align-items: start;">
                                    <div style="background: #ef4444; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.875rem; flex-shrink: 0;">
                                        ${idx + 1}
                                    </div>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 600; color: #991b1b; margin-bottom: 6px;">${f.finding}</div>
                                        <div style="color: #7f1d1d; font-size: 0.875rem; margin-bottom: 8px;">${f.why_it_matters}</div>
                                        <div style="color: #991b1b; font-size: 0.875rem;">
                                            <strong>→ Action:</strong> ${f.recommended_action}
                                        </div>
                                    </div>
                                    <div style="background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; white-space: nowrap;">
                                        ${f.confidence}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Opportunities (Inline Pills) -->
                ${(brief.activation_opportunities && brief.activation_opportunities.length > 0) ? `
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <span style="font-size: 1.5rem;">🎯</span>
                            <h3 style="margin: 0; font-size: 1rem; color: #1f2937; text-transform: uppercase; letter-spacing: 0.5px;">Quick Wins</h3>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px;">
                            ${brief.activation_opportunities.map(o => `
                                <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #10b981; padding: 16px; border-radius: 8px;">
                                    <div style="font-weight: 600; color: #065f46; margin-bottom: 8px;">${o.opportunity}</div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #047857; font-size: 0.875rem;">👤 ${o.potential_reach}</span>
                                        <span style="background: #10b981; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                                            ${o.effort} Effort
                                        </span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>

            <!-- Detailed Findings (Expandable) -->
            ${this.renderDetailedFindings(actionPlan)}
        `;
    }

    renderDetailedFindings(actionPlan) {
        if (!actionPlan.findings || actionPlan.findings.length === 0) return '';

        return `
            <details style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" open>
                <summary style="cursor: pointer; font-size: 1.25rem; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
                    <span>📋</span>
                    <span>Detailed Analysis (${actionPlan.findings.length} findings)</span>
                    <span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; margin-left: auto;">
                        Click to expand
                    </span>
                </summary>

                ${actionPlan.findings.map((finding, idx) => this.renderFindingCard(finding, idx)).join('')}
            </details>
        `;
    }

    renderFindingCard(finding, idx) {
        const priorityColors = {
            'P0': { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
            'P1': { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
            'P2': { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' }
        };
        const colors = priorityColors[finding.priority] || priorityColors['P2'];

        return `
            <div style="border: 2px solid ${colors.border}; border-radius: 12px; padding: 24px; margin-bottom: 16px; background: ${colors.bg};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                            <span style="background: ${colors.border}; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">
                                ${idx + 1}
                            </span>
                            <h4 style="margin: 0; color: ${colors.text}; font-size: 1.125rem;">${finding.finding_fact}</h4>
                        </div>
                        <div style="color: ${colors.text}; font-size: 0.875rem; opacity: 0.8; margin-left: 44px;">
                            ${finding.category}
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span style="background: ${colors.border}; color: white; padding: 6px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                            ${finding.priority}
                        </span>
                        <span style="background: white; color: ${colors.text}; padding: 6px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 2px solid ${colors.border};">
                            ${finding.confidence}
                        </span>
                    </div>
                </div>

                <div style="margin-left: 44px;">
                    <div style="color: #374151; line-height: 1.6; margin-bottom: 16px;">
                        ${finding.interpretation?.likely_implication || ''}
                    </div>

                    <div style="background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 8px;">✅ Validation Steps:</div>
                        <ol style="margin: 0; padding-left: 20px; color: #4b5563;">
                            ${(finding.validation_steps || []).map(step => `<li style="margin: 4px 0;">${step}</li>`).join('')}
                        </ol>
                    </div>

                    ${finding.customer_safe_wording ? `
                        <div style="background: #eff6ff; border-left: 3px solid #3b82f6; padding: 12px; border-radius: 6px; font-size: 0.875rem; color: #1e40af;">
                            <strong>💬 Customer-Safe Wording:</strong> ${finding.customer_safe_wording}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderActivationExpansion(data) {
        if (!data.expansion_summary) return '';

        const summary = data.expansion_summary;

        return `
            <div style="background: white; border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h2 style="margin: 0 0 8px 0; font-size: 1.5rem; color: #1f2937;">💼 Activation & Expansion</h2>
                <p style="color: #6b7280; margin: 0 0 24px 0;">${summary.highest_impact_opportunity}</p>

                <!-- Stats -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px;">
                    <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #1f2937;">${(summary.total_untapped_users || 0).toLocaleString()}</div>
                        <div style="font-size: 0.875rem; color: #6b7280; margin-top: 4px;">Untapped Users</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #065f46;">${(summary.quick_wins || []).length}</div>
                        <div style="font-size: 0.875rem; color: #065f46; margin-top: 4px;">Quick Wins</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 20px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 2rem; font-weight: 700; color: #1e40af;">${(summary.strategic_opportunities || []).length}</div>
                        <div style="font-size: 0.875rem; color: #1e40af; margin-top: 4px;">Strategic Plays</div>
                    </div>
                </div>

                <!-- Quick Wins List -->
                ${(summary.quick_wins && summary.quick_wins.length > 0) ? `
                    <div>
                        <h3 style="font-size: 1rem; color: #1f2937; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">⚡ Quick Wins</h3>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            ${summary.quick_wins.map((win, idx) => `
                                <div style="display: flex; gap: 12px; padding: 12px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #10b981;">
                                    <div style="background: #10b981; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">
                                        ${idx + 1}
                                    </div>
                                    <div style="color: #374151;">${win}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    attachEventListeners() {
        // Event listeners attached via onclick in HTML
    }

    exportAll() {
        if (!this.data) {
            alert('No data to export');
            return;
        }

        const filename = `segment-audit-${new Date().toISOString().split('T')[0]}.json`;
        const blob = new Blob([JSON.stringify(this.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Global instance
window.unifiedRenderer = null;
