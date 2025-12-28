import argparse

from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.environments.chat_env import ChatEnv


def build_env(task: str | None, working_dir: str | None) -> ChatEnv:
    return ChatEnv(task=task or "", working_directory=working_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WBAL chat agent")
    parser.add_argument("--task", type=str, default="", help="Task for the agent")
    parser.add_argument("--working-dir", type=str, default=None, help="Directory for state persistence")
    parser.add_argument("--max-steps", type=int, default=None, help="Max steps before stopping")
    parser.add_argument("--org", type=str, default="", help="Organization name (optional)")
    parser.add_argument("--project", type=str, required=True, help="Project name (required)")
    args = parser.parse_args()

    env_description = f"Org: {args.org}\nProject: {args.project}"
    env = build_env(args.task, args.working_dir)
    env.env = env_description
    agent = OpenAIWBAgent(env=env)
    agent.run(task=args.task, max_steps=args.max_steps)


if __name__ == "__main__":
    main()
