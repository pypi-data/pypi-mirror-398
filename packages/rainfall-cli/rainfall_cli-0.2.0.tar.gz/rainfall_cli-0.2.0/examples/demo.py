"""
Example script demonstrating Rainfall.

Run with: rainfall examples/demo.py
"""


def calculate_tip(bill: float, service_quality: str) -> float:
    """
    Calculate the appropriate tip amount based on the bill and service quality.
    
    Args:
        bill: The total bill amount in dollars
        service_quality: One of 'poor', 'okay', 'good', 'excellent'
    
    Returns:
        The tip amount in dollars (not percentage)
    """
    ...


def is_palindrome(text: str) -> bool:
    """Check if the given text is a palindrome (ignoring case and spaces)."""
    ...


def extract_emails(text: str) -> list:
    """
    Extract all email addresses from the given text.
    Returns a list of email address strings.
    """
    ...


def summarize(text: str, max_words: int = 30) -> str:
    """
    Summarize the given text in approximately the specified number of words.
    Keep the main ideas but make it concise.
    """
    ...


def analyze_sentiment(text: str) -> str:
    """
    Analyze the emotional sentiment of the text.
    
    Returns one of: 'positive', 'negative', 'neutral', 'mixed'
    
    Examples:
        "I love this product!" → 'positive'
        "This is terrible." → 'negative'
        "It's okay I guess." → 'neutral'
    """
    ...


# ============ Demo ============

if __name__ == "__main__":
    print("=" * 50)
    print("🌧️  Rainfall Demo")
    print("=" * 50)
    
    # Test calculate_tip
    print("\n📝 Calculate Tip:")
    tip = calculate_tip(85.50, "excellent")
    print(f"   $85.50 bill, excellent service → ${tip} tip")
    
    # Test is_palindrome
    print("\n📝 Palindrome Check:")
    print(f"   'racecar' → {is_palindrome('racecar')}")
    print(f"   'hello' → {is_palindrome('hello')}")
    print(f"   'A man a plan a canal Panama' → {is_palindrome('A man a plan a canal Panama')}")
    
    # Test extract_emails
    print("\n📝 Extract Emails:")
    text = "Contact us at support@example.com or sales@company.org for help."
    emails = extract_emails(text)
    print(f"   Found: {emails}")
    
    # Test summarize
    print("\n📝 Summarize Text:")
    long_text = """
    Artificial intelligence has transformed the way we interact with technology.
    From virtual assistants to recommendation systems, AI is everywhere.
    Machine learning algorithms can now recognize images, understand speech,
    and even generate human-like text. The future holds promise with
    developments in autonomous vehicles, medical diagnosis, and scientific research.
    """
    summary = summarize(long_text)
    print(f"   {summary}")
    
    # Test sentiment analysis
    print("\n📝 Sentiment Analysis:")
    print(f"   'I absolutely love this!' → {analyze_sentiment('I absolutely love this!')}")
    print(f"   'This is the worst.' → {analyze_sentiment('This is the worst.')}")
    print(f"   'It works fine.' → {analyze_sentiment('It works fine.')}")
    
    print("\n" + "=" * 50)
    print("✅ Demo complete!")
    print("=" * 50)
