import gradio as gr

from generate import generate

def chat(message: str, history: list) -> str:
    return generate(message)


demo = gr.ChatInterface(
    fn=chat,
    title="UMD Dining Guide",
    description="Ask anything about UMD dining halls, meal plans, hours, prices, and more.",
    examples=[
        "What is the door price for a student dinner?",
        "What should I do if I'm too sick to go to a dining hall?",
        "What is the difference between a Resident Plan and a Connector Plan?",
        "Is a meal plan cheaper than buying food on my own as a commuter?",
        "What are Dining Dollars and how do I get them?",
    ],
)

if __name__ == "__main__":
    demo.launch(server_port=7680)
