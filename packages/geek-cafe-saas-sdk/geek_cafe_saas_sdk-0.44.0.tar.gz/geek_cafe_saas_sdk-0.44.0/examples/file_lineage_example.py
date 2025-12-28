"""
Example: Using File Lineage System

This example demonstrates how to track file transformations through
a data processing pipeline.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.s3.s3_connection import S3Connection
from boto3_assist.s3.s3_object import S3Object
from boto3_assist.s3.s3_bucket import S3Bucket

from geek_cafe_saas_sdk.modules.file_system.services import (
    FileSystemService,
    S3FileService    
)


def setup_services():
    """Initialize file system services."""
    db = DynamoDB()
    connection = S3Connection()
    
    s3_service = S3FileService(
        s3_object=S3Object(connection=connection),
        s3_bucket=S3Bucket(connection=connection),
        default_bucket="my-files-bucket"
    )
    
    file_service = FileSystemService(
        dynamodb=db,
        table_name="files-table",
        s3_service=s3_service,
        default_bucket="my-files-bucket"
    )
    
    return file_service


def example_data_pipeline():
    """
    Example: Data processing pipeline with lineage tracking.
    
    Flow:
    1. User uploads original file (measurements.xls)
    2. System converts to main file (measurements.csv)
    3. Data cleaning produces derived files (v1, v2, v3...)
    4. User selects derived file for lineage
    5. System bundles selected + main + original
    """
    
    file_service = setup_services()
    
    tenant_id = "tenant-123"
    user_id = "user-456"
    
    # Step 1: Upload original file
    print("Step 1: Uploading original file...")
    with open("measurements.xls", "rb") as f:
        xls_data = f.read()
    
    original_result = file_service.create(
        tenant_id=tenant_id,
        user_id=user_id,
        file_name="measurements.xls",
        file_data=xls_data,
        mime_type="application/vnd.ms-excel",
        file_role="original"  # Mark as original
    )
    
    if not original_result.success:
        print(f"Error: {original_result.message}")
        return
    
    original_file = original_result.data
    print(f"✓ Original file uploaded: {original_file.file_id}")
    
    # Step 2: Convert to main file (XLS → CSV)
    print("\nStep 2: Converting to CSV...")
    
    # Simulate conversion (replace with actual conversion logic)
    csv_data = convert_xls_to_csv(xls_data)
    
    main_result = file_service.create(
        tenant_id=tenant_id,
        user_id=user_id,
        parent_id=original_file.file_id,
        file_name="measurements.csv",
        file_data=csv_data,
        mime_type="text/csv",
        lineage="converted"
    )
    
    if not main_result.success:
        print(f"Error: {main_result.message}")
        return
    
    main_file = main_result.data
    print(f"✓ Main file created: {main_file.file_id}")
    print(f"  Lineage: {main_file.lineage}")
    
    # Step 3: Create derived files (data cleaning)
    print("\nStep 3: Creating cleaned versions...")
    
    derived_files = []
    for version in range(1, 4):
        # Simulate data cleaning
        cleaned_data = perform_data_cleaning(csv_data, version)
        
        derived_result = lineage_service.create(
            tenant_id=tenant_id,
            user_id=user_id,
            parent_id=main_file.file_id,
            file_name=f"measurements_clean_v{version}.csv",
            file_data=cleaned_data,
            lineage="derived"
        )
        
        if derived_result.success:
            derived_file = derived_result.data
            derived_files.append(derived_file)
            print(f"✓ Derived v{version} created: {derived_file.file_id}")
    
    # Step 4: Get lineage for a derived file
    print("\nStep 4: Getting lineage for derived v2...")
    
    selected_file_id = derived_files[1].file_id  # v2
    lineage_result = lineage_service.get_lineage(
        file_id=selected_file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    if lineage_result.success:
        lineage = lineage_result.data
        print(f"Selected: {lineage['selected'].name}")
        print(f"Main: {lineage['main'].name}")
        print(f"Original: {lineage['original'].name}")
        print(f"All derived versions: {len(lineage['all_derived'])}")
    
    # Step 5: Prepare lineage bundle
    print("\nStep 5: Preparing lineage bundle...")
    
    bundle_result = lineage_service.prepare_lineage_bundle(
        selected_file_id=selected_file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    if bundle_result.success:
        bundle = bundle_result.data
        print("Bundle contents:")
        print(f"  - Selected: {bundle['selected_file'].name}")
        print(f"  - Main: {bundle['main_file'].name}")
        print(f"  - Original: {bundle['original_file'].name}")
        print(f"\nTransformation chain:")
        for step in bundle['metadata']['transformation_chain']:
            print(f"  {step['step']}. {step['type']}: {step['file_name']}")
            if 'operation' in step:
                print(f"     Operation: {step['operation']}")
    
    # Step 6: Download complete bundle
    print("\nStep 6: Downloading complete bundle...")
    
    download_result = lineage_service.download_lineage_bundle(
        selected_file_id=selected_file_id,
        tenant_id=tenant_id,
        user_id=user_id
    )
    
    if download_result.success:
        download_bundle = download_result.data
        
        # Save each file
        if download_bundle['original']:
            save_file('output/original/', download_bundle['original'])
        
        if download_bundle['main']:
            save_file('output/main/', download_bundle['main'])
        
        if download_bundle['selected']:
            save_file('output/processed/', download_bundle['selected'])
        
        print("✓ Bundle downloaded successfully!")


def convert_xls_to_csv(xls_data: bytes) -> bytes:
    """Simulate XLS to CSV conversion."""
    # In production, use a library like openpyxl or pandas
    # For example:
    # import pandas as pd
    # df = pd.read_excel(io.BytesIO(xls_data))
    # return df.to_csv().encode('utf-8')
    
    return b"mock,csv,data\n1,2,3\n4,5,6"


def perform_data_cleaning(csv_data: bytes, version: int) -> bytes:
    """Simulate data cleaning."""
    # In production, implement actual cleaning logic
    # For example: remove nulls, normalize units, etc.
    
    return csv_data + f"\n# Cleaned v{version}".encode('utf-8')


def save_file(directory: str, file_bundle: dict):
    """Save file to disk."""
    import os
    
    os.makedirs(directory, exist_ok=True)
    
    file_path = os.path.join(directory, file_bundle['file'].name)
    with open(file_path, 'wb') as f:
        f.write(file_bundle['data'])
    
    print(f"  Saved: {file_path}")


if __name__ == "__main__":
    example_data_pipeline()
