from Digital_India_Act import run_accessbility_check


def main():
    results = run_accessbility_check(
        "https://kalavriddhi-frontend-6cyz.onrender.com/"
    )

    print("\n-- Accessibility check results ---\n")

    for r in results:
        print(f"URL: {r['url']}")
        print(f"Overall Status: {r['overall_status']}")
        print(f"Rule-based Violations: {r['rule_violation_count']}")
        print(f"Semantic Findings: {r['semantic_issue_count']}")

        if r["rule_violation_count"] > 0:
            print("  Rule Violations:")
            for v in r["rule_violations"]:
                print(
                    f"    - [{v['impact']}] {v['description']} "
                    f"(WCAG: {', '.join(v['wcag'])})"
                )

        if r["semantic_issue_count"] > 0:
            print("  Semantic Findings:")
            for s in r["semantic_findings"]:
                print(
                    f"    - [{s['severity']}] {s['issue']} "
                    f"({s['component']})"
                )

        print("-" * 60)


if __name__ == "__main__":
    main()
