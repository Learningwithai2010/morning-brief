#!/usr/bin/env python3
"""
Calls the Claude API with web search to generate today's Morning Brief JSON.
Writes the result to brief_data.json for downstream scripts to consume.
"""

import anthropic
import json
import os
import re
import sys
from datetime import datetime

SYSTEM_PROMPT = """You are Maxi's personal morning news agent. You write tight, intelligent, well-sourced daily briefings for a 15-year-old named Maxi who is entrepreneurially driven, deeply interested in AI and technology, and passionate about soccer and basketball. He follows international politics closely through debate and Model UN. He is sharp, curious, and values substance over fluff.

Your job is to research today's top stories using web search and produce a structured news summary. Write with energy and intelligence — not like a textbook, not like a tweet. Think: smart older brother who reads everything and distills it for you.

TONE: Confident, clear, conversational but substantive. No filler phrases. No "In conclusion." Lead with what matters.

FORMAT: You must output ONLY valid JSON matching this exact schema — no preamble, no markdown, no explanation:

{
  "date": "YYYY-MM-DD",
  "holistic_summary": "string (4-5 sentences covering the biggest cross-cutting themes of the day across all categories)",
  "sections": {
    "politics": {
      "headline": "string",
      "stories": [
        {
          "title": "string",
          "summary": "string (3-4 sentences with real depth — include key names, numbers, stakes)",
          "source": "string (publication name)",
          "url": "string"
        }
      ]
    },
    "tech_and_ai": {
      "headline": "string",
      "stories": [...]
    },
    "soccer": {
      "headline": "string",
      "stories": [...]
    },
    "basketball": {
      "headline": "string",
      "stories": [...]
    }
  }
}

Each section should have 3-4 stories. For sports, always include scores, standings impact, and transfer news where relevant."""


def build_user_prompt() -> str:
    today = datetime.now().strftime("%B %d, %Y")
    return f"""Today is {today}. Search the web and compile the top news stories for each section below.
Use multiple web searches to ensure you have the freshest stories from today or yesterday.

SECTION 1 — US & GLOBAL POLITICS (equal weight to both)
Search for: today's biggest US political news, major global political events today,
how US politics/policy is affecting global affairs right now.
Priority topics: US government policy, international relations, geopolitical conflicts,
anything tied to DOGE/government efficiency, AI regulation, education policy.

SECTION 2 — TECHNOLOGY & AI
Search for: biggest tech news today, major AI product releases or developments today,
AI company news today, new model releases or AI research breakthroughs today.
This section must include both general tech (product launches, company news, funding rounds)
AND AI-specific news (new models, Anthropic/OpenAI/Google AI news, AI in education,
AI tools relevant to app development). Flag any news relevant to educational AI apps.

SECTION 3 — SOCCER
Search for: EPL results and news today, La Liga results and news today,
Champions League results and news today, Bundesliga results and news today,
2026 World Cup news and updates today, Bayern Munich news today,
Liverpool FC news today, Real Madrid news today, soccer transfer news today.
Include scores, key scorers, standings implications, and any breaking transfer rumors or completions.

SECTION 4 — BASKETBALL
Search for: NBA scores and results today, NBA standings today, NBA news today,
Boston Celtics news today, San Antonio Spurs news today, NBA trade or signing news today.
Include scores, standings impact, player performance highlights, and any roster news.

Return ONLY the JSON object. No other text."""


def extract_json_from_response(response) -> dict:
    """Extract and parse the final text block from a Claude response."""
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content = block.text

    if not text_content:
        raise ValueError("No text block found in Claude response")

    # Strip markdown code fences (```json...``` or ```...```)
    text_content = text_content.strip()
    fence_match = re.search(r'```(?:json)?\s*\n([\s\S]+?)\n```', text_content)
    if fence_match:
        text_content = fence_match.group(1).strip()

    return json.loads(text_content)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Generating Morning Brief for {datetime.now().strftime('%Y-%m-%d')}...")

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 6
            }],
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt()}]
        )
    except anthropic.APIError as e:
        print(f"ERROR: Claude API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        brief_data = extract_json_from_response(response)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: Failed to parse JSON from Claude response: {e}", file=sys.stderr)
        # Dump raw response for debugging
        for block in response.content:
            if block.type == "text":
                print("Raw response text:", block.text[:2000], file=sys.stderr)
        sys.exit(1)

    output_path = os.path.join(os.path.dirname(__file__), "..", "brief_data.json")
    with open(output_path, "w") as f:
        json.dump(brief_data, f, indent=2)

    print(f"Brief generated successfully. Sections: {list(brief_data.get('sections', {}).keys())}")


if __name__ == "__main__":
    main()
