from __future__ import annotations
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from tools.send_email import send_email
from tools.retrieve_emails import retrieve_emails

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

set_tracing_disabled(disabled=True)

MODEL = 'gemini/gemini-2.0-flash'
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY 


agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. You can send emails using the send_email tool and retrieve emails from the inbox using the retrieve_emails tool when requested.",
    model=LitellmModel(model=MODEL),
    tools=[send_email, retrieve_emails]
)

async def main():
    counter = 0
    print("Welcome to the Assistant! Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        # Call Runner.run with await
        response = await Runner.run(agent, user_input)
        print(f"Assistant: {response.final_output}")
        
        counter += 1
        print(f"You sent {counter} message(s)!")

if __name__ == "__main__":
    asyncio.run(main())




