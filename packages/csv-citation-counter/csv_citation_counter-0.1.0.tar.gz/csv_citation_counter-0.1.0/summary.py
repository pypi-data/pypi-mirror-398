import csv
from collections import Counter, defaultdict
import argparse
import os

def count_column_entries_with_citations(file_paths, column_name, citation_column, split_delimiter=None):
    article_counter = Counter()
    citation_counter = Counter()
    max_citation_tracker = defaultdict(int)

    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"Warning: File not found: {file_path}")
            continue

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            if column_name not in reader.fieldnames:
                print(f"Warning: Column '{column_name}' not found in '{file_path}'. Skipping.")
                continue
            if citation_column not in reader.fieldnames:
                print(f"Warning: Citation column '{citation_column}' not found in '{file_path}'. Skipping.")
                continue

            for row in reader:
                entry = row.get(column_name)
                citation_value = row.get(citation_column, "0").strip()
                try:
                    citations = int(citation_value) if citation_value else 0
                except ValueError:
                    citations = 0

                if entry:
                    if split_delimiter:
                        items = [item.strip() for item in entry.split(split_delimiter) if item.strip()]
                        article_counter.update(items)
                        for item in items:
                            citation_counter[item] += citations
                            max_citation_tracker[item] = max(max_citation_tracker[item], citations)
                    else:
                        name = entry.strip()
                        article_counter[name] += 1
                        citation_counter[name] += citations
                        max_citation_tracker[name] = max(max_citation_tracker[name], citations)

    return article_counter, citation_counter, max_citation_tracker

def prompt_file_paths():
    print("Enter file paths or folder names one per line. Press Enter on an empty line to finish.\n")
    file_paths = []
    while True:
        user_input = input("File or folder path: ").strip()
        if not user_input:
            break
        if os.path.isdir(user_input):
            csv_files = [os.path.join(user_input, f) for f in os.listdir(user_input) if f.endswith('.csv')]
            if csv_files:
                print(f"Added {len(csv_files)} CSV file(s) from folder '{user_input}'")
                file_paths.extend(csv_files)
            else:
                print(f"No CSV files found in folder: {user_input}")
        elif os.path.isfile(user_input):
            file_paths.append(user_input)
        else:
            print(f"Path not found: {user_input}")
    return file_paths

def get_input_or_prompt(args):
    file_paths = args.files or prompt_file_paths()
    while not file_paths:
        print("No valid files were provided.")
        file_paths = prompt_file_paths()

    column_name = args.column or input("Enter the column name to analyze: ").strip()
    split_delimiter = args.split if args.split is not None else input("Enter a delimiter to split entries (leave blank if none): ").strip()
    split_delimiter = split_delimiter if split_delimiter else None

    print("\nSort options:\n"
          "  articles = by number of articles\n"
          "  total    = by total citations\n"
          "  avg      = by average citations per article")
    sort_by = args.sortby or input("Choose sort method [default: articles]: ").strip().lower()
    sort_by = sort_by if sort_by in {"articles", "total", "avg"} else "articles"

    return file_paths, column_name, split_delimiter, sort_by

def write_summary_output(article_counter, citation_counter, max_citation_tracker, output_path, sort_by):
    results = []
    for name in article_counter:
        articles = article_counter[name]
        total = citation_counter.get(name, 0)
        avg = total / articles if articles else 0
        max_cit = max_citation_tracker.get(name, 0)
        results.append((name, articles, total, avg, max_cit))

    if sort_by == "total":
        results.sort(key=lambda x: (-x[2], x[0]))  # sort by total citations
    elif sort_by == "avg":
        results.sort(key=lambda x: (-x[3], x[0]))  # sort by average citations
    else:
        results.sort(key=lambda x: (-x[1], x[0]))  # sort by number of articles

    with open(output_path, "w", encoding="utf-8") as f:
        prev_key = None
        for name, articles, total, avg, max_cit in results:
            key = {"articles": articles, "total": total, "avg": avg}[sort_by]
            if prev_key is not None and key != prev_key:
                f.write("\n")
            f.write(f"{name}: {articles} article(s), {total} total citations, {avg:.2f} avg, {max_cit} max\n")
            prev_key = key

    print(f"\n✅ Results written to {output_path}")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Count and summarize sources from CSV columns.")
    parser.add_argument("--files", nargs='+', help="List of CSV file paths or folder names")
    parser.add_argument("--column", help="Name of the column to analyze (e.g., Journal, Authors, etc.)")
    parser.add_argument("--split", help="Delimiter to split entries (e.g., '; ' for author lists)", default=None)
    parser.add_argument("--sortby", help="Sort by: articles (default), total (citations), or avg (average citations)")

    args = parser.parse_args(argv)
    file_paths, column_name, split_delimiter, sort_by = get_input_or_prompt(args)

    try:
        citation_column = "Cited by"
        article_counts, citation_counts, max_citation_counts = count_column_entries_with_citations(
            file_paths, column_name, citation_column, split_delimiter
        )

        sort_label = {
            "articles": "article count",
            "total": "total citations",
            "avg": "average citations"
        }[sort_by]

        print(f"\nTop 10 results sorted by {sort_label} (also saved to summary.txt):\n")
        preview = []
        for name in article_counts:
            total = citation_counts[name]
            count = article_counts[name]
            avg = total / count if count else 0
            max_cit = max_citation_counts[name]
            preview.append((name, count, total, avg, max_cit))

        if sort_by == "total":
            preview.sort(key=lambda x: (-x[2], x[0]))
        elif sort_by == "avg":
            preview.sort(key=lambda x: (-x[3], x[0]))
        else:
            preview.sort(key=lambda x: (-x[1], x[0]))

        for name, count, total, avg, max_cit in preview[:10]:
            print(f"{name}: {count} articles, {total} citations, {avg:.2f} avg, {max_cit} max")

        write_summary_output(article_counts, citation_counts, max_citation_counts, "summary.txt", sort_by)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
