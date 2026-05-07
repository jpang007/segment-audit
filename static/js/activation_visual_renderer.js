/**
 * Visual Renderer for Activation & Expansion Output
 * Renders unused audiences, destinations, missing flows, and product opportunities
 */

class ActivationVisualRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    render(data) {
        if (!data.expansion_summary) {
            return null;
        }

        const html = `
            ${this.renderExpansionSummary(data.expansion_summary)}
            ${this.renderQuickWins(data.expansion_summary.quick_wins)}
            ${this.renderUnusedAudiences(data.unused_audiences)}
            ${this.renderUnusedDestinations(data.unused_destinations)}
            ${this.renderMissingFlows(data.missing_activation_flows)}
            ${this.renderProductOpportunities(data.segment_product_opportunities)}
        `;

        this.container.innerHTML = html;
        this.attachEventListeners();
    }

    renderExpansionSummary(summary) {
        if (!summary) return '';

        return `
            <div class="expansion-summary-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 32px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3); color: white;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 24px;">
                    <div>
                        <h2 style="margin: 0 0 8px 0; font-size: 1.75rem; font-weight: 700;">🚀 Activation & Expansion Summary</h2>
                        <p style="margin: 0; opacity: 0.9; font-size: 1.125rem;">${summary.highest_impact_opportunity || 'Multiple opportunities identified'}</p>
                    </div>
                    <button onclick="window.activationRenderer.exportJSON()" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; backdrop-filter: blur(10px);">
                        📥 Export JSON
                    </button>
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <div style="font-size: 2rem; font-weight: 700; margin-bottom: 4px;">${(summary.total_untapped_users || 0).toLocaleString()}</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">Untapped Users</div>
                        ${summary.total_untapped_users_definition ? `<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 8px;">${summary.total_untapped_users_definition}</div>` : ''}
                    </div>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <div style="font-size: 2rem; font-weight: 700; margin-bottom: 4px;">${(summary.quick_wins || []).length}</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">Quick Wins</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <div style="font-size: 2rem; font-weight: 700; margin-bottom: 4px;">${(summary.strategic_opportunities || []).length}</div>
                        <div style="font-size: 0.875rem; opacity: 0.9;">Strategic Plays</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderQuickWins(quickWins) {
        if (!quickWins || quickWins.length === 0) return '';

        return `
            <div class="quick-wins-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 16px 0; color: #1f2937; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
                    ⚡ Quick Wins
                </h3>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${quickWins.map((win, idx) => `
                        <div style="display: flex; align-items: start; gap: 12px; padding: 12px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #10b981;">
                            <div style="background: #10b981; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">
                                ${idx + 1}
                            </div>
                            <div style="color: #374151; flex: 1;">${win}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderUnusedAudiences(audiences) {
        if (!audiences || audiences.length === 0) return '';

        return `
            <div class="unused-audiences-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #1f2937; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
                        👥 Unused Audiences <span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 600;">${audiences.length}</span>
                    </h3>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="window.activationRenderer.filterAudiences('all')" class="filter-btn active" data-filter="all" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: #667eea; color: white; cursor: pointer; font-size: 0.875rem; font-weight: 600;">All</button>
                        <button onclick="window.activationRenderer.filterAudiences('enabled')" class="filter-btn" data-filter="enabled" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: white; color: #6b7280; cursor: pointer; font-size: 0.875rem; font-weight: 600;">Enabled</button>
                        <button onclick="window.activationRenderer.filterAudiences('disabled')" class="filter-btn" data-filter="disabled" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: white; color: #6b7280; cursor: pointer; font-size: 0.875rem; font-weight: 600;">Disabled</button>
                    </div>
                </div>

                <div id="audiences-container" style="display: flex; flex-direction: column; gap: 16px;">
                    ${audiences.map(aud => this.renderAudienceCard(aud)).join('')}
                </div>
            </div>
        `;
    }

    renderAudienceCard(aud) {
        const effortColors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444'
        };
        const effortColor = effortColors[aud.estimated_effort?.toLowerCase()] || '#6b7280';
        const statusColor = aud.status === 'enabled' ? '#10b981' : '#6b7280';

        return `
            <div class="audience-card" data-status="${aud.status}" style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: #fafafa;">
                <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 12px;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <h4 style="margin: 0; color: #1f2937; font-size: 1.125rem;">${aud.audience_name}</h4>
                            <span style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${aud.status}</span>
                            ${aud.estimated_effort ? `<span style="background: ${effortColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${aud.estimated_effort} effort</span>` : ''}
                        </div>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 4px;">
                            👤 <strong>${(aud.user_count || 0).toLocaleString()}</strong> users
                            ${aud.owner ? ` • 👔 Owner: <strong>${aud.owner}</strong>` : ''}
                        </div>
                    </div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">💡 Opportunity:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${aud.opportunity}</div>
                </div>

                ${aud.blocking_factor ? `
                    <div style="margin-bottom: 12px;">
                        <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">🚧 Blocking Factor:</div>
                        <div style="color: #ef4444; font-size: 0.875rem;">${aud.blocking_factor}</div>
                    </div>
                ` : ''}

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">✅ Suggested Action:</div>
                    <div style="color: #059669; font-size: 0.875rem; background: #d1fae5; padding: 8px 12px; border-radius: 6px;">${aud.suggested_action}</div>
                </div>

                ${aud.evidence ? `
                    <details style="margin-top: 12px;">
                        <summary style="cursor: pointer; color: #667eea; font-size: 0.875rem; font-weight: 600;">📊 Evidence</summary>
                        <div style="margin-top: 8px; padding: 12px; background: #f3f4f6; border-radius: 6px; font-family: monospace; font-size: 0.75rem; color: #374151;">
                            ${Object.entries(aud.evidence).map(([key, val]) => `<div><strong>${key}:</strong> ${val}</div>`).join('')}
                        </div>
                    </details>
                ` : ''}

                ${aud.caveats && aud.caveats.length > 0 ? `
                    <div style="margin-top: 12px; padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px;">
                        <div style="font-weight: 600; color: #92400e; margin-bottom: 6px;">⚠️ Caveats:</div>
                        <ul style="margin: 0; padding-left: 20px; color: #92400e; font-size: 0.875rem;">
                            ${aud.caveats.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderUnusedDestinations(destinations) {
        if (!destinations || destinations.length === 0) return '';

        return `
            <div class="unused-destinations-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
                    🎯 Unused Destinations <span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 600;">${destinations.length}</span>
                </h3>

                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 16px;">
                    ${destinations.map(dest => this.renderDestinationCard(dest)).join('')}
                </div>
            </div>
        `;
    }

    renderDestinationCard(dest) {
        const categoryColors = {
            'email': '#8b5cf6',
            'analytics': '#3b82f6',
            'ads': '#ec4899',
            'warehouse': '#10b981',
            'other': '#6b7280'
        };
        const categoryColor = categoryColors[dest.category?.toLowerCase()] || '#6b7280';
        const effortColors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444'
        };
        const effortColor = effortColors[dest.estimated_effort?.toLowerCase()] || '#6b7280';

        return `
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: #fafafa;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #1f2937; font-size: 1.125rem; flex: 1;">${dest.destination_name}</h4>
                    <span style="background: ${categoryColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${dest.category}</span>
                    ${dest.estimated_effort ? `<span style="background: ${effortColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${dest.estimated_effort}</span>` : ''}
                </div>

                ${dest.owner ? `<div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 12px;">👔 Owner: <strong>${dest.owner}</strong></div>` : ''}

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">💡 Opportunity:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${dest.opportunity}</div>
                </div>

                ${dest.suggested_audiences && dest.suggested_audiences.length > 0 ? `
                    <div style="margin-bottom: 12px;">
                        <div style="font-weight: 600; color: #374151; margin-bottom: 8px;">🎯 Suggested Audiences:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${dest.suggested_audiences.map(aud => `
                                <span style="background: #dbeafe; color: #1e40af; padding: 6px 12px; border-radius: 6px; font-size: 0.875rem;">${aud}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${dest.caveats && dest.caveats.length > 0 ? `
                    <div style="margin-top: 12px; padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px;">
                        <div style="font-weight: 600; color: #92400e; margin-bottom: 6px;">⚠️ Caveats:</div>
                        <ul style="margin: 0; padding-left: 20px; color: #92400e; font-size: 0.875rem;">
                            ${dest.caveats.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderMissingFlows(flows) {
        if (!flows || flows.length === 0) return '';

        return `
            <div class="missing-flows-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
                    🔌 Missing Activation Flows <span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 600;">${flows.length}</span>
                </h3>

                <div style="display: flex; flex-direction: column; gap: 16px;">
                    ${flows.map(flow => this.renderFlowCard(flow)).join('')}
                </div>
            </div>
        `;
    }

    renderFlowCard(flow) {
        const impactColors = {
            'high': '#ef4444',
            'medium': '#f59e0b',
            'low': '#6b7280'
        };
        const impactColor = impactColors[flow.impact_level?.toLowerCase()] || '#6b7280';
        const effortColors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444'
        };
        const effortColor = effortColors[flow.estimated_effort?.toLowerCase()] || '#6b7280';

        return `
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: #fafafa;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #1f2937; font-size: 1.125rem; flex: 1;">${flow.data_source}</h4>
                    <span style="background: ${impactColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${flow.impact_level} impact</span>
                    ${flow.estimated_effort ? `<span style="background: ${effortColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${flow.estimated_effort} effort</span>` : ''}
                </div>

                <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 12px;">
                    📦 Data type: <strong>${flow.data_type}</strong> • 🚫 Not used in: <strong>${flow.not_used_in}</strong>
                    ${flow.owner ? ` • 👔 Owner: <strong>${flow.owner}</strong>` : ''}
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">💡 Opportunity:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${flow.opportunity}</div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">📝 Reasoning:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${flow.reasoning}</div>
                </div>

                ${flow.evidence ? `
                    <details style="margin-top: 12px;">
                        <summary style="cursor: pointer; color: #667eea; font-size: 0.875rem; font-weight: 600;">📊 Evidence</summary>
                        <div style="margin-top: 8px; padding: 12px; background: #f3f4f6; border-radius: 6px; font-family: monospace; font-size: 0.75rem; color: #374151;">
                            ${Object.entries(flow.evidence).map(([key, val]) => `<div><strong>${key}:</strong> ${val}</div>`).join('')}
                        </div>
                    </details>
                ` : ''}
            </div>
        `;
    }

    renderProductOpportunities(products) {
        if (!products || products.length === 0) return '';

        return `
            <div class="product-opportunities-section" style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
                    🎁 Segment Product Opportunities <span style="background: #e5e7eb; color: #6b7280; padding: 4px 12px; border-radius: 12px; font-size: 0.875rem; font-weight: 600;">${products.length}</span>
                </h3>

                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 16px;">
                    ${products.map(prod => this.renderProductCard(prod)).join('')}
                </div>
            </div>
        `;
    }

    renderProductCard(prod) {
        const confidenceColors = {
            'high': '#10b981',
            'medium': '#f59e0b',
            'low': '#6b7280'
        };
        const confidenceColor = confidenceColors[prod.confidence?.toLowerCase()] || '#6b7280';
        const effortColors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444'
        };
        const effortColor = effortColors[prod.estimated_effort?.toLowerCase()] || '#6b7280';

        return `
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: linear-gradient(135deg, #fafafa 0%, #f3f4f6 100%);">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #1f2937; font-size: 1.125rem; flex: 1;">${prod.product}</h4>
                    <span style="background: ${confidenceColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${prod.confidence} confidence</span>
                    ${prod.estimated_effort ? `<span style="background: ${effortColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">${prod.estimated_effort} effort</span>` : ''}
                </div>

                ${prod.owner ? `<div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 12px;">👔 Owner: <strong>${prod.owner}</strong></div>` : ''}

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">📊 Evidence:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${prod.evidence}</div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">🎯 Use Case:</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">${prod.use_case}</div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #374151; margin-bottom: 4px;">💡 Impact:</div>
                    <div style="color: #059669; font-size: 0.875rem; background: #d1fae5; padding: 8px 12px; border-radius: 6px;">${prod.impact}</div>
                </div>

                ${prod.prerequisite ? `
                    <div style="margin-top: 12px; padding: 12px; background: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 6px;">
                        <div style="font-weight: 600; color: #1e40af; margin-bottom: 4px;">✅ Prerequisite:</div>
                        <div style="color: #1e40af; font-size: 0.875rem;">${prod.prerequisite}</div>
                    </div>
                ` : ''}

                ${prod.caveats && prod.caveats.length > 0 ? `
                    <div style="margin-top: 12px; padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px;">
                        <div style="font-weight: 600; color: #92400e; margin-bottom: 6px;">⚠️ Caveats:</div>
                        <ul style="margin: 0; padding-left: 20px; color: #92400e; font-size: 0.875rem;">
                            ${prod.caveats.map(c => `<li>${c}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    attachEventListeners() {
        // Filter buttons already have onclick handlers
    }

    filterAudiences(filter) {
        const cards = document.querySelectorAll('.audience-card');
        const buttons = document.querySelectorAll('.filter-btn');

        // Update button states
        buttons.forEach(btn => {
            if (btn.getAttribute('data-filter') === filter) {
                btn.style.background = '#667eea';
                btn.style.color = 'white';
                btn.classList.add('active');
            } else {
                btn.style.background = 'white';
                btn.style.color = '#6b7280';
                btn.classList.remove('active');
            }
        });

        // Filter cards
        cards.forEach(card => {
            if (filter === 'all') {
                card.style.display = 'block';
            } else {
                card.style.display = card.getAttribute('data-status') === filter ? 'block' : 'none';
            }
        });
    }

    exportJSON() {
        // Get the original data from the page
        const data = window.activationData;
        if (!data) {
            alert('No data available to export');
            return;
        }

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `activation-expansion-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Global instance
window.activationRenderer = null;
