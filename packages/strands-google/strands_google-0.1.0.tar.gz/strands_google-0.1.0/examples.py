#!/usr/bin/env python3
"""Example usage of strands-google tools."""

from strands import Agent
from strands_google import use_google, gmail_send, gmail_reply, google_auth

# Create agent with Google tools
agent = Agent(tools=[use_google, gmail_send, gmail_reply, google_auth])

# Example 1: Authenticate (run this first!)
# This will open your browser and generate gmail_token.json
# Uncomment to run:
# agent("Run google_auth to authenticate my Gmail account")

# Example 2: List Gmail messages
# agent("Show me my 5 most recent Gmail messages")

# Example 3: Send an email
# agent("Send an email to test@example.com with subject 'Hello' and body 'Test message'")

# Example 4: Search Drive files
# agent("List my 10 most recent Google Drive files")

# Example 5: List Calendar events
# agent("Show me my upcoming calendar events for this week")

# Example 6: YouTube search with API key
# agent("Search YouTube for 'python programming' videos")

# Example 7: Direct tool usage
# result = agent.tool.use_google(
#     service="gmail",
#     version="v1",
#     resource="users.messages",
#     method="list",
#     parameters={"userId": "me", "maxResults": 5}
# )
# print(result)

# Example 8: Send email directly
# result = agent.tool.gmail_send(
#     to="friend@example.com",
#     subject="Test",
#     body="This is a test email from strands-google"
# )
# print(result)

print("strands-google examples loaded!")
print("Edit this file to uncomment and run examples.")

while True:
    agent(input("\n# "))
