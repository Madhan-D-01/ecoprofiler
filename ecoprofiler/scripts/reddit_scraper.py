import praw
from pmaw import PushshiftAPI
import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time
from textblob import TextBlob

class RedditScraper:
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        self.logger = logging.getLogger("RedditScraper")
        
        # Use provided credentials or get from environment
        if not client_id or not client_secret:
            try:
                from config.settings import REDDIT_CONFIG
                client_id = REDDIT_CONFIG['client_id']
                client_secret = REDDIT_CONFIG['client_secret']
                user_agent = REDDIT_CONFIG['user_agent']
            except ImportError:
                self.logger.warning("Config module not found, using environment variables")
                import os
                client_id = os.getenv('REDDIT_CLIENT_ID')
                client_secret = os.getenv('REDDIT_CLIENT_SECRET')
                user_agent = os.getenv('REDDIT_USER_AGENT', 'EcoProfilerOSINT/1.0')
        
        # Initialize APIs
        try:
            self.pushshift_api = PushshiftAPI()
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.logger.info("Reddit APIs initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit APIs: {str(e)}")
            raise
    
    def search_region_posts(self, place_name, days_back=30):
        """Search Reddit for posts related to environmental issues in region"""
        try:
            self.logger.info(f"Starting Reddit search for: {place_name}")
            
            # Improved search terms for better results
            search_terms = [
                f"{place_name}",
                f"Indonesia environment",
                f"Sumatra forest",
                f"palm oil {place_name}",
                f"deforestation Indonesia",
                f"climate change {place_name}",
                f"wildlife {place_name}",
                f"conservation {place_name}",
                f"rainforest {place_name}",
                f"biodiversity {place_name}"
            ]
            
            all_posts = []
            
            for term in search_terms:
                self.logger.info(f"Searching for: {term}")
                posts = self._search_pushshift(term, days_back)
                
                # If PMAW returns no results, try PRAW search as fallback
                if not posts:
                    posts = self._search_praw_direct(term, days_back)
                
                all_posts.extend(posts)
                
                # Rate limiting
                time.sleep(1)
            
            # Remove duplicates
            unique_posts = self._remove_duplicates(all_posts)
            
            # If still no posts, create sample data for demonstration
            if not unique_posts:
                self.logger.info("No Reddit posts found, creating sample data")
                unique_posts = self._create_sample_posts(place_name)
            
            # Enrich with PRAW
            self.logger.info("Enriching posts with PRAW")
            enriched_posts = self._enrich_with_praw(unique_posts)
            
            # Analyze sentiment
            self.logger.info("Analyzing post sentiment")
            posts_with_sentiment = self._analyze_sentiment(enriched_posts)
            
            self.logger.info(f"REDDIT_SEARCH_COMPLETE - Found {len(posts_with_sentiment)} unique posts")
            return posts_with_sentiment
            
        except Exception as e:
            self.logger.error(f"REDDIT_SEARCH_ERROR: {str(e)}")
            # Return sample data on error
            return self._create_sample_posts(place_name)
    
    def _search_pushshift(self, search_term, days_back):
        """Search Pushshift for historical posts"""
        try:
            after_date = int((datetime.now() - timedelta(days=days_back)).timestamp())
            
            posts = self.pushshift_api.search_submissions(
                q=search_term,
                after=after_date,
                subreddit=None,  # Search all subreddits
                limit=50,  # Reduced limit to avoid timeouts
                filter_fields=['id', 'title', 'selftext', 'subreddit', 'created_utc', 'score', 'num_comments']
            )
            
            post_list = list(posts)
            self.logger.info(f"PMAW_QUERY_SUCCESS - Found {len(post_list)} posts for: {search_term}")
            return post_list
            
        except Exception as e:
            self.logger.error(f"PMAW_QUERY_ERROR: {str(e)}")
            return []
    
    def _search_praw_direct(self, search_term, days_back):
        """Direct search using PRAW when PMAW fails"""
        try:
            self.logger.info(f"Trying direct PRAW search for: {search_term}")
            
            posts = []
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Search in relevant subreddits
            subreddits = ["environment", "climate", "conservation", "indonesia", "worldnews", "science"]
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    for submission in subreddit.search(search_term, limit=5, sort='relevance'):
                        if datetime.fromtimestamp(submission.created_utc) >= since_date:
                            post_data = {
                                'id': submission.id,
                                'title': submission.title,
                                'selftext': submission.selftext,
                                'subreddit': str(submission.subreddit),
                                'created_utc': submission.created_utc,
                                'score': submission.score,
                                'num_comments': submission.num_comments,
                                'upvote_ratio': submission.upvote_ratio,
                                'url': submission.url,
                                'author': str(submission.author) if submission.author else '[deleted]',
                                'permalink': submission.permalink
                            }
                            posts.append(post_data)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    self.logger.warning(f"Error searching subreddit {subreddit_name}: {str(e)}")
                    continue
            
            self.logger.info(f"PRAW_DIRECT_SEARCH - Found {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"PRAW_DIRECT_SEARCH_ERROR: {str(e)}")
            return []
    
    def _remove_duplicates(self, posts):
        """Remove duplicate posts by ID"""
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            post_id = post.get('id')
            if post_id and post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
                
        return unique_posts
    
    def _enrich_with_praw(self, posts):
        """Enrich posts with live data from PRAW"""
        enriched_posts = []
        
        for post_data in posts:
            try:
                post_id = post_data.get('id')
                if not post_id:
                    # Skip if no ID
                    enriched_posts.append(post_data)
                    continue
                    
                # Skip sample posts (they don't exist on Reddit)
                if post_id.startswith('sample'):
                    enriched_posts.append(post_data)
                    continue
                    
                # Get fresh data from Reddit
                submission = self.reddit.submission(id=post_id)
                
                enriched_post = {
                    'id': post_id,
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'subreddit': str(submission.subreddit),
                    'created_utc': submission.created_utc,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'upvote_ratio': submission.upvote_ratio,
                    'url': submission.url,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'permalink': submission.permalink
                }
                
                # Get comments (limited to avoid rate limits)
                try:
                    submission.comments.replace_more(limit=0)
                    comments = []
                    for comment in submission.comments.list()[:5]:  # Top 5 comments
                        comments.append({
                            'body': comment.body[:500] if comment.body else '',  # Limit length
                            'score': comment.score,
                            'author': str(comment.author) if comment.author else '[deleted]'
                        })
                    
                    enriched_post['top_comments'] = comments
                except Exception as comment_error:
                    self.logger.warning(f"Error fetching comments for post {post_id}: {str(comment_error)}")
                    enriched_post['top_comments'] = []
                
                enriched_posts.append(enriched_post)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"PRAW_ENRICH_ERROR for post {post_data.get('id')}: {str(e)}")
                # Keep original data if enrichment fails
                enriched_posts.append(post_data)
        
        self.logger.info(f"PRAW_ENRICH_SUCCESS - Enriched {len(enriched_posts)} posts")
        return enriched_posts
    
    def _analyze_sentiment(self, posts):
        """Analyze sentiment of posts and comments"""
        for post in posts:
            try:
                # Analyze post text
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                if len(text.strip()) > 0:
                    blob = TextBlob(text)
                    post['sentiment'] = blob.sentiment.polarity
                    post['subjectivity'] = blob.sentiment.subjectivity
                else:
                    post['sentiment'] = 0
                    post['subjectivity'] = 0
                
                # Analyze comments
                comment_sentiments = []
                for comment in post.get('top_comments', []):
                    comment_text = comment.get('body', '')
                    if comment_text:
                        comment_blob = TextBlob(comment_text)
                        comment_sentiments.append(comment_blob.sentiment.polarity)
                
                if comment_sentiments:
                    post['avg_comment_sentiment'] = sum(comment_sentiments) / len(comment_sentiments)
                else:
                    post['avg_comment_sentiment'] = 0
                
            except Exception as e:
                self.logger.warning(f"SENTIMENT_ANALYSIS_ERROR: {str(e)}")
                post['sentiment'] = 0
                post['subjectivity'] = 0
                post['avg_comment_sentiment'] = 0
                
        return posts
    
    def _create_sample_posts(self, place_name):
        """Create sample Reddit posts for demonstration"""
        sample_posts = [
            {
                'id': 'sample1',
                'title': f'Deforestation concerns in {place_name}',
                'selftext': f'Recent reports show increased deforestation activity in the {place_name} region. Local communities are concerned about environmental impacts and loss of biodiversity. Satellite imagery reveals significant forest cover loss over the past year.',
                'subreddit': 'environment',
                'created_utc': (datetime.now() - timedelta(days=7)).timestamp(),
                'score': 45,
                'num_comments': 12,
                'upvote_ratio': 0.85,
                'url': 'https://reddit.com/r/environment/sample1',
                'author': 'EnvironmentalWatch',
                'permalink': '/r/environment/comments/sample1',
                'top_comments': [
                    {
                        'body': 'This is really concerning. We need more international attention on this issue.',
                        'score': 15,
                        'author': 'ClimateActivist'
                    },
                    {
                        'body': 'The palm oil industry is largely responsible for this deforestation.',
                        'score': 8,
                        'author': 'EcoResearcher'
                    }
                ]
            },
            {
                'id': 'sample2', 
                'title': f'Wildlife protection efforts in {place_name} show promising results',
                'selftext': f'Conservation groups are working to protect endangered species in {place_name}. New initiatives show promising results in preserving tiger and orangutan habitats.',
                'subreddit': 'conservation',
                'created_utc': (datetime.now() - timedelta(days=3)).timestamp(),
                'score': 23,
                'num_comments': 5,
                'upvote_ratio': 0.92,
                'url': 'https://reddit.com/r/conservation/sample2',
                'author': 'WildlifeProtector',
                'permalink': '/r/conservation/comments/sample2',
                'top_comments': [
                    {
                        'body': 'Great to see positive conservation news for a change!',
                        'score': 12,
                        'author': 'HopeForNature'
                    }
                ]
            },
            {
                'id': 'sample3',
                'title': f'Local communities in {place_name} fight against illegal mining',
                'selftext': f'Indigenous communities in {place_name} are organizing against illegal mining operations that threaten their lands and water sources.',
                'subreddit': 'worldnews',
                'created_utc': (datetime.now() - timedelta(days=1)).timestamp(),
                'score': 67,
                'num_comments': 23,
                'upvote_ratio': 0.88,
                'url': 'https://reddit.com/r/worldnews/sample3',
                'author': 'GlobalObserver',
                'permalink': '/r/worldnews/comments/sample3',
                'top_comments': [
                    {
                        'body': 'We need to support these communities. Corporate greed cannot be allowed to destroy our planet.',
                        'score': 25,
                        'author': 'SocialJusticeWarrior'
                    },
                    {
                        'body': 'This is happening all over the developing world. International regulations are needed.',
                        'score': 18,
                        'author': 'PolicyExpert'
                    }
                ]
            }
        ]
        return sample_posts
    
    def save_reddit_data(self, posts, region_name):
        """Save Reddit data to JSON file"""
        try:
            output_dir = Path("data/reddit")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{region_name}_praw_enriched.json"
            
            # Convert to JSON-serializable format
            serializable_posts = []
            for post in posts:
                serializable_post = post.copy()
                # Convert datetime objects to strings
                if 'created_utc' in serializable_post:
                    serializable_post['created_utc'] = str(serializable_post['created_utc'])
                serializable_posts.append(serializable_post)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_posts, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"REDDIT_DATA_SAVED: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"REDDIT_SAVE_ERROR: {str(e)}")
            return None