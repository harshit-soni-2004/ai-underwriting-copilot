"""
Synthetic MSME Applicant and Document Generator.
Generates reproducible test applicants with bank statements, invoices, and GST filings.
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic MSME applicant data")
    parser.add_argument("--applicants", type=int, default=10, help="Number of applicants to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    print(f"Synthetic generator ready (Phase 1). Seed: {args.seed}, Target: {args.applicants} applicants.")

if __name__ == "__main__":
    main()
