import os
import pandas as pd
from langchain_core.documents import Document

# Define the data directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
data_dir = os.path.join(parent_dir, "data")

print(f"Data directory: {data_dir}")

# CSV files to load
csv_files = {
    "fields.csv": {
        "type": "field",
        "text_template": "Field: {name} (ID: {id}) has {topics_count} topics."
    },
    "top_subfields_us.csv": {
        "type": "subfield",
        "text_template": "Subfield: {name} (ID: {id}) has {us_works_count:,} US works."
    },
    "subfield_funders_us.csv": {
        "type": "funder",
        "text_template": "The funder for subfield {subfield_name} (ID: {subfield_id}) is {funder_name} (ID: {funder_id}) with {subfield_works_count:,} works in this subfield. The funder has {total_works_count:,} total works and is located in {country_code}."
    },
    "top_topics_us.csv": {
        "type": "topic",
        "text_template": "Topic: {name} (ID: {id}) belongs to field {field} and has {us_works_count:,} US works."
    }
}


def create_documents_from_csv(file_path, file_config):
    """
    Read a CSV file and convert each row into a LangChain Document object.

    Args:
        file_path: Path to the CSV file
        file_config: Dictionary with 'type' and 'text_template' for formatting

    Returns:
        List of Document objects
    """
    documents = []

    try:
        df = pd.read_csv(file_path)
        file_name = os.path.basename(file_path)
        doc_type = file_config["type"]
        text_template = file_config["text_template"]

        for _, row in df.iterrows():
            # Create human-readable text content
            try:
                page_content = text_template.format(**row.to_dict())
            except KeyError as e:
                # If template has missing keys, create a simpler version
                page_content = f"{doc_type.capitalize()}: {row.get('name', 'Unknown')}"
                if 'id' in row:
                    page_content += f" (ID: {row['id']})"

            # Create metadata dictionary
            metadata = {
                "source": file_name,
                "type": doc_type,
                "category":'Physical Sciences'  # Add category metadata
            }

            # Add all row data to metadata (convert to string for non-null values)
            for col, val in row.items():
                if pd.notna(val):
                    metadata[col] = str(val)

            # Create Document object
            doc = Document(page_content=page_content, metadata=metadata)
            documents.append(doc)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

    return documents


def load_all_csv_documents():
    """
    Load all CSV files and create Document objects.

    Returns:
        List of all Document objects from all CSV files
    """
    all_documents = []

    print("\nLoading CSV data...")
    print("-" * 80)

    for csv_file, config in csv_files.items():
        file_path = os.path.join(data_dir, csv_file)

        if not os.path.exists(file_path):
            print(f"⚠ Warning: {csv_file} not found. Skipping...")
            continue

        documents = create_documents_from_csv(file_path, config)
        all_documents.extend(documents)

        print(f"✓ Loaded {len(documents)} {config['type']}s from {csv_file}")

    print("-" * 80)
    print(f"\nTotal documents: {len(all_documents)}")

    return all_documents


def main():
    """Main function to load and display documents."""
    # Check if data directory exists
    if not os.path.exists(data_dir):
        raise FileNotFoundError(
            f"The directory {data_dir} does not exist. Please check the path."
        )

    # Load all documents
    documents = load_all_csv_documents()

    if not documents:
        print("\n⚠ No documents were loaded. Please check your CSV files.")
        return

    # Display sample document
    print("\n" + "=" * 80)
    print("Sample Document:")
    print("=" * 80)
    if documents:
        sample_doc = documents[0]
        print(f"\nPage Content: \"{sample_doc.page_content}\"")
        print(f"\nMetadata: {sample_doc.metadata}")

    # Display summary by type
    print("\n" + "=" * 80)
    print("Summary by Document Type:")
    print("=" * 80)
    type_counts = {}
    for doc in documents:
        doc_type = doc.metadata.get("type", "unknown")
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in sorted(type_counts.items()):
        print(f"  {doc_type.capitalize()}: {count} documents")

    print("\n✓ Document loading complete!")
    return documents


if __name__ == "__main__":
    main()

