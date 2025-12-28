def print_report(results):
    print("\n🩺 PyProject Doctor Report\n")

    for r in results:
        status = "✅" if r["ok"] else "❌"
        print(f"{status} {r['title']}")
        if not r["ok"]:
            print("   Reason:", r["reason"])
            print("   Fix:")
            for f in r["fix"]:
                print("    ", f)
        print()

    fails = [r for r in results if not r["ok"]]
    if fails:
        print("Summary:")
        for i, r in enumerate(fails, 1):
            print(f"{i}. {r['title']}")
    else:
        print("🎉 No issues found")
