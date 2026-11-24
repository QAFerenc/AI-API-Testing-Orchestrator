import asyncio
import sys


async def main():

    from orchestrator import run_orchestrator

    print("=" * 60)
    print("AI API TESTING ORCHESTRATOR")
    print("=" * 60)

    result = await run_orchestrator()

    summary = result["report"]["summary"]

    print("\nEXECUTION SUMMARY")
    print("=" * 60)

    print("Execution ID:", result["execution_id"])

    print("Status:", result["status"])

    print("Original tests:", summary["original_tests"])

    print("Recovered tests:", summary["recovered_tests"])

    print("Unresolved failures:", summary["unresolved_failures"])

    print(
        "Final pass rate:",
        summary["final_pass_rate_percent"],
        "%"
    )

    print(
        "Total duration:",
        round(result["total_duration_seconds"], 2),
        "seconds"
    )

    print("\nGENERATED REPORTS")
    print("=" * 60)

    artifacts = result["artifacts"]

    print("JSON report:", artifacts["json_report"])

    print("HTML report:", artifacts["html_report"])

    print("Visual report:", artifacts["visual_html_report"])

    for name, path in artifacts["charts"].items():

        print(name + ":", path)

    return 0 if result["status"] == "PASSED" else 1


if __name__ == "__main__":

    try:

        exit_code = asyncio.run(main())

    except KeyboardInterrupt:

        print("Execution interrupted.")

        exit_code = 130

    except Exception as error:

        print(
            "Execution failed:",
            type(error).__name__,
            file=sys.stderr
        )

        exit_code = 1

    sys.exit(exit_code)
