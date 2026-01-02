#!/usr/bin/env python3
"""
Competitive Intelligence Data Analysis Script
Extracts metrics, generates SWOT analysis, and creates visualizations
"""

import json
import os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Set up fonts for international character support
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# Create output directories
BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"
CHARTS_DIR = FILES_DIR / "charts"
DATA_DIR = FILES_DIR / "data"

CHARTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ========== DATA EXTRACTION ==========

def extract_competitive_data():
    """Extract key metrics from research files"""

    data = {
        "market_share": {
            "2024_Q3": {
                "AWS": 31,
                "Azure": 24,
                "GCP": 11
            },
            "2025_Q2": {
                "AWS": 30,
                "Azure": 20,
                "GCP": 13
            }
        },
        "growth_rate_2025": {
            "AWS": 17.5,
            "Azure": 39,
            "GCP": 32
        },
        "revenue_2025": {
            "AWS": 132,  # Billion USD (annualized)
            "Azure": 75,  # Billion USD (FY 2025)
            "GCP": 50     # Billion USD (>50B)
        },
        "customer_growth_yoy": {
            "AWS": 28,    # Startups/SMB segment
            "Azure": 14,
            "GCP": 23
        },
        "pricing_comparison": {
            "compute_vm_monthly": {
                "AWS": 53.29,      # c6g.large on-demand
                "Azure": 3.80,     # Bs-series cheapest
                "GCP": 34.20       # n1-standard-1 (~$0.0475/hr * 720hrs)
            },
            "serverless_per_million_requests": {
                "AWS": 0.20,
                "Azure": 0.20,
                "GCP": 0.40
            },
            "object_storage_per_gb_month": {
                "AWS": 0.023,      # S3 Standard
                "Azure": 0.018,    # Blob Hot tier
                "GCP": 0.020       # Standard (estimated)
            },
            "nosql_storage_per_gb_month": {
                "AWS": 0.25,       # DynamoDB
                "Azure": 0.25,     # Cosmos DB
                "GCP": 0.18        # Firestore
            }
        },
        "feature_coverage": {
            "compute": {
                "AWS": 10,
                "Azure": 9,
                "GCP": 9
            },
            "storage": {
                "AWS": 10,
                "Azure": 9,
                "GCP": 8
            },
            "database": {
                "AWS": 10,
                "Azure": 9,
                "GCP": 9
            },
            "ai_ml": {
                "AWS": 8,
                "Azure": 9,
                "GCP": 10
            },
            "hybrid_cloud": {
                "AWS": 7,
                "Azure": 10,
                "GCP": 6
            },
            "enterprise_integration": {
                "AWS": 7,
                "Azure": 10,
                "GCP": 7
            }
        },
        "customer_satisfaction": {
            "AWS": {
                "scalability": 9,
                "security": 9,
                "pricing_complexity": 4,  # Lower is worse
                "support": 7,
                "ease_of_use": 6
            },
            "Azure": {
                "scalability": 9,
                "security": 8,
                "pricing_complexity": 4,
                "support": 5,
                "ease_of_use": 7
            },
            "GCP": {
                "scalability": 9,
                "security": 8,
                "pricing_complexity": 3,
                "support": 4,
                "ease_of_use": 5
            }
        }
    }

    return data

def generate_swot_analysis():
    """Generate SWOT analysis for each competitor"""

    swot = {
        "AWS": {
            "strengths": [
                "Market leader with 30% market share",
                "Largest service portfolio (200+ services)",
                "Custom silicon advantage (Graviton5, Trainium3)",
                "Strong global infrastructure ($132B annualized revenue)",
                "Excellent scalability and reliability",
                "Strong security features and compliance",
                "High customer adoption of Graviton (98% of top 1000 customers)",
                "Deep backlog ($200B) provides revenue visibility"
            ],
            "weaknesses": [
                "Market share declining from 33% (2021) to 30% (2025)",
                "Slowest growth rate among Big Three (17.5% vs 39% Azure, 32% GCP)",
                "Complex pricing model (most common customer complaint)",
                "Disconnected service integration compared to competitors",
                "Variable support quality",
                "Steep learning curve",
                "No proprietary foundation models (relies on third-party)"
            ],
            "opportunities": [
                "AI workload migration from training to production",
                "Legacy application modernization market",
                "Multicloud/hybrid cloud adoption",
                "Startups and SMB segment growing 28% YoY",
                "Emerging markets expansion",
                "Agentic AI and autonomous coding tools"
            ],
            "threats": [
                "Microsoft's enterprise integration and Office 365 synergies",
                "Google's AI/ML leadership and proprietary models",
                "Competitors growing 2x faster",
                "Customer demand for pricing transparency",
                "Rising competition in custom silicon space",
                "Vendor lock-in concerns driving multi-cloud strategies"
            ]
        },
        "Azure": {
            "strengths": [
                "Strong #2 position with 20% market share",
                "Fastest growth rate among Big Three (39% YoY)",
                "$75B annual revenue with 34% growth",
                "Seamless Microsoft ecosystem integration",
                "Best-in-class hybrid cloud solutions (Azure Stack)",
                "Only cloud offering both Claude and GPT models",
                "Strong enterprise focus and Active Directory integration",
                "Custom silicon (Azure Boost) with 400 Gbps networking"
            ],
            "weaknesses": [
                "Pricing complexity and unexpected cost growth",
                "Support response delays for smaller customers",
                "Steep learning curve and complex configuration",
                "Vendor lock-in to Microsoft ecosystem",
                "Fewer data centers than AWS",
                "Limited integration with non-Microsoft tools",
                "Azure Virtual Desktop needs maturity improvements"
            ],
            "opportunities": [
                "AI model diversity advantage (Claude + GPT)",
                "Vector database capabilities (SQL Server 2025)",
                "Enterprise agentic platforms (Microsoft Discovery)",
                "Hybrid cloud market expansion",
                "Multi-agent systems growth",
                "Developer experience improvements"
            ],
            "threats": [
                "AWS's market leadership and service breadth",
                "Google's AI/ML technical superiority",
                "Organizations avoiding vendor lock-in",
                "Complex pricing driving customers to competitors",
                "Limited multi-cloud support",
                "Perception of being 'Microsoft-only' solution"
            ]
        },
        "GCP": {
            "strengths": [
                "AI/ML leadership with proprietary TPUs and Gemini models",
                "Best-in-class data analytics (BigQuery)",
                "Full-stack integration from chips to models",
                "Strong growth: 30% revenue, 23% customer base YoY",
                "7th-gen TPU (Ironwood) launching 2025",
                "Superior network infrastructure",
                "200+ foundation models on Vertex AI",
                "Only platform with all four generative media types"
            ],
            "weaknesses": [
                "Smallest market share among Big Three (13%)",
                "Complex pricing (most common customer complaint)",
                "Poor customer support with support paywalls",
                "Steep learning curve and insufficient training resources",
                "Limited hybrid/multi-cloud integration",
                "Frequent UI changes disrupt productivity",
                "Higher pricing than Azure for similar services"
            ],
            "opportunities": [
                "AI/ML workload migration market",
                "Big data analytics expansion",
                "Enterprise search quality advantage",
                "Open source ecosystem (TensorFlow, Kubernetes)",
                "Agent2Agent (A2A) protocol adoption",
                "Palo Alto partnership ($10B agreement)"
            ],
            "threats": [
                "AWS's market dominance and service breadth",
                "Azure's enterprise integration advantages",
                "Limited market share limits ecosystem development",
                "Customer support issues driving away smaller customers",
                "Pricing transparency demands",
                "Hybrid cloud requirements favor Azure"
            ]
        }
    }

    return swot

# ========== VISUALIZATIONS ==========

def create_market_share_chart(data):
    """Create market share comparison chart"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Q3 2024 Pie Chart
    labels = ['AWS', 'Azure', 'GCP', 'Others']
    q3_sizes = [31, 24, 11, 34]
    colors = ['#FF9900', '#00A4EF', '#4285F4', '#CCCCCC']
    explode = (0.05, 0.02, 0.02, 0)

    ax1.pie(q3_sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.set_title('Cloud Market Share Q3 2024', fontsize=14, fontweight='bold')

    # Q2 2025 Pie Chart
    q2_sizes = [30, 20, 13, 37]

    ax2.pie(q2_sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax2.set_title('Cloud Market Share Q2 2025', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'market_share_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created market share comparison chart")

def create_growth_rate_chart(data):
    """Create growth rate comparison bar chart"""

    fig, ax = plt.subplots(figsize=(10, 6))

    providers = ['AWS', 'Azure', 'GCP']
    growth_rates = [17.5, 39, 32]
    colors = ['#FF9900', '#00A4EF', '#4285F4']

    bars = ax.bar(providers, growth_rates, color=colors, alpha=0.8, edgecolor='black')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}%',
                ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel('Year-over-Year Growth Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Cloud Provider Growth Rate Comparison (2025)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 45)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'growth_rate_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created growth rate comparison chart")

def create_revenue_chart(data):
    """Create revenue comparison bar chart"""

    fig, ax = plt.subplots(figsize=(10, 6))

    providers = ['AWS', 'Azure', 'GCP']
    revenues = [132, 75, 50]
    colors = ['#FF9900', '#00A4EF', '#4285F4']

    bars = ax.bar(providers, revenues, color=colors, alpha=0.8, edgecolor='black')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${height}B',
                ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel('Annual Revenue (Billion USD)', fontsize=12, fontweight='bold')
    ax.set_title('Cloud Provider Revenue Comparison (2025)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 150)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'revenue_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created revenue comparison chart")

def create_pricing_comparison_chart(data):
    """Create pricing comparison across services"""

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    providers = ['AWS', 'Azure', 'GCP']
    colors = ['#FF9900', '#00A4EF', '#4285F4']

    # Compute VM pricing
    vm_prices = [53.29, 3.80, 34.20]
    bars1 = ax1.bar(providers, vm_prices, color=colors, alpha=0.8, edgecolor='black')
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Price (USD/month)', fontsize=10, fontweight='bold')
    ax1.set_title('Compute VM Pricing Comparison', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Serverless pricing
    serverless_prices = [0.20, 0.20, 0.40]
    bars2 = ax2.bar(providers, serverless_prices, color=colors, alpha=0.8, edgecolor='black')
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Price (USD/million requests)', fontsize=10, fontweight='bold')
    ax2.set_title('Serverless Function Pricing', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # Object storage pricing
    storage_prices = [0.023, 0.018, 0.020]
    bars3 = ax3.bar(providers, storage_prices, color=colors, alpha=0.8, edgecolor='black')
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Price (USD/GB/month)', fontsize=10, fontweight='bold')
    ax3.set_title('Object Storage Pricing', fontsize=12, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3, linestyle='--')

    # NoSQL storage pricing
    nosql_prices = [0.25, 0.25, 0.18]
    bars4 = ax4.bar(providers, nosql_prices, color=colors, alpha=0.8, edgecolor='black')
    for bar in bars4:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Price (USD/GB/month)', fontsize=10, fontweight='bold')
    ax4.set_title('NoSQL Database Storage Pricing', fontsize=12, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'pricing_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created pricing comparison chart")

def create_feature_matrix_heatmap(data):
    """Create feature coverage heatmap"""

    categories = ['Compute', 'Storage', 'Database', 'AI/ML', 'Hybrid\nCloud', 'Enterprise\nIntegration']
    providers = ['AWS', 'Azure', 'GCP']

    # Feature scores (out of 10)
    scores = np.array([
        [10, 10, 10, 8, 7, 7],   # AWS
        [9, 9, 9, 9, 10, 10],     # Azure
        [9, 8, 9, 10, 6, 7]       # GCP
    ])

    fig, ax = plt.subplots(figsize=(12, 6))

    im = ax.imshow(scores, cmap='RdYlGn', aspect='auto', vmin=0, vmax=10)

    # Set ticks
    ax.set_xticks(np.arange(len(categories)))
    ax.set_yticks(np.arange(len(providers)))
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_yticklabels(providers, fontsize=11, fontweight='bold')

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Add text annotations
    for i in range(len(providers)):
        for j in range(len(categories)):
            text = ax.text(j, i, scores[i, j],
                          ha="center", va="center", color="black",
                          fontsize=12, fontweight='bold')

    ax.set_title('Feature Coverage Matrix (Score: 0-10)', fontsize=14, fontweight='bold', pad=20)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Capability Score', rotation=270, labelpad=20, fontweight='bold')

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'feature_matrix_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created feature matrix heatmap")

def create_customer_satisfaction_radar(data):
    """Create customer satisfaction radar chart"""

    categories = ['Scalability', 'Security', 'Pricing\nClarity', 'Support', 'Ease of Use']

    # AWS scores
    aws_scores = [9, 9, 4, 7, 6]
    # Azure scores
    azure_scores = [9, 8, 4, 5, 7]
    # GCP scores
    gcp_scores = [9, 8, 3, 4, 5]

    # Number of variables
    num_vars = len(categories)

    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Close the plot
    aws_scores += aws_scores[:1]
    azure_scores += azure_scores[:1]
    gcp_scores += gcp_scores[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # Plot data
    ax.plot(angles, aws_scores, 'o-', linewidth=2, label='AWS', color='#FF9900')
    ax.fill(angles, aws_scores, alpha=0.25, color='#FF9900')

    ax.plot(angles, azure_scores, 'o-', linewidth=2, label='Azure', color='#00A4EF')
    ax.fill(angles, azure_scores, alpha=0.25, color='#00A4EF')

    ax.plot(angles, gcp_scores, 'o-', linewidth=2, label='GCP', color='#4285F4')
    ax.fill(angles, gcp_scores, alpha=0.25, color='#4285F4')

    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')

    # Set y-axis limit
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Add legend
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)

    ax.set_title('Customer Satisfaction Comparison\n(Score: 0-10, Higher is Better)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'customer_satisfaction_radar.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created customer satisfaction radar chart")

def create_competitive_positioning_chart(data):
    """Create competitive positioning quadrant chart"""

    fig, ax = plt.subplots(figsize=(12, 10))

    # Position data: (market_share, growth_rate)
    positions = {
        'AWS': (30, 17.5),
        'Azure': (20, 39),
        'GCP': (13, 32)
    }

    colors = {
        'AWS': '#FF9900',
        'Azure': '#00A4EF',
        'GCP': '#4285F4'
    }

    # Revenue size for bubble size (scaled)
    revenues = {
        'AWS': 132,
        'Azure': 75,
        'GCP': 50
    }

    for provider, (share, growth) in positions.items():
        size = revenues[provider] * 30  # Scale for visibility
        ax.scatter(share, growth, s=size, c=colors[provider], alpha=0.6,
                  edgecolors='black', linewidth=2)
        ax.annotate(f'{provider}\n(${revenues[provider]}B)',
                   xy=(share, growth), fontsize=12, fontweight='bold',
                   ha='center', va='center')

    # Add quadrant lines
    ax.axhline(y=25, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.axvline(x=20, color='gray', linestyle='--', alpha=0.5, linewidth=1)

    # Add quadrant labels
    ax.text(35, 42, 'Leaders\n(High Share, High Growth)', fontsize=11,
            ha='center', va='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax.text(10, 42, 'Challengers\n(Low Share, High Growth)', fontsize=11,
            ha='center', va='center', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
    ax.text(35, 12, 'Established\n(High Share, Low Growth)', fontsize=11,
            ha='center', va='center', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
    ax.text(10, 12, 'Niche\n(Low Share, Low Growth)', fontsize=11,
            ha='center', va='center', bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))

    ax.set_xlabel('Market Share (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Growth Rate (% YoY)', fontsize=12, fontweight='bold')
    ax.set_title('Competitive Positioning Analysis (2025)\nBubble size = Annual Revenue',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(5, 40)
    ax.set_ylim(10, 45)

    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'competitive_positioning.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✓ Created competitive positioning chart")

# ========== MAIN EXECUTION ==========

def main():
    print("=" * 60)
    print("COMPETITIVE INTELLIGENCE DATA ANALYSIS")
    print("=" * 60)
    print()

    # Extract data
    print("1. Extracting competitive data...")
    data = extract_competitive_data()

    # Generate SWOT
    print("2. Generating SWOT analysis...")
    swot = generate_swot_analysis()

    # Save JSON data
    print("3. Saving analysis data...")
    with open(DATA_DIR / 'competitive_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved competitive analysis data to {DATA_DIR / 'competitive_analysis.json'}")

    with open(DATA_DIR / 'swot_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(swot, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved SWOT analysis to {DATA_DIR / 'swot_analysis.json'}")

    # Create visualizations
    print("\n4. Creating visualizations...")
    create_market_share_chart(data)
    create_growth_rate_chart(data)
    create_revenue_chart(data)
    create_pricing_comparison_chart(data)
    create_feature_matrix_heatmap(data)
    create_customer_satisfaction_radar(data)
    create_competitive_positioning_chart(data)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nOutputs saved to:")
    print(f"  - Charts: {CHARTS_DIR}")
    print(f"  - Data: {DATA_DIR}")
    print()

if __name__ == '__main__':
    main()
