"""Inspect what Windows exposes from an open FORScan application."""

from forscan_reader import ForscanReaderError, inspect_open_forscan


def main():
    print("OBD-Insight FORScan read-only probe")
    print("This does not click or change anything in FORScan.\n")

    found_window = False
    for backend in ("uia", "win32"):
        print(f"Checking Windows backend: {backend}")
        try:
            inspection = inspect_open_forscan(backend=backend)
        except ForscanReaderError as error:
            print(f"  {error}\n")
            continue

        found_window = True
        print(f"  Window: {inspection.window_title}")
        print(f"  Controls visible to Windows: {len(inspection.controls)}")
        print(f"  Possible log controls: {len(inspection.log_candidates)}")

        for control in inspection.log_candidates:
            preview = " ".join(control.text.split())[:240]
            print(
                f"  Candidate #{control.index}: "
                f"type={control.control_type or 'Unknown'}, "
                f"class={control.class_name or 'Unknown'}"
            )
            print(f"    {preview}")

        if not inspection.log_candidates:
            print("  No Vehicle, Found module, or DTC text was exposed.")
            print("  First visible controls:")
            for control in inspection.controls[:25]:
                label = control.name or " ".join(control.text.split())[:80] or "(no text)"
                print(
                    f"    #{control.index} "
                    f"{control.control_type or 'Unknown'} | "
                    f"{control.class_name or 'Unknown'} | {label}"
                )
        print()

    if not found_window:
        print("Open FORScan, leave its Log tab visible, and run this probe again.")


if __name__ == "__main__":
    main()
