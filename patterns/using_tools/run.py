from .graph import answer_question


def main() -> None:
    question = "What is the square of the average of 10 and 5?"
    result = answer_question(question)
    print(f"Question: {question}")
    print(f"Route: {result.get('route', 'general')}")
    print(result.get("answer", "No answer was returned."))


if __name__ == "__main__":
    main()