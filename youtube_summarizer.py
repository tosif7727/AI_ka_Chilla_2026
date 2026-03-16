"""
Minimal YouTube Video Summarizer with LangChain
Paste a YouTube URL, get summary + key points + ask follow-up questions
"""

from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript(video_id):
    """Fetch transcript from YouTube video"""
    try:
        ytt_api = YouTubeTranscriptApi()
        
        # First, list what transcripts are available
        try:
            transcript_list = ytt_api.list(video_id)
            available_transcripts = list(transcript_list)
            
            if not available_transcripts:
                return "Error: No transcripts available for this video"
            
            # Try to find any available transcript (manual or auto-generated)
            for lang in ['en', 'en-US', 'en-GB', 'a.en']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    data = transcript.fetch()
                    return ' '.join([entry.text for entry in data])
                except:
                    continue
            
            # If specific languages fail, take first available
            transcript = available_transcripts[0]
            data = transcript.fetch()
            return ' '.join([entry.text for entry in data])
            
        except Exception as list_error:
            # Fallback: try direct fetch with common languages
            try:
                transcript = ytt_api.fetch(video_id, languages=['en', 'en-US', 'en-GB', 'es', 'fr', 'de', 'auto'])
                return ' '.join([entry.text for entry in transcript])
            except:
                return f"Error: No transcripts available for this video"
                
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_video(url, api_key):
    """Main function to summarize YouTube video"""
    
    # Get video ID and transcript
    video_id = get_video_id(url)
    if not video_id:
        return "Invalid YouTube URL"
    
    print(f"📹 Fetching transcript for video ID: {video_id}...")
    transcript = get_transcript(video_id)
    
    if transcript.startswith("Error"):
        return transcript
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-5-mini", api_key=api_key)

    
    # Create summary prompt
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes YouTube videos concisely."),
        ("user", """Analyze this video transcript and provide:

1. **Summary** (2-3 sentences)
2. **Key Points** (bullet points)
3. **Main Takeaways**

Transcript:
{transcript}""")
    ])
    
    # Generate summary
    print("🤖 Generating summary...")
    chain = summary_prompt | llm
    response = chain.invoke({"transcript": transcript})
    
    return response.content, transcript, llm

def ask_question(question, transcript, llm):
    """Ask follow-up questions about the video"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant answering questions about a YouTube video transcript."),
        ("user", """Based on this video transcript, answer the question:

Question: {question}

Transcript:
{transcript}""")
    ])
    
    chain = qa_prompt | llm
    response = chain.invoke({"question": question, "transcript": transcript})
    return response.content

# Example usage
if __name__ == "__main__":
    # Get API key
    api_key = input("Enter your Anthropic API key: ").strip()
    
    # Get YouTube URL
    url = input("\n📺 Enter YouTube URL: ").strip()
    
    # Summarize
    result = summarize_video(url, api_key)
    
    if isinstance(result, tuple):
        summary, transcript, llm = result
        print("\n" + "="*60)
        print(summary)
        print("="*60)
        
        # Follow-up questions
        while True:
            question = input("\n❓ Ask a question (or 'quit' to exit): ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            answer = ask_question(question, transcript, llm)
            print(f"\n💡 {answer}")
    else:
        print(result)