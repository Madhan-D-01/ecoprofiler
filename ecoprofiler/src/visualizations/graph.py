import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging
from typing import List, Dict, Any

logger = logging.getLogger("GraphVisualization")

# Try to import networkx, but provide fallback if not available
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available. Graph visualizations will be limited.")

def create_entity_graph(companies: List[Dict[str, Any]]) -> go.Figure:
    """Create network graph of corporate entities and relationships"""
    try:
        if not companies:
            return create_empty_graph("No company data available")
        
        if not NETWORKX_AVAILABLE:
            return create_simple_bar_chart(companies)
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes for companies
        for company in companies:
            company_id = company.get('lei') or company.get('wikidata_id') or company.get('name')
            if company_id:
                G.add_node(
                    company_id,
                    name=company.get('name', 'Unknown'),
                    type='company',
                    sanctioned=company.get('sanctioned', False),
                    shell_company=company.get('shell_company', False)
                )
        
        # Add edges based on relationships
        for company in companies:
            company_id = company.get('lei') or company.get('wikidata_id') or company.get('name')
            
            # Add parent relationships
            if company.get('parent') and company_id:
                parent_id = company['parent'].get('lei') or company['parent'].get('name')
                if parent_id and parent_id in G.nodes:
                    G.add_edge(company_id, parent_id, relationship='parent')
            
            # Add subsidiary relationships
            for subsidiary in company.get('subsidiaries', []):
                sub_id = subsidiary.get('lei') or subsidiary.get('name')
                if sub_id and sub_id in G.nodes and company_id:
                    G.add_edge(company_id, sub_id, relationship='subsidiary')
        
        # Convert to Plotly figure
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Extract node positions
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node label
            node_data = G.nodes[node]
            label = f"{node_data.get('name', node)}"
            if node_data.get('sanctioned'):
                label += " 🚨"
            if node_data.get('shell_company'):
                label += " ⚠️"
            node_text.append(label)
            
            # Node color based on risk
            if node_data.get('sanctioned'):
                node_color.append('red')
            elif node_data.get('shell_company'):
                node_color.append('orange')
            else:
                node_color.append('blue')
                
            # Node size based on connections
            node_size.append(15 + len(list(G.neighbors(node))) * 3)
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                color=node_color,
                size=node_size,
                line=dict(width=2, color='darkblue')
            )
        )
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace = go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                line=dict(width=1, color='gray'),
                hoverinfo='none',
                mode='lines'
            )
            edge_traces.append(edge_trace)
        
        # Create figure
        fig = go.Figure()
        
        # Add edges first
        for trace in edge_traces:
            fig.add_trace(trace)
        
        # Add nodes on top
        fig.add_trace(node_trace)
        
        # Update layout
        fig.update_layout(
            title='Corporate Entity Network',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="🚨 = Sanctioned | ⚠️ = Shell Company Risk",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor="left", yanchor="bottom",
                font=dict(size=10)
            ) ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        logger.info("Entity network graph created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating entity graph: {str(e)}")
        return create_empty_graph(f"Error creating network: {str(e)}")

def create_simple_bar_chart(companies: List[Dict[str, Any]]) -> go.Figure:
    """Create a simple bar chart when networkx is not available"""
    try:
        if not companies:
            return create_empty_graph("No company data available")
        
        # Extract company names and risk scores
        company_data = []
        for company in companies:
            risk_score = 0
            if company.get('sanctioned'):
                risk_score += 50
            if company.get('shell_company'):
                risk_score += 30
            
            company_data.append({
                'name': company.get('name', 'Unknown'),
                'risk_score': risk_score,
                'sanctioned': company.get('sanctioned', False)
            })
        
        df = pd.DataFrame(company_data)
        df = df.sort_values('risk_score', ascending=False)
        
        # Create bar chart
        fig = px.bar(
            df,
            x='name',
            y='risk_score',
            title='Company Risk Scores (NetworkX not available)',
            labels={'name': 'Company', 'risk_score': 'Risk Score'},
            color='risk_score',
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating simple bar chart: {str(e)}")
        return create_empty_graph("Error creating visualization")

def create_risk_bar_chart(companies: List[Dict[str, Any]]) -> go.Figure:
    """Create bar chart of company risk levels"""
    try:
        if not companies:
            return create_empty_chart("No Company Data")
        
        # Calculate risk scores
        risk_data = []
        for company in companies:
            risk_score = 0
            if company.get('sanctioned'):
                risk_score += 50
            if company.get('shell_company'):
                risk_score += 30
            if company.get('industry') in ['mining', 'logging', 'oil', 'quarry']:
                risk_score += 20
                
            risk_data.append({
                'name': company.get('name', 'Unknown'),
                'risk_score': min(100, risk_score),
                'sanctioned': company.get('sanctioned', False)
            })
        
        df = pd.DataFrame(risk_data)
        df = df.sort_values('risk_score', ascending=False).head(10)  # Top 10
        
        # Create bar chart
        fig = px.bar(
            df,
            x='risk_score',
            y='name',
            orientation='h',
            color='risk_score',
            color_continuous_scale='RdYlGn_r',  # Red to Green (reversed)
            title='Top 10 Companies by Environmental Risk Score'
        )
        
        fig.update_layout(
            yaxis=dict(title='Company'),
            xaxis=dict(title='Risk Score (0-100)'),
            coloraxis_showscale=False
        )
        
        # Add annotations for sanctioned companies
        for i, row in df.iterrows():
            if row['sanctioned']:
                fig.add_annotation(
                    x=row['risk_score'],
                    y=row['name'],
                    text="🚨",
                    showarrow=False,
                    xshift=20
                )
        
        logger.info("Risk bar chart created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating risk chart: {str(e)}")
        return create_empty_chart("Error creating chart")

def create_empty_graph(message: str) -> go.Figure:
    """Create empty graph placeholder"""
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        annotations=[dict(
            text=message,
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig

def create_empty_chart(message: str) -> go.Figure:
    """Create empty chart with message"""
    fig = go.Figure()
    fig.update_layout(
        title=message,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        annotations=[dict(
            text=message,
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig