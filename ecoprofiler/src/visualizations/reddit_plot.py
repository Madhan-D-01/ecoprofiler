import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger("RedditVisualization")

def create_reddit_timeline(reddit_posts: pd.DataFrame) -> go.Figure:
    """Create timeline of Reddit post activity"""
    try:
        if reddit_posts.empty:
            return create_empty_timeline()
        
        # Convert created_utc to datetime
        posts_df = reddit_posts.copy()
        posts_df['created_dt'] = pd.to_datetime(posts_df['created_utc'], unit='s', errors='coerce')
        
        # Group by date
        daily_posts = posts_df.groupby(posts_df['created_dt'].dt.date).agg({
            'id': 'count',
            'score': 'sum',
            'sentiment': 'mean'
        }).reset_index()
        
        daily_posts.columns = ['date', 'post_count', 'total_score', 'avg_sentiment']
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add post count bars
        fig.add_trace(go.Bar(
            x=daily_posts['date'],
            y=daily_posts['post_count'],
            name='Post Count',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        # Add sentiment line
        fig.add_trace(go.Scatter(
            x=daily_posts['date'],
            y=daily_posts['avg_sentiment'],
            name='Avg Sentiment',
            line=dict(color='red', width=3),
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title='Reddit Activity Timeline',
            xaxis=dict(title='Date'),
            yaxis=dict(
                title='Number of Posts',
                side='left',
                titlefont=dict(color='lightblue'),
                tickfont=dict(color='lightblue')
            ),
            yaxis2=dict(
                title='Average Sentiment',
                side='right',
                overlaying='y',
                range=[-1, 1],
                titlefont=dict(color='red'),
                tickfont=dict(color='red')
            ),
            legend=dict(x=0, y=1.1, orientation='h')
        )
        
        logger.info("Reddit timeline created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating Reddit timeline: {str(e)}")
        return create_empty_timeline()

def create_sentiment_chart(reddit_posts: pd.DataFrame) -> go.Figure:
    """Create sentiment distribution chart"""
    try:
        if reddit_posts.empty:
            return create_empty_sentiment_chart()
        
        # Categorize sentiment
        def categorize_sentiment(score):
            if score > 0.1:
                return 'Positive'
            elif score < -0.1:
                return 'Negative'
            else:
                return 'Neutral'
        
        posts_df = reddit_posts.copy()
        posts_df['sentiment_category'] = posts_df['sentiment'].apply(categorize_sentiment)
        
        sentiment_counts = posts_df['sentiment_category'].value_counts()
        
        # Create pie chart
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title='Reddit Post Sentiment Distribution',
            color=sentiment_counts.index,
            color_discrete_map={
                'Positive': 'green',
                'Neutral': 'gray', 
                'Negative': 'red'
            }
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        logger.info("Sentiment chart created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating sentiment chart: {str(e)}")
        return create_empty_sentiment_chart()

def create_subreddit_breakdown(reddit_posts: pd.DataFrame) -> go.Figure:
    """Create breakdown of posts by subreddit"""
    try:
        if reddit_posts.empty:
            return create_empty_breakdown_chart()
        
        subreddit_counts = reddit_posts['subreddit'].value_counts().head(10)  # Top 10
        
        fig = px.bar(
            x=subreddit_counts.values,
            y=subreddit_counts.index,
            orientation='h',
            title='Top 10 Subreddits by Post Count',
            labels={'x': 'Number of Posts', 'y': 'Subreddit'}
        )
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        logger.info("Subreddit breakdown created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating subreddit breakdown: {str(e)}")
        return create_empty_breakdown_chart()

def create_engagement_scatter(reddit_posts: pd.DataFrame) -> go.Figure:
    """Create scatter plot of engagement vs sentiment"""
    try:
        if reddit_posts.empty:
            return create_empty_scatter()
        
        fig = px.scatter(
            reddit_posts,
            x='sentiment',
            y='score',
            size='num_comments',
            color='sentiment',
            color_continuous_scale='RdYlGn',
            title='Post Engagement vs Sentiment',
            labels={
                'sentiment': 'Sentiment Score',
                'score': 'Post Score (Upvotes)',
                'num_comments': 'Number of Comments'
            },
            hover_data=['title']
        )
        
        # Add reference lines
        fig.add_vline(x=-0.1, line_dash="dash", line_color="red")
        fig.add_vline(x=0.1, line_dash="dash", line_color="green")
        
        logger.info("Engagement scatter plot created successfully")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating engagement scatter: {str(e)}")
        return create_empty_scatter()

def create_empty_timeline() -> go.Figure:
    """Create empty timeline placeholder"""
    fig = go.Figure()
    fig.update_layout(
        title="No Reddit Data Available",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        annotations=[dict(
            text="No Reddit post data available for timeline",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig

def create_empty_sentiment_chart() -> go.Figure:
    """Create empty sentiment chart placeholder"""
    fig = go.Figure()
    fig.update_layout(
        title="No Sentiment Data Available",
        annotations=[dict(
            text="No sentiment data available",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig

def create_empty_breakdown_chart() -> go.Figure:
    """Create empty breakdown chart placeholder"""
    fig = go.Figure()
    fig.update_layout(
        title="No Subreddit Data Available",
        xaxis=dict(title="Number of Posts"),
        yaxis=dict(title="Subreddit"),
        annotations=[dict(
            text="No subreddit data available",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig

def create_empty_scatter() -> go.Figure:
    """Create empty scatter plot placeholder"""
    fig = go.Figure()
    fig.update_layout(
        title="No Engagement Data Available",
        xaxis=dict(title="Sentiment"),
        yaxis=dict(title="Post Score"),
        annotations=[dict(
            text="No engagement data available",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14)
        )]
    )
    return fig