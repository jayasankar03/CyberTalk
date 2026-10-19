
import asyncio

from agreement_evaluator import evaluate_agreement


async def main():
    topic = (
        "Implement multi-factor authentication for remote access "
        "without unnecessarily disrupting IT operations."
    )

    transcript = [
        {
            "turn": 1,
            "speaker": "Security Officer",
            "message": (
                "Multi-factor authentication is necessary to reduce "
                "the risk of compromised accounts. I recommend enabling "
                "it for all remote access within two weeks."
            ),
        },
        {
            "turn": 1,
            "speaker": "IT Operations Manager",
            "message": (
                "I support multi-factor authentication, but an immediate "
                "rollout could disrupt users. I propose a pilot first, "
                "followed by a phased rollout over two weeks."
            ),
        },
        {
            "turn": 2,
            "speaker": "Security Officer",
            "message": (
                "I agree to a pilot followed by a phased rollout, "
                "provided all remote-access accounts are covered by "
                "the end of the two-week period."
            ),
        },
        {
            "turn": 2,
            "speaker": "IT Operations Manager",
            "message": (
                "Agreed. We will run the pilot, monitor operational "
                "issues, and complete the rollout within two weeks."
            ),
        },
    ]

    result = await evaluate_agreement(topic, transcript)

    print("\n--- Agreement Evaluation Result ---")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
